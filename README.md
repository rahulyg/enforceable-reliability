# Measuring Enforceable Reliability in an Analytical LLM System

How much numerical reliability can be structurally enforced in an LLM analytical system, what does enforcement cost in usefulness and latency, and which failure modes survive regardless?

- Arm A: free-form narration.
- Arm B: structured claims with source row references.
- Arm C: validated claims where deterministic code renders the value read from the source row.

## Results

**Populated at phase 7.**

| Metric | Arm A | Arm B | Arm C |
| --- | --- | --- | --- |
| Answer rate | | | |
| Answer accuracy | | | |
| Claim precision | | | |
| Claim recall | | | |
| Value fabrication | | | |
| Binding errors | | | |
| Directional errors | | | |
| Incomplete comparison | | | |
| False refusal | | | |
| Median latency | | | |
| Cost/query | | | |

All figures reported as k/n, never bare percentages.
Latency will be reported in milliseconds (ms), and cost in USD/query.

The evaluation will pair correctness with completeness and abstention, so an arm cannot appear reliable merely by refusing questions or omitting required claims. Error counts will distinguish fabricated values from binding, direction, and comparison failures. No measurements have been collected for this scaffold.

## What Arm C guarantees

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

Status: Phase 0 of 9 — walking skeleton. Nothing below is claimed as working yet.

Running it: pending phase 0.

See the [design brief](docs/design.md) for the proposed system and evaluation.
