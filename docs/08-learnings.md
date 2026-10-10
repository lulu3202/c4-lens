# Learnings

The short lifecycle made the meaningful constraints visible early: approval is a product state, not a diagram style, and one canonical model prevents Context and Container drift. A separate backend, persistence, and an API contract were unnecessary. The one adjustment was adding a deterministic fallback so tests and the demo remain useful without credentials. Next time, the Context → behavior → container ordering is worth keeping; deployment authentication remains an external handoff.
