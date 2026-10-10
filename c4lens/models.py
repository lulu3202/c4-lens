from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, model_validator


class Provenance(str, Enum):
    STATED = "stated"
    DERIVED = "derived"
    PROPOSED = "proposed_assumption"


class ElementType(str, Enum):
    PERSON = "person"
    SOFTWARE_SYSTEM = "software_system"
    CONTAINER = "container"


class Element(BaseModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9_-]*$")
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    type: ElementType
    provenance: Provenance
    external: bool = False
    parent_system_id: str | None = None
    technology: str | None = None


class Relationship(BaseModel):
    source_id: str
    target_id: str
    description: str = Field(min_length=1)
    technology: str | None = None
    provenance: Provenance


class Assumption(BaseModel):
    text: str = Field(min_length=1)
    provenance: Provenance = Provenance.PROPOSED


class C4Model(BaseModel):
    system_name: str = Field(min_length=1)
    problem_summary: str = Field(min_length=1)
    people: list[Element] = []
    software_systems: list[Element] = []
    containers: list[Element] = []
    relationships: list[Relationship] = []
    assumptions: list[Assumption] = []

    @model_validator(mode="after")
    def category_types_match(self) -> C4Model:
        groups = (
            (self.people, ElementType.PERSON),
            (self.software_systems, ElementType.SOFTWARE_SYSTEM),
            (self.containers, ElementType.CONTAINER),
        )
        for elements, expected in groups:
            if any(item.type != expected for item in elements):
                raise ValueError(
                    f"Elements must be filed under their {expected.value} category"
                )
        return self

    def all_elements(self) -> list[Element]:
        return [*self.people, *self.software_systems, *self.containers]

    def has_proposed_content(self) -> bool:
        return any(
            item.provenance == Provenance.PROPOSED for item in self.all_elements()
        ) or bool(self.assumptions)
