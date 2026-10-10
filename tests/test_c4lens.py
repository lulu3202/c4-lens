import pytest

from c4lens.export import export_json, export_png, export_svg
from c4lens.llm import (
    ProviderNotConfiguredError,
    apply_proposal_review,
    generate_model,
    sample_model,
)
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


def test_review_requires_each_proposal_and_honours_rejection():
    model = sample_model("x")
    with pytest.raises(ValueError, match="Every proposed"):
        apply_proposal_review(model, set(), set())
    reviewed = apply_proposal_review(
        model, {"llm_provider", "relationship:1", "assumption:0"}, set()
    )
    assert validate_model(reviewed, approved=True).valid
    rejected = apply_proposal_review(
        model, set(), {"llm_provider", "relationship:1", "assumption:0"}
    )
    assert "llm_provider" not in {item.id for item in rejected.all_elements()}
    assert validate_model(rejected, approved=True).valid


def test_anthropic_adapter_uses_structured_output(monkeypatch):
    class Response:
        parsed_output = sample_model("live")

    class Messages:
        def parse(self, **kwargs):
            assert kwargs["output_format"] is C4Model
            assert kwargs["messages"][0]["content"] == "problem"
            return Response()

    class Client:
        messages = Messages()

    monkeypatch.setenv("ANTHROPIC_MODEL", "test-model")
    assert generate_model("problem", client=Client()).problem_summary == "live"


def test_live_generation_requires_anthropic_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(ProviderNotConfiguredError):
        generate_model("problem")


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
    model = apply_proposal_review(
        sample_model("x"), {"llm_provider", "relationship:1", "assumption:0"}, set()
    )
    dot = diagram_dot(model, "context", approved=True)
    assert "streamlit_app" not in dot
    assert b"svg" in export_svg(model, "context")
    assert export_png(model, "container").startswith(b"\x89PNG")
    assert b'"system_name"' in export_json(model)


def test_end_to_end_draft_to_approved_export_flow():
    draft = sample_model("A held-out incident review service with external alerts")
    assert draft.has_proposed_content()
    approved = apply_proposal_review(
        draft, {"llm_provider", "relationship:1", "assumption:0"}, set()
    )
    assert validate_model(approved, approved=True).valid
    assert export_svg(approved, "container")
