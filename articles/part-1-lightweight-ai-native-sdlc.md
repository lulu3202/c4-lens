# A Lightweight AI-Native SDLC for Building with Coding Agents

*Part 1 of 2*

Coding agents make implementation startlingly fast. That is useful, but it also makes it easy to travel from a sentence to a convincing-looking codebase before anyone has made product behavior, architecture choices, evidence, or human decisions explicit. Traditional process can overcorrect: a solo builder ends up maintaining more documents than decisions. I wanted a middle path—small enough to use in a greenfield build, disciplined enough to catch the mistakes that speed makes cheap.

The rule is simple: **one question, one canonical artifact**. The lifecycle is:

> Intent → C4 Context → Product Behavior → Architecture Review Pack → Boundary Contract if needed → Build Contract → Plan + Proof → Build + CI → Release Candidate → Product Assurance → Ship + Learn

It is not a collection of required templates. It is a sequence of questions. A stage stays only while it answers a question the next stage cannot safely guess.

![Lifecycle Context visual](../docs/article-assets/02-context.png)

*Look at the boundary, not the implementation detail: this is the early visual that keeps the product in its world before runtime architecture is invented.*

## Intent: what outcome are we choosing?

Intent answers: *what are we trying to make, for whom, and what are we deliberately not making?* It comes first because implementation pressure turns every imaginable capability into an implied requirement. The minimum artifact is a short problem statement with a target outcome, success condition, constraints, and exclusions. Skip it only for a change whose intent is already unambiguous and recorded, such as a tightly scoped bug fix.

For a new product, a paragraph is sufficient. The point is not to predict every screen. It is to give later decisions a reference point: does this new dependency, workflow, or feature advance the stated outcome, or is it scope gravity?

## C4 Context: what exists around the product?

Context answers: *who uses the system, what is the system boundary, and what external systems matter?* Its position is intentional. Context comes before runtime architecture because “we need a database and an API” is usually an answer to a question nobody has asked yet.

The minimum artifact is a System Context diagram and a few relationship statements. It may show a person, the product, and an external provider. It does not need containers or components. Skip it only when modifying a known, stable boundary where that context already exists and remains accurate.

This stage is particularly useful with coding agents. A model can propose technical parts fluently; that does not mean the parts belong. A context artifact gives a reviewer a way to say, “that relationship is outside the product,” before a generated implementation makes it expensive to remove.

## Product Behavior: what must a person be able to do?

Behavior answers: *what is the journey, what decisions are made, and what is the expected result?* It follows Context because behavior should serve an identified actor and boundary, not a speculative stack. The minimum artifact is a concise flow: entry, decision or review, outcome, and failure/empty states where meaningful. A short acceptance list often works better than a page of prose.

Only after behavior is concrete is a Container view useful. This is the key ordering rule: **behavior before container**. A runtime design that cannot point to a behavior it supports is often platform preference disguised as architecture. Skip a separate behavior artifact only when the requested change is mechanically contained and the current journey is already documented.

## Architecture Review Pack: which design decisions are consequential?

This stage answers: *what is the smallest viable technical shape, and what complexity is being rejected?* The minimum is a decision table or compact review pack: proposed shape, alternatives, reasons, risks, and a Container diagram when runtime structure is justified. It is not an architecture diary.

For a small build, “one Python/Streamlit application, one provider adapter, validation, and rendering” can be a complete answer. The important companion list may be what is not needed yet: a database, separate API, React client, workflow framework, microservices, or hosted architecture runtime. This stage can be merged into the build contract when no decision has meaningful trade-offs; otherwise it should stand alone so the trade-off remains reviewable.

Component diagrams are optional. They add value when internal responsibilities are independently complex or likely to drift. They are not proof of maturity. In the same spirit, do not create an OpenAPI document because an SDLC diagram happens to have a box for it.

## Boundary Contract: does an interface deserve its own agreement?

Boundary Contract answers: *what must remain true across an independently meaningful interface?* Its minimum artifact might be an OpenAPI contract, event schema, CLI contract, or a provider adapter interface. It is conditional: create it when a boundary is independently owned, deployed, versioned, or expected to drift. Skip it when the interface is internal to one small deployable and the build contract already constrains it.

That conditionality matters. Requiring a contract for every function pushes a small product back toward ceremony. Omitting it when another team or service needs a stable promise creates a different kind of ambiguity. The artifact should match the risk, not the process diagram.

## Build Contract: what may the implementation assume?

The Build Contract answers: *what does the agent propose, what does deterministic code decide, and where must a human decide?* It is a small but powerful boundary. In C4 Lens, the model may propose a structured architecture; deterministic code validates structure; a human accepts or rejects assumptions before canonical exports exist.

This stage belongs before detailed plans because it prevents accidental authority. Without it, a generated model, parsed JSON, or a passing UI can quietly become “the architecture.” The minimum artifact is a list of invariants, ownership, and explicit non-goals. Skip it only when no generative or ambiguous decision exists.

## Plan + Proof: how will we know this worked?

Plan + Proof answers: *what evidence would change our mind?* Write it before implementation, while a plausible implementation has not biased the test. The minimum artifact is a short set of deterministic cases and hands-on checks: success path, invalid input, review gate, export, and any real integration boundary.

This is not a demand for exhaustive test plans. It is a demand that the intended proof exists before code. A diagram generator, for example, needs more than schema tests: it needs a real rendered output and a user-visible review decision. Skip only the checks that cannot fail independently; do not skip the evidence.

## Build + CI: can the first vertical slice keep proving itself?

Build + CI answers: *does the smallest runnable path work repeatedly without hidden local state?* CI begins with the first vertical slice, not after “the real build” is done. The minimum is lint, deterministic tests, and an import/compile check. Credentialed services should be narrow adapters that tests mock; otherwise every contribution becomes hostage to someone’s key or billing account.

This is where coding agents shine. They can make the first slice quickly, but a check that starts with that slice keeps speed from becoming irreproducibility. Skip no CI stage merely because the repository is small; keep it proportionate instead.

## Release Candidate and Product Assurance: what does the actual product do?

A Release Candidate answers: *what exact artifact will users encounter?* It precedes Product Assurance because assurance against local fragments is weaker than assurance against the deployed candidate. The minimum is a deployed build or a production-like package identified by commit/version and configured with the intended boundary.

Product Assurance asks: *does it work in the way a real reviewer will use it?* It is where screenshots, live interactions, exports, and integration behavior matter. Unit tests can prove a parser, but they cannot prove that a browser paints the final SVG or that a deployment is serving the branch being debugged. Skip nothing here; reduce the scenario set to the risks that matter.

## Ship + Learn: what changes in the next loop?

Shipping answers: *is this useful enough to release with honest limits?* Learning answers: *which process or product assumption did evidence disprove?* The minimum artifact is a release note and a short learning record. This stage is part of the lifecycle, not a retrospective indulgence: it turns real defects into a better next build contract and proof plan.

An earlier Skill Matcher experiment supplied the contrast. It accumulated overlapping artifacts, made architecture decisions too early, and documented more than it decided. This approach was independently simplified after that experience. It is also informed by AI-native SDLC thinking. Anthropic’s public guidance describes agentic coding workflows such as exploration, planning, implementation, and commit, while intentionally leaving room for teams to choose their own process [in its engineering guidance](https://www.anthropic.com/engineering/claude-code-best-practices). The useful lesson is not to imitate a vendor workflow; it is to make each human decision and proof explicit enough for agents to help without silently owning the decision.

Part 2 puts this lifecycle under pressure in a real one-day greenfield build: C4 Lens, a tool that turns a problem statement into a reviewable Context and Container model.
