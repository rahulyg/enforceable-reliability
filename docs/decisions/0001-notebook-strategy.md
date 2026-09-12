# ADR 0001: Notebook strategy

**Status:** Accepted

## Context

This project needs a small number of reproducible places to explore data, inspect intermediate results, and demonstrate end-to-end milestones. It also needs reusable behaviour to be testable and maintainable outside an interactive environment.

## Decision

Use notebooks for exploration and demonstration, while keeping production behaviour in the Python package and test suite. Reusable, tested code belongs in `src/` and `tests/`; notebooks should call that code rather than become the only implementation of it.

The initial notebook plan is:

| Notebook | Purpose | Phase |
| --- | --- | --- |
| `notebooks/00_walking_skeleton.ipynb` | Demonstrate one complete synthetic end-to-end path. | 0 |
| `notebooks/01_data_exploration.ipynb` | Explore the M5 subset and document the scoping evidence. | 2 |
| `notebooks/02_forecast_metrics.ipynb` | Inspect rolling-origin backtests and reconcile deterministic metrics. | 3–4 |
| `notebooks/03_evaluation_analysis.ipynb` | Analyze and present the frozen evaluation results. | 7 |

Four notebooks are the initial organization, not a cap. Add, split, merge, or retire notebooks only when doing so improves reproducibility or clarity; update this decision and the notebook index when the strategy materially changes.

Phases 1, 5, 6, and 8 primarily produce repository artifacts rather than notebooks: question manifests and scoring documentation; validator modules and adversarial tests; answer-layer modules and integration tests; and packaging, documentation, and reproducibility artifacts, respectively.

No notebook files are created by this decision. Each notebook is added with the phase work it supports.

## Consequences

- Exploratory work and milestone demonstrations remain visible and reproducible.
- Business logic can be exercised by automated tests without requiring notebook execution.
- The notebook index makes the intended purpose of each interactive artifact explicit.
- Changes to the notebook count require a documented rationale rather than silently expanding the workflow.
