from __future__ import annotations

import os

from .models import Assumption, C4Model, Element, ElementType, Provenance, Relationship


def sample_model(problem: str) -> C4Model:
    """A deterministic reviewable draft used when no live provider is configured."""
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


def generate_model(problem: str) -> C4Model:
    """Single-provider adapter. Falls back to an explicit deterministic draft without a key."""
    if not os.getenv("OPENAI_API_KEY"):
        return sample_model(problem)
    from openai import OpenAI

    client = OpenAI()
    response = client.beta.chat.completions.parse(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[
            {
                "role": "system",
                "content": "Propose a small C4Model. Never present inferred information as stated: mark it proposed_assumption. Return only the requested schema.",
            },
            {"role": "user", "content": problem},
        ],
        response_format=C4Model,
    )
    parsed = response.choices[0].message.parsed
    if parsed is None:
        raise RuntimeError("The LLM returned no structured architecture model.")
    return parsed


def resolve_proposals(model: C4Model) -> C4Model:
    """Record a human review decision by turning draft proposals into derived structure."""
    data = model.model_dump()
    for group in ("people", "software_systems", "containers", "relationships"):
        for item in data[group]:
            if item["provenance"] == Provenance.PROPOSED.value:
                item["provenance"] = Provenance.DERIVED.value
    data["assumptions"] = []
    return C4Model.model_validate(data)
