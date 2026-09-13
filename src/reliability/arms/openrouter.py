"""Minimal non-streaming OpenRouter adapter; no retries by design."""

from __future__ import annotations

import json
import os
from pathlib import Path
from urllib import error, request

from reliability.eval.evidence import EvidenceRow

ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "deepseek/deepseek-v4-flash-0731"
ENV_VAR = "OPENROUTER_API_KEY"
PLACEHOLDER_KEY = "replace_with_your_openrouter_api_key"


def _key_from_environment() -> str:
    key = os.environ.get(ENV_VAR, "").strip()
    if key and key != PLACEHOLDER_KEY:
        return key
    env_path = Path.cwd() / ".env"
    if env_path.is_file():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            name, separator, value = line.strip().partition("=")
            if name == ENV_VAR and separator:
                key = value.strip()
                break
    if not key or key == PLACEHOLDER_KEY:
        raise RuntimeError(
            "OpenRouter API key is missing or a placeholder; set OPENROUTER_API_KEY."
        )
    return key


class OpenRouterClient:
    def __init__(self, *, model: str = MODEL) -> None:
        self._model = model

    def answer(self, question: str, evidence_row: EvidenceRow) -> str:
        prompt = (
            "Answer the question using only the evidence row below. State the metric value "
            "and unit; do not infer anything beyond it.\n\n"
            f"Question: {question}\n"
            f"Evidence row: row_id={evidence_row.row_id}; series_id={evidence_row.series_id}; "
            f"model_version={evidence_row.model_version}; origin_day={evidence_row.origin_day}; "
            f"horizon={evidence_row.horizon}; metric={evidence_row.metric}; "
            f"value={evidence_row.value:g}; unit={evidence_row.unit}"
        )
        payload = json.dumps(
            {
                "model": self._model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
            }
        ).encode()
        http_request = request.Request(
            ENDPOINT,
            data=payload,
            headers={
                "Authorization": f"Bearer {_key_from_environment()}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with request.urlopen(http_request, timeout=30) as response:
                body = response.read().decode("utf-8")
        except error.HTTPError as exc:
            raise RuntimeError(f"OpenRouter returned HTTP {exc.code}.") from exc
        except error.URLError as exc:
            raise RuntimeError(f"OpenRouter request failed: {exc.reason}") from exc
        try:
            return str(json.loads(body)["choices"][0]["message"]["content"])
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise RuntimeError("OpenRouter returned an unexpected response.") from exc
