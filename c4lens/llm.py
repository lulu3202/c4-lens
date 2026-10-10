from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv

from .models import Assumption, C4Model, Element, ElementType, Provenance, Relationship

load_dotenv()

DEFAULT_MODEL = "claude-sonnet-4-6"


class ProviderNotConfiguredError(RuntimeError):
    """Raised when a live generation is requested without the required secret."""


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
    """Make exactly one Anthropic structured-output request and validate its result."""
    if client is None and not os.getenv("ANTHROPIC_API_KEY"):
        raise ProviderNotConfiguredError(
            "Live Anthropic generation is unavailable. Add ANTHROPIC_API_KEY to local .env or Streamlit secrets."
        )
    if client is None:
        from anthropic import Anthropic

        client = Anthropic()
    response = client.messages.parse(
        model=os.getenv("ANTHROPIC_MODEL", DEFAULT_MODEL),
        max_tokens=4096,
        system="You propose a reviewable C4 architecture model. Only explicit user claims may be stated. Mark inferred entities, relationships, and assumptions as proposed_assumption. Include one non-external software system named system_name; containers belong to it. Do not create components, DOT, or prose outside the schema.",
        messages=[{"role": "user", "content": problem}],
        output_format=C4Model,
    )
    parsed = response.parsed_output
    if parsed is None:
        raise RuntimeError("Anthropic returned no structured architecture model.")
    return C4Model.model_validate(parsed)


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
