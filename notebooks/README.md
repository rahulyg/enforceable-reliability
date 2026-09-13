# Notebooks

Notebooks are exploratory and demonstrative artifacts. Reusable, tested production code belongs in `src/` and `tests/`. `00_walking_skeleton.ipynb` runs on the selected global Python 3.14 kernel and adds local `src/` explicitly; package tests and CI use uv's isolated environment. Its live smoke switch is false by default.

| Planned notebook | Purpose | Phase |
| --- | --- | --- |
| `00_walking_skeleton.ipynb` | Complete synthetic end-to-end prototype. | 0 |
| `01_data_exploration.ipynb` | M5 subset exploration and scoping evidence. | 2 |
| `02_forecast_metrics.ipynb` | Backtest inspection and deterministic metric reconciliation. | 3–4 |
| `03_evaluation_analysis.ipynb` | Analysis and presentation of frozen evaluation results. | 7 |

This is an initial four-notebook plan, not a fixed limit. See the [notebook strategy decision](../docs/decisions/0001-notebook-strategy.md) for the rationale and boundaries.
