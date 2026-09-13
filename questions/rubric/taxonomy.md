# Failure taxonomy — `phase1-rubric-v1`

Use every applicable label, then designate exactly one root cause: the earliest
causal failure that made the answer wrong or incomplete. If evidence cannot
support a causal ordering, designate `unsupported_inference` as root cause and
record the ambiguity for adjudication. Label future outputs blind to arm where
practical; Rahul independently reviews and adjudicates disagreements.

| Label | Apply when | Typical root cause rule |
| --- | --- | --- |
| `retrieval` | Wrong tool, parameters, or evidence scope means needed data was not fetched. | Root if the retrieval miss directly causes the failure. |
| `incomplete_comparison` | A ranking/superlative is made without the complete required universe or ties. | Root unless an earlier retrieval error caused the coverage gap. |
| `fabrication` | A value appears in no retrieved evidence. | Root if the value was invented rather than misbound. |
| `binding` | A real value is attached to the wrong entity, metric, model, period, horizon, unit, or row. | Root when the tuple mismatch is the first error. |
| `directional` | Correct endpoints are described with the inverse direction. | Root after endpoint tuple matches are established. |
| `unsupported_inference` | An explanation, cause, or implication exceeds the evidence. | Root for unsupported interpretation absent an earlier factual error. |
| `false_refusal` | An answerable question is declined. | Root when no earlier system failure explains the decline. |
| `missing_abstention` | An unanswerable or trap question is answered rather than appropriately declined. | Root unless a prior false retrieval/binding claim is the causal error. |
| `material_omission` | A required claim, tie, endpoint, caveat, or component is absent such that the response misleads. | Root only when no earlier error better explains the omission. |

The taxonomy is multi-label, not mutually exclusive. It has no catch-all
label: record an adjudication note when none fit rather than relabelling a
failure to improve counts.
