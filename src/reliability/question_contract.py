"""Verify the aggregate-only Phase 1 held-out seal without decryption."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, NoReturn

QUESTION_CLASSES = frozenset(
    {"lookup", "cross_period", "ranking", "multi_step", "unanswerable", "trap"}
)
EXPECTED_ARTIFACT = Path("questions/heldout/questions.jsonl.age")
EXPECTED_REVISIONS = {
    "question_schema_revision": "phase1-question-v1",
    "manifest_schema_revision": "phase1-manifest-v1",
    "rubric_revision": "phase1-rubric-v1",
    "seal_process_revision": "phase1-seal-v1",
}
SHA256_PATTERN = re.compile(r"[a-f0-9]{64}\Z")
AGE_HEADER = b"age-encryption.org/v1\n"


class ContractError(ValueError):
    """Raised when the public aggregate contract cannot be verified."""


def _fail(message: str) -> NoReturn:
    raise ContractError(message)


def _as_object(value: object, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        _fail(f"{name} must be a JSON object")
    return value


def _as_string(value: object, name: str) -> str:
    if not isinstance(value, str):
        _fail(f"{name} must be a string")
    return value


def _as_integer(value: object, name: str, *, minimum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        _fail(f"{name} must be an integer at least {minimum}")
    return value


def _require_keys(document: dict[str, Any], keys: set[str], name: str) -> None:
    actual = set(document)
    missing = keys - actual
    unexpected = actual - keys
    if missing or unexpected:
        _fail(
            f"{name} keys do not match contract; missing={sorted(missing)!r}, "
            f"unexpected={sorted(unexpected)!r}"
        )


def _load_manifest(manifest_path: Path) -> dict[str, Any]:
    try:
        value: object = json.loads(manifest_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ContractError(f"held-out manifest is missing: {manifest_path}") from exc
    except json.JSONDecodeError as exc:
        raise ContractError(f"held-out manifest is not valid JSON: {exc}") from exc
    return _as_object(value, "manifest")


def _stream_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as cipher:
        while block := cipher.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def _artifact_path(root: Path, manifest: dict[str, Any]) -> Path:
    cipher_artifact = _as_object(manifest["cipher_artifact"], "cipher_artifact")
    _require_keys(cipher_artifact, {"path", "format"}, "cipher_artifact")
    declared_path = _as_string(cipher_artifact["path"], "cipher_artifact.path")
    if declared_path != EXPECTED_ARTIFACT.as_posix():
        _fail("cipher_artifact.path must be questions/heldout/questions.jsonl.age")
    if cipher_artifact["format"] != "age":
        _fail("cipher_artifact.format must be age")

    candidate = root / EXPECTED_ARTIFACT
    if candidate.is_symlink():
        _fail("cipher artifact must not be a symlink")
    try:
        candidate.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise ContractError("cipher artifact escapes repository root") from exc
    if not candidate.is_file():
        _fail(f"cipher artifact is missing: {candidate}")
    return candidate


def _validate_timestamp(value: object) -> None:
    timestamp = _as_string(value, "sealed_at")
    try:
        parsed = datetime.fromisoformat(timestamp)
    except ValueError as exc:
        raise ContractError("sealed_at must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        _fail("sealed_at must include a timezone")


def verify_manifest(manifest_path: Path, repository_root: Path) -> None:
    """Check the sealed artifact and aggregate manifest without opening plaintext."""
    manifest = _load_manifest(manifest_path)
    required_keys = set(EXPECTED_REVISIONS) | {
        "cipher_artifact",
        "cipher_sha256",
        "total_questions",
        "counts_by_primary_class",
        "declared_minimum_per_class",
        "minimum_met",
        "sealed_at",
    }
    _require_keys(manifest, required_keys, "manifest")
    for field, expected in EXPECTED_REVISIONS.items():
        if manifest[field] != expected:
            _fail(f"{field} must be {expected!r}")

    root = repository_root.resolve()
    artifact = _artifact_path(root, manifest)
    expected_digest = _as_string(manifest["cipher_sha256"], "cipher_sha256")
    if SHA256_PATTERN.fullmatch(expected_digest) is None:
        _fail("cipher_sha256 must be a lowercase SHA-256 hex digest")
    actual_digest = _stream_sha256(artifact)
    if actual_digest != expected_digest:
        _fail("cipher_sha256 does not match the ciphertext")

    with artifact.open("rb") as cipher:
        if cipher.read(len(AGE_HEADER)) != AGE_HEADER:
            _fail("cipher artifact does not have a standard age header")

    counts = _as_object(manifest["counts_by_primary_class"], "counts_by_primary_class")
    if set(counts) != QUESTION_CLASSES:
        _fail("counts_by_primary_class must contain exactly the six primary classes")
    count_values = [
        _as_integer(
            counts[question_class],
            f"counts_by_primary_class.{question_class}",
            minimum=0,
        )
        for question_class in sorted(QUESTION_CLASSES)
    ]
    total = _as_integer(manifest["total_questions"], "total_questions", minimum=1)
    if sum(count_values) != total:
        _fail("total_questions does not equal the sum of class counts")
    declared_minimum = _as_integer(
        manifest["declared_minimum_per_class"],
        "declared_minimum_per_class",
        minimum=1,
    )
    expected_minimum_met = all(count >= declared_minimum for count in count_values)
    if manifest["minimum_met"] is not expected_minimum_met:
        _fail("minimum_met does not agree with class counts and declared minimum")
    _validate_timestamp(manifest["sealed_at"])


def default_repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=default_repository_root())
    arguments = parser.parse_args(argv)
    root = arguments.root.resolve()
    manifest = root / "questions/heldout/manifest.json"
    try:
        verify_manifest(manifest, root)
    except ContractError as exc:
        print(f"Phase 1 seal verification failed: {exc}", file=sys.stderr)
        return 1
    print("Phase 1 held-out seal verified without decryption.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
