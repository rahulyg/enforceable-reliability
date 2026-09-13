# Phase 1 question contract and held-out sealing

This directory freezes the evaluation contract before any answer-arm outputs
are collected. It contains no model calls, numeric gold answers, arm outputs,
or results.

`dev/questions.jsonl` is public prompt-iteration material: six questions for
each primary class. `schema/`, `rubric/`, and `requirements/` are the versioned
contract used for both splits.

## Held-out access boundary

Rahul is both the held-out key custodian and independent reviewer. The private
identity must never be stored in this repository, CI, a PR, a shell history, or
an environment file. Do not create a substitute or demonstration recipient.
The public repository may contain held-out material only at:

```
questions/heldout/questions.jsonl.age
```

It has no plaintext prompt, ID, answer, source-row ID, model output, fixture,
or backup companion file. The `.gitignore` rule prevents staging plaintext from
that directory by default; inspect the staged diff before committing.

## Offline sealing gate

This gate is intentionally not satisfiable until Rahul provides his real public
`age1...` recipient through an approved channel. A public recipient is safe to
use, but it must be Rahul's supplied recipient; this project does not generate
or publish a key on his behalf.

On a custodian-controlled machine, create and independently review a plaintext
JSONL file outside this repository. Validate that it has exactly twelve
held-out questions in each class and conforms to
`schema/question.schema.json`. Then, with a recipient supplied by Rahul:

```
AGE_RECIPIENT='age1...supplied-by-rahul...'
age -r "$AGE_RECIPIENT" -o questions/heldout/questions.jsonl.age /absolute/path/outside/repo/questions.jsonl
shasum -a 256 questions/heldout/questions.jsonl.age
```

Do not put `AGE_RECIPIENT`, an identity path, or plaintext in a command file,
PR description, issue, CI variable, or repository documentation. The encrypted
artifact is intentionally not ASCII-armored: standard `age` ciphertext is the
required format. `age` must be installed on the custodian machine; install it
through that machine's approved package management only if it is needed.

At the same time, write `questions/heldout/manifest.json` from the following
shape, filling only aggregate values and the exact digest. Do not add prompt
content or any identifiers.

```json
{
  "question_schema_revision": "phase1-question-v1",
  "manifest_schema_revision": "phase1-manifest-v1",
  "rubric_revision": "phase1-rubric-v1",
  "seal_process_revision": "phase1-seal-v1",
  "cipher_artifact": {"path": "questions/heldout/questions.jsonl.age", "format": "age"},
  "cipher_sha256": "<lowercase sha256 of ciphertext>",
  "total_questions": 72,
  "counts_by_primary_class": {
    "lookup": 12,
    "cross_period": 12,
    "ranking": 12,
    "multi_step": 12,
    "unanswerable": 12,
    "trap": 12
  },
  "declared_minimum_per_class": 12,
  "minimum_met": true,
  "sealed_at": "<UTC ISO-8601 timestamp>"
}
```

Commit only the ciphertext and manifest, run `uv run python -m
reliability.question_contract`, and arrange independent review by Rahul before
declaring Phase 1 complete. The verifier does not decrypt and cannot validate
the plaintext's semantic quality, its count, its secrecy before sealing, or
the absence of prior contamination; it verifies only the artifact hash and
manifest's internal aggregate assertions.
