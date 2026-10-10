# Building a Lightweight AI-Native SDLC for Coding Agents

*Part 1 of 2 — Draft 1*

Prompt-to-code is quick, but it leaves too much unsaid: what is factual, what is assumed, what should be tested, and whether the code actually serves the intended journey. Traditional SDLC can overcorrect by creating more documents than decisions. For C4 Lens, I tried a smaller rule: one stage, one question, one canonical artifact.

The resulting lifecycle is Intent → C4 Context → Product Behavior → Architecture Review Pack → Boundary Contract if needed → Build Contract → Plan + Proof → Build + CI → Release Candidate → Product Assurance → Ship + Learn. It is deliberately sequential, but not ceremonious. Each gate is there to prevent a specific kind of guess.

Context comes before runtime architecture. Behavior comes before containers. Proof is written before implementation. Those choices prevented the usual gravity toward a database, an API, and a frontend split before the product justified any of them.

For this experiment, the boundary contract was skipped because a Streamlit monolith had no independently meaningful interface likely to drift. The useful artifacts were short: intent, context, product flow, architecture decision table, build contract, and proof plan. CI started with the first runnable slice.

This is not a claim that an LLM understands architecture. The point is to place its useful proposal capability inside a reviewable system with deterministic checks. Part 2 follows the actual C4 Lens build, including the limits encountered around credentials and deployment.
