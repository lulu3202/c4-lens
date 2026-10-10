from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components

from c4lens.export import export_json, export_png, export_svg
from c4lens.llm import generate_model, resolve_proposals
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
        "Enter a problem statement to create a reviewable draft. Without `OPENAI_API_KEY`, C4 Lens uses a clearly labelled deterministic draft."
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
    if not st.session_state.approved and st.button(
        "Resolve proposed assumptions and approve"
    ):
        st.session_state.model = resolve_proposals(model)
        approved_validation = validate_model(st.session_state.model, approved=True)
        if approved_validation.valid:
            st.session_state.approved = True
            st.rerun()
        st.error(" ".join(approved_validation.errors))

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
