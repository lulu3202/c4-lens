from __future__ import annotations

import json
import os
from typing import Any

from dotenv import load_dotenv

from .models import Assumption, C4Model, Element, ElementType, Provenance, Relationship

load_dotenv()

DEFAULT_MODEL = "openai/gpt-5.6-terra"


class ProviderNotConfiguredError(RuntimeError):
    """Raised when a live generation is requested without the required secret."""


def _greenfield_schema() -> dict[str, Any]:
    """Require a proposed runtime shape from live greenfield extraction."""
    schema = C4Model.model_json_schema()
    schema["properties"]["containers"]["minItems"] = 1
    return schema


def sample_model(problem: str) -> C4Model:
    """A deterministic fixture exclusively for tests; never an interactive fallback."""
    summary = problem.strip() or "A system requiring architecture review."
    return C4Model(
        system_name="C4 Lens",
        problem_summary=summary,
        people=[
            Element(
                id="user",
                name="Architecture reviewer",
                description="Reviews and approves generated architecture.",
                type=ElementType.PERSON,
                provenance=Provenance.STATED,
            )
        ],
        software_systems=[
            Element(
                id="c4_lens",
                name="C4 Lens",
                description="Turns a problem statement into reviewable C4 diagrams.",
                type=ElementType.SOFTWARE_SYSTEM,
                provenance=Provenance.DERIVED,
            ),
            Element(
                id="llm_provider",
                name="LLM provider",
                description="Proposes a structured architecture model.",
                type=ElementType.SOFTWARE_SYSTEM,
                provenance=Provenance.PROPOSED,
                external=True,
            ),
        ],
        containers=[
            Element(
                id="streamlit_app",
                name="Streamlit application",
                description="Collects input, presents review, and exports diagrams.",
                type=ElementType.CONTAINER,
                provenance=Provenance.DERIVED,
                parent_system_id="c4_lens",
                technology="Python / Streamlit",
            )
        ],
        relationships=[
            Relationship(
                source_id="user",
                target_id="c4_lens",
                description="Describes and reviews a system",
                provenance=Provenance.STATED,
            ),
            Relationship(
                source_id="c4_lens",
                target_id="llm_provider",
                description="Requests a structured draft",
                provenance=Provenance.PROPOSED,
            ),
        ],
        assumptions=[
            Assumption(
                text="An LLM provider will be available for live structured extraction."
            )
        ],
    )


def generate_model(problem: str, client: Any | None = None) -> C4Model:
    """Make one Vercel AI Gateway structured-output request and validate its result."""
    if client is None and not os.getenv("AI_GATEWAY_API_KEY"):
        raise ProviderNotConfiguredError(
            "Live Vercel AI Gateway generation is unavailable. Add AI_GATEWAY_API_KEY to local .env or Streamlit secrets."
        )
    if client is None:
        from openai import OpenAI

        client = OpenAI(
            api_key=os.getenv("AI_GATEWAY_API_KEY"),
            base_url="https://ai-gateway.vercel.sh/v1",
        )
    request = {
        "model": os.getenv("AI_GATEWAY_MODEL", DEFAULT_MODEL),
        "max_tokens": 4096,
        "messages": [
            {
                "role": "system",
                "content": "You propose a reviewable C4 architecture model for a greenfield system. Only people and software systems explicitly named by the user may be stated. Mark logical consequences as derived only when they follow directly from the user's words. You MUST return one or more runtime containers. A greenfield problem usually does not name them, so propose a minimal plausible container set for the named system. Mark every inferred container, its technology, inferred relationship, external integration, and architectural assumption as proposed_assumption. Include a concise proposed assumption explaining the container choices. Never present a proposed container as stated or derived. Include one non-external software system named system_name; every container belongs to it. Prefer a small useful architecture over a generic exhaustive one. Do not create components, DOT, or prose outside the JSON schema.",
            },
            {"role": "user", "content": problem},
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "c4_model",
                "strict": True,
                "schema": _greenfield_schema(),
            },
        },
    }
    response = client.chat.completions.create(**request)
    content = response.choices[0].message.content
    if not content:
        raise RuntimeError(
            "Vercel AI Gateway returned no structured architecture model."
        )
    model = C4Model.model_validate(json.loads(content))
    if model.containers:
        return model
    request["messages"][0]["content"] += " Your previous draft had zero containers and is invalid. Return a replacement model with 3 to 5 proposed containers, every container marked proposed_assumption, plus proposed relationships and assumptions that explain the choices."
    response = client.chat.completions.create(**request)
    content = response.choices[0].message.content
    if not content:
        raise RuntimeError(
            "Vercel AI Gateway returned no corrected architecture model."
        )
    model = C4Model.model_validate(json.loads(content))
    if not model.containers:
        raise RuntimeError(
            "Vercel AI Gateway did not propose a Container architecture. Try a more specific problem statement."
        )
    return model


def apply_proposal_review(
    model: C4Model, accepted: set[str], rejected: set[str]
) -> C4Model:
    """Apply explicit per-item human decisions; unreviewed proposals remain unapprovable."""
    data = model.model_dump()
    proposal_keys = {
        *[
            item.id
            for item in model.all_elements()
            if item.provenance == Provenance.PROPOSED
        ],
        *[
            f"relationship:{index}"
            for index, item in enumerate(model.relationships)
            if item.provenance == Provenance.PROPOSED
        ],
        *[
            f"assumption:{index}"
            for index, item in enumerate(model.assumptions)
            if item.provenance == Provenance.PROPOSED
        ],
    }
    if proposal_keys != accepted | rejected or accepted & rejected:
        raise ValueError(
            "Every proposed item needs one explicit accept or reject decision."
        )
    rejected_ids = {
        key for key in rejected if not key.startswith(("relationship:", "assumption:"))
    }
    for group in ("people", "software_systems", "containers"):
        data[group] = [item for item in data[group] if item["id"] not in rejected_ids]
        for item in data[group]:
            if (
                item["id"] in accepted
                and item["provenance"] == Provenance.PROPOSED.value
            ):
                item["provenance"] = Provenance.DERIVED.value
    data["relationships"] = [
        {
            **item,
            "provenance": Provenance.DERIVED.value
            if f"relationship:{index}" in accepted
            else item["provenance"],
        }
        for index, item in enumerate(data["relationships"])
        if f"relationship:{index}" not in rejected
        and item["source_id"] not in rejected_ids
        and item["target_id"] not in rejected_ids
    ]
    data["assumptions"] = [
        {
            **item,
            "provenance": Provenance.DERIVED.value
            if f"assumption:{index}" in accepted
            else item["provenance"],
        }
        for index, item in enumerate(data["assumptions"])
        if f"assumption:{index}" not in rejected
    ]
    return C4Model.model_validate(data)
