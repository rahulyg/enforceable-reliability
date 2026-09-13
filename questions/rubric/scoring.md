# Scoring rubric — `phase1-rubric-v1`

This rubric is frozen before any arm output or numeric gold key exists. Numeric
gold values and independently verified row bindings are populated in Phase 4,
not here. No model judge is permitted.

## Per-question deterministic scoring

Score an attempted response against the question's symbolic required-claim
descriptors and the future independently verified gold key.

1. **Attempt and answerability.** `answer` questions are answerable; `abstain`
   questions require a refusal that identifies unsupported or absent evidence.
   An attempted answer on an abstention question is a missing abstention. An
   abstention on an answerable question is a false refusal.
2. **Tuple match.** Every asserted numeric claim must match one source tuple:
   entity/series/segment, metric, model, origin/period, horizon, value/unit,
   and stable row ID. A value alone never passes.
3. **Coverage, ties, and direction.** Ranking claims require the complete
   declared universe and report all applicable ties. Cross-period claims
   require both endpoints and a direction consistent with their ordered values.
   Multi-step claims require every declared component and the frozen composition
   operation. A missing required component is not repaired by a correct subset.
4. **Required-claim precision and recall.** Precision is matching asserted
   required claims divided by asserted required claims. Recall is matching
   required claims divided by required claims. Report both as `k/n`.
5. **Question accuracy and material omission.** An answer is accurate only if
   its required tuple(s), operation, scope, and direction are correct. A true
   answer with a missing required fact is additionally labelled material
   omission and cannot receive complete coverage.

Report answer rate, accuracy, claim precision, claim recall, false refusal,
and correct abstention as raw `k/n` counts. Do not publish bare percentages.
Retries and re-asks remain charged to their originating query in later phases.

## Primary-class precedence

Assign one `primary_class` using this order when a prompt fits more than one
shape: `trap` > `unanswerable` > `multi_step` > `ranking` > `cross_period` >
`lookup`. Tags may retain secondary scoring needs, but reporting and minimum
counts use only the primary class.

`trap` is a false premise: the prompt asserts an entity, metric, event, or
relationship contradicted by the scoped evidence. `unanswerable` is instead
absent or insufficient evidence for a premise that has not been shown false.
Both require abstention, but their explanation and label differ.
