"""Tests for the public Phase 1 evaluation contract."""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path

import pytest

from reliability.question_contract import (
    AGE_HEADER,
    EXPECTED_ARTIFACT,
    QUESTION_CLASSES,
    ContractError,
    verify_manifest,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEV_QUESTIONS = REPOSITORY_ROOT / "questions/dev/questions.jsonl"


def _read_dev_questions() -> list[dict[str, object]]:
    return [
        json.loads(line)
        for line in DEV_QUESTIONS.read_text(encoding="utf-8").splitlines()
    ]


def _write_seal(root: Path) -> Path:
    artifact = root / EXPECTED_ARTIFACT
    artifact.parent.mkdir(parents=True)
    artifact.write_bytes(AGE_HEADER + b"-> X25519 test-recipient\n--- test-payload")
    manifest = {
        "question_schema_revision": "phase1-question-v1",
        "manifest_schema_revision": "phase1-manifest-v1",
        "rubric_revision": "phase1-rubric-v1",
        "seal_process_revision": "phase1-seal-v1",
        "cipher_artifact": {"path": EXPECTED_ARTIFACT.as_posix(), "format": "age"},
        "cipher_sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
        "total_questions": 72,
        "counts_by_primary_class": {
            question_class: 12 for question_class in QUESTION_CLASSES
        },
        "declared_minimum_per_class": 12,
        "minimum_met": True,
        "sealed_at": "2026-09-13T00:00:00Z",
    }
    manifest_path = artifact.with_name("manifest.json")
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return manifest_path


def test_public_dev_set_has_six_questions_per_primary_class() -> None:
    questions = _read_dev_questions()
    assert len(questions) == 36
    assert Counter(question["primary_class"] for question in questions) == {
        question_class: 6 for question_class in QUESTION_CLASSES
    }
    question_ids = {question["question_id"] for question in questions}
    assert len(question_ids) == 36
    assert all(str(question_id).startswith("q_dev_") for question_id in question_ids)


def test_public_dev_question_contract_has_no_gold_or_output_fields() -> None:
    expected_fields = {
        "question_id",
        "split",
        "primary_class",
        "prompt",
        "expected_behavior",
        "required_claims",
        "scoring_tags",
        "required_retrieval",
        "revisions",
    }
    for question in _read_dev_questions():
        assert set(question) == expected_fields
        assert question["split"] == "dev"
        assert question["primary_class"] in QUESTION_CLASSES
        assert question["expected_behavior"] in {"answer", "abstain"}
        assert set(question["revisions"]) == {"schema", "rubric", "retrieval_ledger"}
        assert question["revisions"] == {
            "schema": "phase1-question-v1",
            "rubric": "phase1-rubric-v1",
            "retrieval_ledger": "phase1-retrieval-v1",
        }
        assert set(question["required_retrieval"]) == {"operation", "scope"}
        assert isinstance(question["required_claims"], list)
        assert question["required_claims"]
        for claim in question["required_claims"]:
            assert isinstance(claim, dict)
            assert set(claim) == {"claim_id", "kind", "descriptor"}
        assert "gold" not in json.dumps(question).lower()
        assert "output" not in json.dumps(question).lower()


def test_primary_class_implies_frozen_operation_and_answerability() -> None:
    expected = {
        "lookup": ("lookup", "answer"),
        "cross_period": ("cross_period", "answer"),
        "ranking": ("ranking", "answer"),
        "multi_step": ("multi_step", "answer"),
        "unanswerable": ("unsupported", "abstain"),
        "trap": ("notfound", "abstain"),
    }
    for question in _read_dev_questions():
        operation, expected_behavior = expected[str(question["primary_class"])]
        retrieval = question["required_retrieval"]
        assert isinstance(retrieval, dict)
        assert retrieval["operation"] == operation
        assert question["expected_behavior"] == expected_behavior


def test_verifier_accepts_valid_aggregate_seal_without_decrypting(
    tmp_path: Path,
) -> None:
    manifest = _write_seal(tmp_path)
    verify_manifest(manifest, tmp_path)


def test_verifier_rejects_ciphertext_hash_mismatch(tmp_path: Path) -> None:
    manifest = _write_seal(tmp_path)
    artifact = tmp_path / EXPECTED_ARTIFACT
    artifact.write_bytes(artifact.read_bytes() + b"changed")
    with pytest.raises(ContractError, match="does not match"):
        verify_manifest(manifest, tmp_path)


def test_verifier_rejects_inconsistent_count_claim(tmp_path: Path) -> None:
    manifest_path = _write_seal(tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["counts_by_primary_class"]["trap"] = 11
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ContractError, match="total_questions"):
        verify_manifest(manifest_path, tmp_path)


def test_repository_has_no_plaintext_heldout_material() -> None:
    heldout = REPOSITORY_ROOT / "questions/heldout"
    if not heldout.exists():
        return
    allowed = {"questions.jsonl.age", "manifest.json"}
    assert {path.name for path in heldout.iterdir()} <= allowed


def test_no_plaintext_heldout_path_exists_in_artifacts_fixtures_or_history() -> None:
    for directory in (
        REPOSITORY_ROOT / "artifacts",
        REPOSITORY_ROOT / "tests/fixtures",
    ):
        if directory.exists():
            assert not any(
                "heldout" in path.name.lower() for path in directory.rglob("*")
            )
    history = subprocess.run(
        ["git", "log", "--all", "--format=", "--name-only", "--", "questions/heldout"],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    historical_paths = {line for line in history.stdout.splitlines() if line}
    assert historical_paths <= {
        "questions/heldout/questions.jsonl.age",
        "questions/heldout/manifest.json",
    }
