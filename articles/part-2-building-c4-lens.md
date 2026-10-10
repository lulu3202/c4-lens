# Building C4 Lens with My Lightweight AI-Native SDLC

*Part 2 of 2 — Draft 1*

C4 Lens began with a narrow question: could a builder turn a problem statement into two useful C4 diagrams without allowing an LLM to blur facts and guesses? The V1 answer is a Streamlit app that uses Vercel AI Gateway with `openai/gpt-5.6-terra` for one structured proposal, validates one Pydantic model in Python, asks for review, and only then produces clean System Context and Container diagrams.

The early context was sparse: reviewer, C4 Lens, and an LLM provider. That restraint mattered. After describing the product journey — describe, review draft, resolve assumptions, approve, export — the runtime shape became straightforward: Streamlit, a single provider adapter, Pydantic validation, and Graphviz rendering. Database, FastAPI, React, LangGraph, Structurizr runtime, and microservices were consciously rejected.

The key guardrail is visible in the product: **Draft — proposed assumptions highlighted**. Stated facts, derived structure, and proposed assumptions are separate. A first implementation mistake was discovered in review: a generic “resolve proposals and approve” action could turn all proposals into derived structure. That was not a meaningful approval gate. The corrected screen requires a human Accept or Reject decision for every proposed entity, relationship, and assumption; the compact JSON editor remains available for corrections. Validation refuses approval while any proposal is undecided. Context and Container derive from the same canonical model, so the two views cannot quietly diverge.

The proof plan covered invalid relationships, duplicate IDs, hierarchy errors, the approval boundary, exports, and deterministic end-to-end flows. CI runs lint, tests, and a core-import smoke check. The Vercel AI Gateway adapter uses its OpenAI-compatible structured JSON-schema endpoint and the existing Pydantic model. Tests mock that narrow boundary, so CI has no credential dependency. Eight deterministic tests pass locally after the migration. The three planned greenfield scenarios and deployment smoke test remain evidence gaps until a gateway key is available to the release candidate.

Real artifacts: [Context source](../docs/article-assets/02-context.svg), [product flow](../docs/03-product.md), [container source](../docs/article-assets/04-container.svg). Screenshots of the live gateway candidate and release candidate will be added only after those real states exist.

REPO: https://github.com/lulu3202/c4-lens

DEMO: HUMAN ACTION REQUIRED — deploy the configured branch in Streamlit Community Cloud, add `AI_GATEWAY_API_KEY`, and record the resulting URL.
