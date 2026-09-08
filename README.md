# Measuring Enforceable Reliability in an Analytical LLM System

How much numerical reliability can be structurally enforced in an LLM analytical system, what does enforcement cost in usefulness and latency, and which failure modes survive regardless?

This repository contains a proposed design and an evaluation plan. Nothing described below has been implemented or measured yet.

- Arm A: free-form narration.
- Arm B: structured claims with source references.
- Arm C: validated claims with deterministic rendering, where code renders the value read from the source row.

## Results

**No evaluation has been run. This table is populated at phase 7.**

| Metric | Arm A | Arm B | Arm C |
| --- | --- | --- | --- |
| Answer rate | | | |
| Answer accuracy | | | |
| Claim precision | | | |
| Claim recall | | | |
| Correct abstention rate | | | |
| Value fabrication | | | |
| Binding errors | | | |
| Directional errors | | | |
| Incomplete comparison | | | |
| False refusal | | | |
| Median latency | | | |
| Mean input tokens/query | | | |
| Mean output tokens/query | | | |
| Cost/query | | | |

### How these will be reported

- All rate figures will be reported as `k/n`, never bare percentages.
- Latency in milliseconds (ms), input and output tokens in tokens/query, cost in USD/query.
- **Correct abstention rate** will be correct abstentions divided by questions requiring abstention, including applicable trap questions. Per-class labelling rules are written at phase 1, before any model outputs are seen.
- **Claim precision** will be scored against independently verified gold answers, not against validator acceptance. A validator that grades its own output proves nothing.
- Retries and re-asks will count toward the originating query's totals for latency, tokens, and cost.

The evaluation will pair correctness with completeness and abstention, so an arm cannot appear reliable merely by refusing questions or omitting required claims. Error counts will distinguish fabricated values from binding, direction, and comparison failures.

## What Arm C is intended to guarantee

The proposed design guarantee is that every numeric value displayed is read by deterministic code directly from a source row whose entity, metric, period, and model version were validated against the claim. This is a design commitment to be implemented and tested, not a claim of completed implementation.

It does not guarantee:

- That the right row was selected.
- That the comparison set was complete.
- That the direction of change is described correctly.
- That the interpretation is sound.
- That a material fact was not omitted.

These residual failures remain part of the evaluation. Source traceability alone does not establish a useful or complete answer.

## Architecture

A public retail time-series subset will feed seasonal-naive and LightGBM forecasts, rolling-origin backtests, and a deterministic metrics table with addressable source rows. The three answer arms will share evidence and an evaluation interface. Model review and candidate selection provide analytical use cases; the experiment measures answer architectures rather than declaring a universally superior forecasting model. The forecasting layer is deliberately unremarkable and exists to produce real numbers with ground truth.

Status: Phase 0 of 9 — scaffold created; walking skeleton not implemented. No evaluation results yet.

## Roadmap

Nine phases, tracked on the [project board](https://github.com/users/rahulyg/projects/2). No phase is complete.

| Phase | Complete when |
| --- | --- |
| 0. Walking skeleton | One question flows end to end and the assertion passes. |
| 1. Question set and scoring rubric | Manifest committed and verifiable without opening the held-out questions. |
| 2. Data | Clean typed dataset, scoping decision defended in writing. |
| 3. Forecast and backtest | Leakage test passes — no feature at origin *t* uses data after *t*. |
| 4. Metrics table | Unit tests pass, row IDs stable across re-runs, and Python answers every dev question correctly with no LLM involved. |
| 5. Validator | Passes a synthetic adversarial suite, including a value present in the retrieved rows bound to the wrong entity. |
| 6. Answer layer | All three arms answer the same question through the same interface. |
| 7. Eval run | Comparison table populated with k/n counts. |
| 8. Package | A stranger can run it and state what it proves. |

## Running it

Prerequisites: [uv](https://docs.astral.sh/uv/). uv will fetch Python 3.12 if it is not already present.

```
make install   # uv sync --locked
make lint      # ruff check, ruff format --check, mypy --strict on src/
make test      # pytest
make all       # lint, then test
```

The package currently contains no implementation and no tests. `make test` reports `no tests collected` and succeeds; it fails on real test failures and on collection errors.

See the [design brief](docs/design.md) for the proposed system and evaluation.
