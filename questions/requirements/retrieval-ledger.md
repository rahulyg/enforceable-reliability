# Retrieval ledger requirements — `phase1-retrieval-v1`

Every evidence record used for scoring must retain these fields: dataset and
dataset version; entity, series, or segment; metric; model; origin or period;
horizon; value and unit; and a stable row ID. Values are not recorded in the
Phase 1 question files.

The question contract declares one required operation:

| Operation | Required ledger evidence |
| --- | --- |
| `lookup` | Exact tuple for the requested entity/series/segment, metric, model, origin/period, horizon, value/unit, and stable row ID. |
| `cross_period` | Exact, comparable tuples for both named endpoints plus ordered-period evidence. |
| `ranking` | The complete declared comparison universe, coverage status, tie handling, and all candidate tuples. |
| `multi_step` | All component tuples, the declared composition, and the inputs needed to reproduce it. |
| `notfound` | Explicit evidence that the requested entity/series/segment or row is absent from the scoped dataset/version. |
| `unsupported` | Explicit evidence that available rows cannot support the requested operation or scope. |

The stable row ID must identify the source tuple in its dataset/version context.
Future retrieval must fail closed on an unresolved, stale, or incomplete row.
