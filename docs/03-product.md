# Product Behavior

```mermaid
flowchart LR
  A[Describe system] --> B[Review draft]
  B --> C{Resolve assumptions?}
  C -->|correct| B
  C -->|approve| D[View Context / Container]
  D --> E[Export SVG, PNG, JSON]
```

The user enters a problem, then sees stated facts, derived structure, and proposed assumptions. The draft banner remains until the user explicitly accepts or rejects every proposed item, or corrects it in JSON, and approves it. Invalid models show errors instead of renderable approved output. A failed live generation reports an error; no state is persisted beyond the browser session.
