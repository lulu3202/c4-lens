from __future__ import annotations

from dataclasses import dataclass

from .models import C4Model, ElementType


@dataclass(frozen=True)
class ValidationResult:
    errors: list[str]

    @property
    def valid(self) -> bool:
        return not self.errors


def validate_model(model: C4Model, approved: bool = False) -> ValidationResult:
    errors: list[str] = []
    elements = model.all_elements()
    ids = [item.id for item in elements]
    if len(ids) != len(set(ids)):
        errors.append("Entity IDs must be unique.")
    lookup = {item.id: item for item in elements}
    system = next(
        (
            item
            for item in model.software_systems
            if item.name == model.system_name and not item.external
        ),
        None,
    )
    if system is None:
        errors.append(
            "A non-external software system matching system_name is required."
        )
    for container in model.containers:
        if not container.parent_system_id or container.parent_system_id not in lookup:
            errors.append(
                f"Container '{container.id}' must reference an existing parent system."
            )
        elif lookup[container.parent_system_id].type != ElementType.SOFTWARE_SYSTEM:
            errors.append(
                f"Container '{container.id}' parent must be a software system."
            )
        if not container.description.strip():
            errors.append(f"Container '{container.id}' needs a clear responsibility.")
    for rel in model.relationships:
        if rel.source_id not in lookup or rel.target_id not in lookup:
            errors.append(
                f"Relationship '{rel.source_id} → {rel.target_id}' has an unknown endpoint."
            )
        if not rel.description.strip():
            errors.append("Relationships need a direction and description.")
    if approved and model.has_proposed_content():
        errors.append("Proposed assumptions must be resolved before approval.")
    return ValidationResult(errors)


def view_elements(model: C4Model, view: str) -> list[str]:
    if view == "context":
        return [item.id for item in [*model.people, *model.software_systems]]
    return [
        item.id for item in [*model.people, *model.software_systems, *model.containers]
    ]


def validate_view(model: C4Model, view: str) -> ValidationResult:
    errors: list[str] = []
    if view not in {"context", "container"}:
        return ValidationResult(["Unknown view."])
    if view == "context" and model.containers:
        # Containers are deliberately excluded, not invalid in the canonical model.
        pass
    if view == "container":
        if not model.containers:
            errors.append("No Container architecture has been proposed yet.")
        primary = next(
            (
                item
                for item in model.software_systems
                if item.name == model.system_name and not item.external
            ),
            None,
        )
        if primary and any(c.parent_system_id != primary.id for c in model.containers):
            errors.append(
                "Container view may only contain containers inside the described system."
            )
    return ValidationResult(errors)
