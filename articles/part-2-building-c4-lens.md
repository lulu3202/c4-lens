# Building C4 Lens with My Lightweight AI-Native SDLC

*Part 2 of 2 — Draft 1*

C4 Lens began with a narrow question: could a builder turn a problem statement into two useful C4 diagrams without allowing an LLM to blur facts and guesses? The V1 answer is a Streamlit app that proposes one Pydantic model, validates it in Python, asks for review, and only then produces clean System Context and Container diagrams.

The early context was sparse: reviewer, C4 Lens, and an LLM provider. That restraint mattered. After describing the product journey — describe, review draft, resolve assumptions, approve, export — the runtime shape became straightforward: Streamlit, a single provider adapter, Pydantic validation, and Graphviz rendering. Database, FastAPI, React, LangGraph, Structurizr runtime, and microservices were consciously rejected.

The key guardrail is visible in the product: **Draft — proposed assumptions highlighted**. Stated facts, derived structure, and proposed assumptions are separate. Approval transforms reviewed proposals into derived structure and clears the assumption list; validation refuses approval otherwise. Context and Container derive from the same canonical model, so the two views cannot quietly diverge.

The proof plan covered invalid relationships, duplicate IDs, hierarchy errors, the approval boundary, exports, and deterministic end-to-end flows. CI runs lint, tests, and an import smoke test. The live-provider test remains a human action until an API key is configured, and Community Cloud deployment likewise needs the owner to add the secret.

Real artifacts: [Context source](../docs/article-assets/02-context.svg), [product flow](../docs/03-product.md), [container source](../docs/article-assets/04-container.svg). Add repository and demo links after review: `REPO LINK`, `DEMO LINK`.
