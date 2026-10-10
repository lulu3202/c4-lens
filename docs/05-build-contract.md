# Build Contract

- The app MUST use one Pydantic C4 model as the source for both views.
- A draft MUST label proposed assumptions; it MUST NOT export canonical diagrams before an explicit decision on every proposal and approval.
- The LLM MAY propose data but MUST NOT validate, render, or approve it.
- IDs, endpoints, hierarchy, responsibilities, and provenance MUST be validated deterministically.
- Context MUST exclude containers; Container MUST only include containers owned by the described system.
- State MUST be session-only. No secrets, accounts, persistence, component diagrams, or HTTP API are in V1.
- Exports MUST be SVG, PNG, and JSON from the approved model.
- Done means lint, tests, startup smoke test, and a reviewable draft-to-export flow pass.
