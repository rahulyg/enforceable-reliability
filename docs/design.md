# Measuring Enforceable Reliability in an Analytical LLM System

*Section numbering starts at 2 because section 1 was removed.*

*A forecasting substrate, three progressively constrained answer architectures, and an evaluation harness that measures what each constraint actually buys.*

> **Status: proposed design.** A Phase 0 synthetic walking skeleton exists: one fixture-backed seasonal-naive forecast flows through MAE, addressable evidence, Arm A delegation, and a smoke runner. It is plumbing verification only, not an evaluation, reliability result, or forecast-quality result. Every future architecture, metric, and guarantee described here remains a commitment to be built and tested. Numeric values below are illustrative worked examples or citations to external published work — never results from this project.

The implementation workflow and initial notebook mapping are recorded separately in [ADR 0001: Notebook strategy](decisions/0001-notebook-strategy.md).

---

## 2. What this project investigates

This investigation compares three answer architectures in an analytical LLM system and asks:

> **How much numerical reliability can be structurally enforced in an LLM analytical system, what does enforcement cost in usefulness and latency, and which failure modes survive regardless?**

This is deliberately framed as an investigation, not a demonstration. A project that asserts "my agent doesn't hallucinate" is weak. A project that measures three architectures against a held-out set and reports exactly which error classes each one eliminates — and which it doesn't — is defensible on its evidence.

**What it produces:** a comparison table, an error taxonomy with counts, and a narrowly stated guarantee.

**What it does not produce:** a competition-grade forecast. The forecasting layer is deliberately competent and unremarkable; it exists to generate a stream of real numbers with genuine ground truth.

---

## 3. Why the design takes this shape

Three constraints drive everything downstream. Read this before the architecture.

### 3.1 Evaluation needs objective ground truth

Most LLM projects have mushy evaluation — "was that a good answer?" collapses into a judge model scoring another model.

Forecasting has ground truth that arrives later: the world reports whether the forecast was right. Once forecast metrics are computed deterministically into a table, the agent's answers *also* have ground truth, because the correct answer to "which segment degraded most?" is a fact sitting in a row. Objectivity cascades.

### 3.2 Removing arithmetic tools does not prevent fabricated numbers

This correction is the reason the project was redesigned.

An earlier version of this design claimed that denying the model computation tools made it structurally unable to state a wrong number. **That is false.** A language model emits tokens; digits are tokens. Read-only database access protects the *database*. It does not constrain the *answer*. The model can still:

- emit a value that appears in no retrieved row,
- attach a real value to the wrong entity, metric, period, or model version,
- describe a degradation as an improvement,
- claim a superlative without having retrieved the full comparison set.

If a guarantee is wanted, it has to come from **validating structured claims and rendering approved values through deterministic code** — and even then the guarantee is narrow (see §6, Arm C, and §11).

### 3.3 A trust claim is only worth what its verification is worth

Which forces the verification unit to be correct. Checking that `1.14` appears somewhere in the retrieved rows is not verification — see §7.

---

## 4. System design

```
LAYER 1 — DATA
  Public retail time series (M5 subset). Typed, versioned, reproducible.
        │
LAYER 2 — FORECAST
  Seasonal-naive reference + LightGBM (lag/calendar features)
  Rolling-origin backtest → predictions table
  Tagged: model_version, origin_date, horizon, series_id
        │
LAYER 3 — METRICS (deterministic, unit-tested)
  Joins predictions ⨝ actuals. Computes MASE, RelMAE, bias,
  error-by-horizon, error-by-segment.
  → metrics table.  SINGLE SOURCE OF NUMERIC TRUTH. Row-addressable.
        │ read-only, row_id addressable
LAYER 4 — ANSWER LAYER  (three interchangeable arms — §6)
  A: free-form narration
  B: structured claims with source references
  C: validated claims + deterministic rendering
        │
LAYER 5 — EVALUATION
  Dev set (prompt iteration) │ Held-out set (touched once per arm)
  Tuple-level claim validation · taxonomy · paired coverage/accuracy
  · abstention rates · cost · latency

```

Every row in the metrics table carries a stable `row_id`. That addressability is what makes Arm C possible — a claim can point at its source.

---

## 5. Forecast layer and its metrics

### 5.1 MASE, defined correctly

MASE scales forecast errors by the **in-sample (training) MAE of a naive method** — not by the baseline's performance on the test period. Defined in [Hyndman and Koehler, *Another look at measures of forecast accuracy*](https://robjhyndman.com/papers/mase.pdf); see also [Forecasting: Principles and Practice](https://otexts.robjhyndman.com/fpp2/accuracy.html).

For a seasonal series with period *m*, the scaled error is

```
              e_j
q_j =  ───────────────────────────────
        (1/(T−m)) · Σ |y_t − y_{t−m}|
              over the TRAINING set

```

and `MASE = mean(|q_j|)`.

