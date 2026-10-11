# Learnings

## What the lifecycle proved

Context-before-Behavior worked: it named the people, product boundary, and external dependency before implementation details arrived. Behavior-before-Container then prevented premature runtime architecture. The Architecture Review Pack was enough to record the consequential choices; separate architecture documents would have repeated the same decisions. A Boundary Contract was correctly skipped because V1 had no independently meaningful interface likely to drift.

The Build Contract prevented feature expansion by preserving a narrow rule: the LLM proposes, deterministic code validates, and a human approves. Proof defined before implementation kept CI credential-independent from the first runnable vertical slice.

## What Product Assurance found

Product Assurance exposed defects that unit tests alone did not: an initial greenfield draft with zero containers, automatic promotion of unresolved proposals, and an SVG/Streamlit rendering mismatch. Deployment also exposed issues local/static reasoning missed. A stale Streamlit build demonstrated why the running release candidate must be positively identified before renderer debugging begins.

Pictograms consumed unexpectedly large effort. Markup-only tests were insufficient; the useful proof was an actual render through the real Graphviz-to-SVG-to-Streamlit pipeline, plus inspection of the exported asset. The final renderer therefore has integration evidence as well as synthetic SVG coverage.

## Changes to the SDLC

Retain Intent, Context, Product Behavior, the Architecture Review Pack, Build Contract, Plan + Proof, Build + CI, Release Candidate, Product Assurance, and Ship + Learn. Retain Boundary Contract and OpenAPI as conditional stages, not mandatory paperwork. Keep Component diagrams optional. Merge no stages: each retained stage answers a distinct question. Remove only duplicated narrative documents that do not introduce a new decision or check.

Lightweight does not mean skipping verification. It means creating only the artifacts and checks that answer a real question, then treating deployed evidence as stronger than a plausible local story.
