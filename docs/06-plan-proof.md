# Plan + Proof

| Slice | Outcome | Proof |
|---|---|---|
| 1 | shell and deterministic sample | app import + fixture |
| 2 | structured model / one provider adapter | schema and mocked-key-free tests |
| 3 | validation and provenance review | invalid endpoint, duplicate ID, approval tests |
| 4 | Context and Container render | SVG node and hierarchy tests |
| 5 | approval and exports | draft-to-approved end-to-end export test |
| 6 | release readiness | ruff, pytest, Streamlit smoke test |

Fixtures cover a valid simple system, external system, multiple-view model, bad relationship, duplicate ID, missing reference, assumptions, hierarchy, approval state, export, and two held-out statements in deterministic end-to-end coverage.
