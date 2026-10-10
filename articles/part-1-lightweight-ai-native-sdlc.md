# Building a Lightweight AI-Native SDLC for Coding Agents

*Part 1 of 2 — Draft 1*

Prompt-to-code is quick, but it leaves too much unsaid: what is factual, what is assumed, what should be tested, and whether the code actually serves the intended journey. Traditional SDLC can overcorrect by creating more documents than decisions. For C4 Lens, I tried a smaller rule: one stage, one question, one canonical artifact.

The resulting lifecycle is Intent → C4 Context → Product Behavior → Architecture Review Pack → Boundary Contract if needed → Build Contract → Plan + Proof → Build + CI → Release Candidate → Product Assurance → Ship + Learn. It is deliberately sequential, but not ceremonious. Each gate is there to prevent a specific kind of guess.

Context comes before runtime architecture. Behavior comes before containers. Proof is written before implementation. Those choices prevented the usual gravity toward a database, an API, and a frontend split before the product justified any of them.

For this experiment, the boundary contract was skipped because a Streamlit monolith had no independently meaningful interface likely to drift. The useful artifacts were short: intent, context, product flow, architecture decision table, build contract, and proof plan. CI started with the first runnable slice.

The order matters more than the names of the documents. Intent names the outcome and the exclusions before implementation pressure turns every possibility into a feature. Context asks what the thing is in the world and postpones runtime detail. Product behavior then makes the actual user decision visible. Only then is a container view useful: it has a behavior to support rather than an imagined platform to justify.

The Architecture Review Pack is deliberately a decision record, not an architecture diary. It makes consequential choices visible — in this case whether persistence, a separate API, or a client application are justified. A Boundary Contract is conditional: create one when an independently meaningful interface might drift, not because a lifecycle diagram has a box for it. The same applies to OpenAPI and component diagrams.

Build Contract and Plan + Proof turn the approved direction into checks. The important move is writing down what would fail before code makes a plausible-looking alternative. CI starts with the first runnable slice, so the feedback loop is already there when the system is still small. A release candidate comes before Product Assurance because assurance should test the closest thing to the product a user will encounter, not a collection of unit tests.

The earlier Skill Matcher experiment was useful mainly as contrast: overlapping artifacts and premature decisions created more history than evidence. This version was independently adapted from AI-native SDLC thinking, including public Anthropic/Claude material; any published citation should be verified against a primary source first. It is not a claim that an LLM understands architecture. The point is to place its useful proposal capability inside a reviewable system with deterministic checks. Part 2 follows the actual C4 Lens build, including the limits encountered around credentials and deployment.
