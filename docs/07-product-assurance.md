# Product Assurance

**Status: READY WITH DOCUMENTED LIMITATIONS**

## Release evidence

The Streamlit Community Cloud deployment succeeded. Live generation through Vercel AI Gateway succeeded in the deployed application; the configured default model is `openai/gpt-5.6-terra`. The application validates structured model output with Pydantic, then applies deterministic C4 hierarchy, relationship, provenance, and approval checks.

System Context and Container are rendered from the same canonical model. Proposed entities, relationships, and architectural choices require an explicit human **Accept** or **Reject** decision. Canonical JSON, SVG, and PNG exports remain unavailable until approval. The final SVG pipeline includes native pictograms, and deployed smoke testing verified the application display and exports.

Final local quality checks pass: `ruff check .` and `pytest -q` (**12 tests**). Tests mock the Vercel AI Gateway boundary, so CI remains credential-independent.

## Documented limitations

1. Wide Container diagrams can be visually compressed in Streamlit's half-width visualization column. Their SVG and PNG exports remain usable at natural size.
2. Model extraction is probabilistic. In one live tutor example, human actors were classified as external. The review gate is intentional: proposed output is not architecture truth.
3. C4 Simon was unavailable in this environment. Deterministic C4 hierarchy and rule validation was used instead.

These are not release blockers for V1. They are visible operating constraints for reviewers and future iterations.
