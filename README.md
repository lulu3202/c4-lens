# C4 Lens

C4 Lens turns a software problem statement into reviewable C4 System Context and Container diagrams. It deliberately distinguishes stated facts, derived structure, and proposed assumptions before a person approves the model.

## V1

- One structured, Pydantic-backed C4 model
- Deterministic validation and human approval gate
- Context / Container tabs and SVG, PNG, JSON exports
- Session-only Streamlit state

## How it works

One LLM call may propose a structured model. Python validates IDs, relationship endpoints, C4 hierarchy, provenance, and view membership before Graphviz renders diagrams. No LLM output becomes approved architecture by itself.

## Run locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

`AI_GATEWAY_API_KEY` enables the single Vercel AI Gateway adapter; `AI_GATEWAY_MODEL` defaults to `openai/gpt-5.6-terra`. Without a key, interactive live generation is unavailable (the deterministic fixture is test-only). Do not commit either value.

## Quality and deployment

Run `ruff check .` and `pytest -q`. GitHub Actions runs both plus an import smoke check. Streamlit Community Cloud can deploy this repository directly; set `AI_GATEWAY_API_KEY` in its secret configuration and optionally `AI_GATEWAY_MODEL`. The live gateway smoke test is human action required until a key is configured.

The lifecycle map is [`docs/01-intent.md`](docs/01-intent.md) through [`docs/08-learnings.md`](docs/08-learnings.md). C4 Lens is independent software and is not affiliated with Structurizr or the C4 Model authors. No license has been selected.
