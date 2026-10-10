from c4lens.export import export_json, export_png, export_svg
from c4lens.llm import resolve_proposals, sample_model
from c4lens.models import C4Model
from c4lens.render import diagram_dot
from c4lens.validate import validate_model, validate_view


def test_deterministic_draft_is_valid_but_not_approvable():
    model = sample_model("A system for reviewing architecture")
    assert validate_model(model).valid
    assert not validate_model(model, approved=True).valid
    assert (
        "proposed assumptions" in validate_model(model, approved=True).errors[0].lower()
    )


def test_review_resolves_assumptions_before_approval():
    resolved = resolve_proposals(sample_model("x"))
    assert not resolved.assumptions
    assert validate_model(resolved, approved=True).valid


def test_invalid_relationship_and_duplicate_ids_are_rejected():
    model = sample_model("x")
    data = model.model_dump()
    data["people"].append(data["people"][0].copy())
    data["relationships"].append(
        {
            "source_id": "missing",
            "target_id": "c4_lens",
            "description": "bad",
            "provenance": "stated",
        }
    )
    result = validate_model(C4Model.model_validate(data))
    assert any("unique" in error for error in result.errors)
    assert any("unknown endpoint" in error for error in result.errors)


def test_container_must_belong_to_described_system():
    model = sample_model("x")
    data = model.model_dump()
    data["containers"][0]["parent_system_id"] = "llm_provider"
    result = validate_view(C4Model.model_validate(data), "container")
    assert not result.valid


def test_context_excludes_containers_and_svg_and_exports_work():
    model = resolve_proposals(sample_model("x"))
    dot = diagram_dot(model, "context", approved=True)
    assert "streamlit_app" not in dot
    assert b"svg" in export_svg(model, "context")
    assert export_png(model, "container").startswith(b"\x89PNG")
    assert b'"system_name"' in export_json(model)


def test_end_to_end_draft_to_approved_export_flow():
    draft = sample_model("A held-out incident review service with external alerts")
    assert draft.has_proposed_content()
    approved = resolve_proposals(draft)
    assert validate_model(approved, approved=True).valid
    assert export_svg(approved, "container")
