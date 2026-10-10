import json
from xml.etree import ElementTree as ET

import pytest

from c4lens.export import export_json, export_png, export_svg
from c4lens.llm import (
    ProviderNotConfiguredError,
    apply_proposal_review,
    generate_model,
    sample_model,
)
from c4lens.models import C4Model
from c4lens.render import _embed_icons, diagram_dot
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


def test_gateway_adapter_uses_structured_output(monkeypatch):
    class Response:
        class Choice:
            class Message:
                content = sample_model("live").model_dump_json()

            message = Message()

        def __init__(self):
            self.choices = [self.Choice()]

    class Completions:
        def create(self, **kwargs):
            assert kwargs["response_format"]["type"] == "json_schema"
            assert kwargs["messages"][1]["content"] == "problem"
            assert "greenfield" in kwargs["messages"][0]["content"]
            assert "propose a minimal plausible container set" in kwargs["messages"][0]["content"]
            assert kwargs["response_format"]["json_schema"]["schema"]["properties"]["containers"]["minItems"] == 1
            return Response()

    class Chat:
        completions = Completions()

    class Client:
        chat = Chat()

    monkeypatch.setenv("AI_GATEWAY_MODEL", "test-model")
    assert generate_model("problem", client=Client()).problem_summary == "live"


def test_live_generation_requires_gateway_key(monkeypatch):
    monkeypatch.delenv("AI_GATEWAY_API_KEY", raising=False)
    with pytest.raises(ProviderNotConfiguredError):
        generate_model("problem")


def test_gateway_retries_zero_container_greenfield_draft(monkeypatch):
    empty = sample_model("empty").model_dump()
    empty["containers"] = []
    proposed = sample_model("corrected").model_dump()
    proposed["containers"][0]["provenance"] = "proposed_assumption"

    class Response:
        def __init__(self, content):
            self.choices = [type("Choice", (), {"message": type("Message", (), {"content": content})()})()]

    class Completions:
        def __init__(self):
            self.responses = [Response(json.dumps(empty)), Response(json.dumps(proposed))]
            self.calls = []

        def create(self, **kwargs):
            self.calls.append(kwargs)
            return self.responses.pop(0)

    completions = Completions()
    client = type("Client", (), {"chat": type("Chat", (), {"completions": completions})()})()
    monkeypatch.setenv("AI_GATEWAY_MODEL", "test-model")
    model = generate_model("problem", client=client)
    assert model.containers[0].provenance.value == "proposed_assumption"
    assert len(completions.calls) == 2
    assert "previous draft had zero containers" in completions.calls[1]["messages"][0]["content"]


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


def test_container_view_requires_a_container_and_cannot_export_a_duplicate_context():
    model = sample_model("x")
    data = model.model_dump()
    data["containers"] = []
    without_containers = C4Model.model_validate(data)
    result = validate_view(without_containers, "container")
    assert not result.valid
    assert result.errors == ["No Container architecture has been proposed yet."]
    with pytest.raises(ValueError, match="No Container architecture"):
        diagram_dot(without_containers, "container")
    with pytest.raises(ValueError, match="No Container architecture"):
        export_png(without_containers, "container")


def test_context_excludes_containers_and_svg_and_exports_work():
    model = apply_proposal_review(
        sample_model("x"), {"llm_provider", "relationship:1", "assumption:0"}, set()
    )
    dot = diagram_dot(model, "context", approved=True)
    assert "streamlit_app" not in dot
    svg = export_svg(model, "context")
    assert b"svg" in svg
    assert export_png(model, "container").startswith(b"\x89PNG")
    assert b'"system_name"' in export_json(model)


def test_final_svg_embeds_self_contained_pictograms():
    model = sample_model("x")
    graphviz_svg = '<svg xmlns="http://www.w3.org/2000/svg">' + "".join(
        f'<g id="node{index}" class="node"><title>{item_id}</title><polygon points="0,0 1,1"/>'
        '<text text-anchor="start" x="40" y="-20">Node</text></g>'
        for index, item_id in enumerate(("user", "c4_lens", "llm_provider", "streamlit_app"), 1)
    ) + "</svg>"
    final_svg = _embed_icons(graphviz_svg, model)
    namespace = {"svg": "http://www.w3.org/2000/svg"}
    root = ET.fromstring(final_svg)
    expected = {
        "user": ("person", {"circle", "path"}),
        "c4_lens": ("software-system", {"rect", "path"}),
        "llm_provider": ("external-system", {"rect", "path"}),
        "streamlit_app": ("container", {"rect"}),
    }
    for node in root.findall(".//svg:g[@class='node']", namespace):
        item_id = node.findtext("svg:title", namespaces=namespace)
        kind, required_geometry = expected[item_id]
        pictogram = node.find(f"svg:g[@class='c4-pictogram {kind}']", namespace)
        assert pictogram is not None
        geometry = {child.tag.rsplit("}", 1)[-1] for child in pictogram}
        assert required_geometry <= geometry
        assert all(child.attrib for child in pictogram)


def test_end_to_end_draft_to_approved_export_flow():
    draft = sample_model("A held-out incident review service with external alerts")
    assert draft.has_proposed_content()
    approved = apply_proposal_review(
        draft, {"llm_provider", "relationship:1", "assumption:0"}, set()
    )
    assert validate_model(approved, approved=True).valid
    assert export_svg(approved, "container")