**Worked example (illustrative; not project results).** Suppose across the training data the average one-step seasonal-naive absolute error is **20 units**. Call this the scale factor *S*; it is computed once and is a property of the series.

Your model's absolute errors on the test window are 10, 12, 8, 10 → MAE = **10**.

```
MASE = 10 / 20 = 0.5

```

Read as: *average error half the size of the average training-period seasonal-naive error.* Below 1 is better than that reference; above 1 is worse.

**The critical property:** *S* does not move when the test window changes or when a comparator performs differently. That fixedness is what makes MASE comparable across series and across studies.

**This experiment's choice:** scale factors are fixed from the **initial training window** and reused across all rolling origins, so a series' scale does not drift as origins advance. That is a convention adopted here for comparability across origins, not a property of MASE itself, and it is documented as such.

**The tell that distinguishes it from a ratio-of-two-models.** In the quarterly beer example published in [Forecasting: Principles and Practice](https://otexts.robjhyndman.com/fpp2/accuracy.html) — an external reference, not a result from this project — the seasonal naive method scores MASE = **0.94**, not 1.00. If MASE were model-MAE ÷ baseline-MAE on the test set, the baseline would score exactly 1.00 by construction. It does not.

### 5.2 Relative MAE — a separate metric, separately labelled

If the question is "how much better than seasonal naive *on this test window*," that is a different quantity:

```
RelMAE = MAE(model, test) / MAE(seasonal_naive, test)

```

RelMAE = 0.71 supports the statement *"29% lower test-period MAE than seasonal naive."* **MASE = 0.71 does not support that statement.** Report both; never conflate the labels.

### 5.3 Undefined-denominator handling

If a training series is constant across the seasonal lag, *S* = 0 and MASE is undefined. M5 contains many intermittent and near-constant series, so this is not hypothetical.

Handling: exclude affected cases **only from the metric aggregations they actually affect** — an undefined MASE scale removes a series from MASE aggregation, not from MAE or bias — and **report the excluded counts explicitly** alongside every affected figure.

RelMAE is **not** assumed to be a valid fallback: its denominator, the seasonal-naive test-period MAE, can itself be zero or undefined. Where either ratio is undefined, **MAE is retained** as the reportable error measure for those cases. Silently dropping series, or quietly substituting one ratio for another, would misstate the aggregates.

### 5.4 What lands in the metrics table

MASE, RelMAE, MAE, bias (signed, separate from magnitude), error by horizon, error by segment, all keyed by model version and origin date, each row addressable.

---

## 6. The three arms

Same forecast data, same metrics table, same question set. Only the answer architecture changes.

### Arm A — Free-form narration

Retrieved rows go into context; the model writes prose freely.

*Prevents structurally:* nothing. *Baseline for the comparison.*

### Arm B — Structured claims with source references

The model must emit claims as structured objects rather than prose:

```json
{"entity": "HOUSEHOLD", "metric": "mase", "period": "2015-03",
 "model_version": "v2", "value": 1.14, "source_row_id": "m_88214"}

```

Values are still produced by the model. Structure makes every claim *checkable*.

*Prevents structurally:* nothing — but converts silent errors into detectable ones.

### Arm C — Validated claims with deterministic rendering

The model emits the same structured claims, then:

1. A validator fetches each `source_row_id` and checks that the row's entity, metric, period, and model version match the claim.
2. Claims failing validation are dropped or surfaced as an error.
3. **The renderer writes the value read from the source row — not the value the model emitted.**

*Prevents structurally:* value fabrication, and binding of a value to the wrong entity/metric/period/version. The model chooses *what to say about*; code decides *what number appears*.

*Does not prevent:* selecting the wrong row, retrieving an incomplete comparison set, wrong directional interpretation, material omission. Those are measured in §8, not eliminated.

### The experiment

Run all three arms on the same held-out question set. Report which error classes each eliminates, which persist, and what each restriction costs in answer usefulness, latency, and tokens. **That table is the deliverable.**

---

## 7. Claim validation — the verification unit

The naive check — *does this number appear in the retrieved rows?* — passes on wrong answers.

**Counterexample (illustrative; not project results).** Retrieved:

| Category | MASE |
| --- | --- |
| HOUSEHOLD | 1.14 |
| FOODS | 0.98 |

Agent says: *"FOODS had the worst MASE at 1.14."*

`1.14` is present. Scalar check passes. **The answer is wrong.**

So validation operates on the **tuple**, not the scalar:

```
(entity, metric, period, model_version, value)  →  must match one source row

```

And superlatives require a second check: **was the full comparison set retrieved?** "Worst across categories" is unverifiable — and unanswerable — if only two of nine categories were fetched. Ranking claims are validated against retrieved coverage, not just against the top row.

Comparative claims ("up from", "improved") require both endpoints validated *and* the stated direction checked against the arithmetic sign.

---

## 8. Evaluation design

### 8.1 The gaming problem

A system that refuses everything achieves perfect fidelity. A system that answers thinly achieves perfect traceability. Any single headline metric is gameable, so metrics are reported **in pairs, with raw counts**.

| Dimension | Guards against |
| --- | --- |
| **Answer rate** (n attempted / n answerable) | Over-refusal |
| **Answer accuracy** (of attempted) | Reckless answering |
| **Claim precision** (claims matching the gold key / claims made) | Fabrication, binding errors |
| **Claim recall** (required claims made / required) | Thin, incomplete answers |
| **False refusal rate** (on answerable) | Over-refusal |
| **Correct abstention rate** (correct abstentions / questions requiring abstention, including applicable trap questions) | Over-confidence |
| **Median latency, mean input and output tokens, cost per query** (retries and re-asks charged to the originating query) | Reliability bought at absurd expense |

Every rate reported as `k / n`, not a bare percentage. "99.2%" is meaningless without *n* and without the definition of success. Latency is reported in ms, tokens as mean input and output tokens per query, and cost in USD per query.

**Claim precision is scored against an independently verified gold key, never against validator verdicts.** A validator that grades its own acceptances measures nothing. Validator false accepts and false rejects are measured separately, against that same key.

### 8.2 Question set and holdout

Golden questions split into **dev** (used freely for prompt iteration) and **held-out** (run once per arm, at the end). Held-out results are the headline. Dev results may be shown to demonstrate iteration, clearly labelled.

Question classes: simple lookup · comparison across periods · superlative/ranking · multi-step · **unanswerable** (data cannot support it; correct behaviour is abstention) · **trap** (presupposes something false — e.g. asks about a segment that doesn't exist).

### 8.3 Error taxonomy

Every failure classified, counts reported per arm:

1. **Retrieval error** — wrong tool or parameters; correct data never fetched
2. **Incomplete comparison set** — superlative claimed without full ranking retrieved
3. **Value fabrication** — value present in no retrieved row
4. **Binding error** — real value, wrong entity / metric / period / version
5. **Directional error** — values correct, narration inverts the direction
6. **Unsupported inference** — causal or explanatory claim the data cannot support
7. **False refusal** — declined an answerable question
8. **Missing abstention** — answered an unanswerable or trap question
9. **Material omission** — true but misleadingly incomplete

The taxonomy is the interesting output. Aggregate scores say *whether*; the taxonomy says *how*.

---

## 9. What we're building

**Data.** M5 retail, scoped to a defensible subset. The scoping decision is documented and defended, not apologised for.

**Forecast.** Seasonal-naive reference plus one LightGBM model with lag and calendar features. Rolling-origin backtest across several origins. Predictions written with model version, origin, horizon.

**Metrics.** Deterministic, pure, unit-tested functions writing row-addressable output. Explicit undefined-MASE handling.

**Answer layer.** A small set of read-only retrieval tools plus three interchangeable answer architectures sharing one interface, so arms are swappable in the eval runner.

**Validator.** Tuple matching, comparison-set coverage checking, directional verification.

**Eval harness.** Dev/held-out split, runner across all three arms, taxonomy classification, paired metrics with counts, cost and latency capture.

**Engineering.** Git with real commit hygiene. Tests on metric functions and validator. Typed config. README leading with the comparison table.

---

## 10. Definition of done

A public repository whose README opens with this, populated:

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

*Held-out set, n = \_\_. Forecast layer: MASE \_\_ (excl. \_\_ undefined series), RelMAE vs seasonal naive \_\_.*

**Planned investigation:**

> Analytical LLM systems fail by stating wrong numbers confidently, and people act on them. This project asks how much of that is structurally preventable rather than merely prompt-tunable. The plan is to build the same analytical agent three ways — free narration, structured claims with source references, and validated claims where deterministic code renders the values — and to measure all three on a held-out question set. Arm C is designed so that value fabrication and binding errors cannot occur by construction; whether that holds in practice, and what the constraint costs in latency and answer usefulness, is precisely what the evaluation is meant to establish. Directional and interpretation errors are not addressed by the design and are expected to survive it. **Implementation and evaluation are both pending. No measurements exist yet.**

---

## 11. The guarantee, stated narrowly

**Arm C is designed to guarantee:** every numeric value displayed is read by deterministic code directly from a source row whose entity, metric, period, and model version were validated against the claim.

**Arm C is not designed to guarantee:** that the right row was selected, that the comparison set was complete, that the direction of change is described correctly, that the interpretation is sound, or that a material fact was not omitted.

Those residual failure modes are **measured and reported**, not eliminated. Stating the boundary precisely is the point — a guarantee that overreaches is worse than a narrow one that holds.

---

## 12. Out of scope

Named so scope creep is a decision, not an accident.

- Beating M5 benchmarks
- Fine-tuning
- Multi-agent orchestration
- Frontend
- Streaming / real-time
- RAG and vector search — deliberately excluded; unstructured retrieval weakens the ground-truth property the whole design depends on

*Restore first if room appears:* prediction-interval calibration, then containerisation, then drift detection.
