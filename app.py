from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components

from c4lens.export import export_json, export_png, export_svg
from c4lens.llm import apply_proposal_review, generate_model
from c4lens.models import C4Model, Provenance
from c4lens.render import render_svg
from c4lens.validate import validate_model

st.set_page_config(page_title="C4 Lens", page_icon="◌", layout="wide")
st.title("C4 Lens")
st.caption(
    "Turn a software problem into reviewable C4 diagrams — with assumptions kept visible."
)

if "model" not in st.session_state:
    st.session_state.model = None
    st.session_state.approved = False

problem = st.text_area(
    "Describe your system",
    placeholder="For example: A service that helps teams review architecture proposals…",
    height=160,
)
if st.button("Generate architecture", type="primary", disabled=not problem.strip()):
    with st.spinner("Proposing a structured architecture model…"):
        try:
            st.session_state.model = generate_model(problem)
            st.session_state.approved = False
        except Exception as exc:  # noqa: BLE001 - provider SDK failures are user-facing
            st.error(f"Generation failed: {exc}")

model: C4Model | None = st.session_state.model
if model is None:
    st.info(
        "Enter a problem statement to create a reviewable draft. Live Vercel AI Gateway generation requires `AI_GATEWAY_API_KEY`; the deterministic fixture is used only by automated tests."
    )
    st.stop()

st.divider()
if not st.session_state.approved:
    st.warning("Draft — proposed assumptions highlighted")
else:
    st.success("Approved architecture — canonical diagrams are ready to export.")

left, right = st.columns((1, 1))
with left:
    st.subheader("Review the model")
    groups = (
        (
            "Stated facts",
            [x for x in model.all_elements() if x.provenance == Provenance.STATED],
        ),
        (
            "Derived structure",
            [x for x in model.all_elements() if x.provenance == Provenance.DERIVED],
        ),
        (
            "Proposed assumptions",
            [x for x in model.all_elements() if x.provenance == Provenance.PROPOSED],
        ),
    )
    for title, values in groups:
        st.markdown(f"**{title}**")
        if values:
            for item in values:
                st.write(f"• {item.name}: {item.description}")
        else:
            st.caption("None")
    for assumption in model.assumptions:
        st.warning(f"Assumption: {assumption.text}")
    with st.expander("Lightweight correction (edit model JSON)"):
        edited = st.text_area(
            "Canonical model JSON", value=model.model_dump_json(indent=2), height=360
        )
        if st.button("Apply correction"):
            try:
                st.session_state.model = C4Model.model_validate_json(edited)
                st.rerun()
            except Exception as exc:  # noqa: BLE001 - show all schema parse errors
                st.error(f"Could not apply correction: {exc}")
    validation = validate_model(model)
    if not validation.valid:
        st.error(" ".join(validation.errors))
    if not st.session_state.approved:
        st.markdown("**Decide each proposed item before approval**")
        proposals = [
            (item.id, f"{item.name}: {item.description}")
            for item in model.all_elements()
            if item.provenance == Provenance.PROPOSED
        ]
        proposals += [
            (
                f"relationship:{index}",
                f"Relationship: {item.source_id} → {item.target_id} — {item.description}",
            )
            for index, item in enumerate(model.relationships)
            if item.provenance == Provenance.PROPOSED
        ]
        proposals += [
            (f"assumption:{index}", f"Assumption: {item.text}")
            for index, item in enumerate(model.assumptions)
            if item.provenance == Provenance.PROPOSED
        ]
        decisions = {}
        for key, label in proposals:
            decisions[key] = st.radio(
                label,
                ["Choose…", "Accept", "Reject"],
                key=f"review-{key}",
                horizontal=True,
            )
        if st.button("Approve reviewed architecture"):
            accepted = {
                key for key, decision in decisions.items() if decision == "Accept"
            }
            rejected = {
                key for key, decision in decisions.items() if decision == "Reject"
            }
            try:
                st.session_state.model = apply_proposal_review(
                    model, accepted, rejected
                )
                approved_validation = validate_model(
                    st.session_state.model, approved=True
                )
                if not approved_validation.valid:
                    raise ValueError(" ".join(approved_validation.errors))
                st.session_state.approved = True
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))

with right:
    st.subheader("Visualize")
    context, container = st.tabs(["System Context", "Container"])
    for tab, view in ((context, "context"), (container, "container")):
        with tab:
            try:
                components.html(
                    render_svg(
                        model, view, approved=st.session_state.approved
                    ).decode(),
                    height=520,
                    scrolling=True,
                )
            except ValueError as exc:
                st.error(str(exc))

if st.session_state.approved:
    st.subheader("Export canonical architecture")
    one, two, three = st.columns(3)
    with one:
        st.download_button(
            "Download System Context SVG",
            export_svg(model, "context"),
            "c4-context.svg",
            "image/svg+xml",
        )
    with two:
        st.download_button(
            "Download Container PNG",
            export_png(model, "container"),
            "c4-container.png",
            "image/png",
        )
    with three:
        st.download_button(
            "Download model JSON",
            export_json(model),
            "c4-model.json",
            "application/json",
        )
