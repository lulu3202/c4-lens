from __future__ import annotations

from html import escape

from graphviz import Digraph, Source

from .models import C4Model, Element
from .validate import validate_model, validate_view, view_elements

COLORS = {"person": "#084c61", "software_system": "#16697a", "container": "#489fb5"}


def _label(item: Element) -> str:
    provenance = " • proposed" if item.provenance.value == "proposed_assumption" else ""
    scope = " [external]" if item.external else ""
    tech = f"\\n[{item.technology}]" if item.technology else ""
    return f"{item.name}{scope}{provenance}\\n{item.description}{tech}"


def diagram_dot(model: C4Model, view: str, approved: bool = False) -> str:
    result = validate_model(model, approved)
    view_result = validate_view(model, view)
    if not result.valid or not view_result.valid:
        raise ValueError("; ".join([*result.errors, *view_result.errors]))
    allowed = set(view_elements(model, view))
    graph = Digraph("c4", format="svg")
    graph.attr(rankdir="LR", bgcolor="white", pad="0.3", nodesep="0.45", ranksep="0.8")
    graph.attr(
        "node",
        shape="box",
        style="rounded,filled",
        fontname="Arial",
        fontcolor="white",
        margin="0.18",
    )
    for item in model.all_elements():
        if item.id in allowed:
            color = (
                "#d97706"
                if item.provenance.value == "proposed_assumption" and not approved
                else COLORS[item.type.value]
            )
            graph.node(item.id, _label(item), fillcolor=color)
    for rel in model.relationships:
        if rel.source_id in allowed and rel.target_id in allowed:
            graph.edge(
                rel.source_id,
                rel.target_id,
                label=rel.description,
                fontname="Arial",
                fontsize="10",
            )
    return graph.source


def render_svg(model: C4Model, view: str, approved: bool = False) -> bytes:
    dot = diagram_dot(model, view, approved)
    try:
        return Source(dot, format="svg").pipe()
    except Exception:  # noqa: BLE001 - Graphviz executable is optional locally
        # Useful local fallback when the Graphviz executable is not installed.
        allowed = set(view_elements(model, view))
        items = [item for item in model.all_elements() if item.id in allowed]
        width, height = 1000, max(300, 130 * len(items))
        blocks = []
        for index, item in enumerate(items):
            y = 40 + index * 115
            color = (
                "#d97706"
                if item.provenance.value == "proposed_assumption" and not approved
                else COLORS[item.type.value]
            )
            blocks.append(
                f'<rect x="80" y="{y}" width="360" height="80" rx="10" fill="{color}"/><text x="100" y="{y + 30}" fill="white" font-family="Arial" font-size="18">{escape(item.name)}</text><text x="100" y="{y + 57}" fill="white" font-family="Arial" font-size="13">{escape(item.description)}</text>'
            )
        title = f"{escape(model.system_name)} — {'System Context' if view == 'context' else 'Container'}"
        return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"><rect width="100%" height="100%" fill="white"/><text x="40" y="28" font-family="Arial" font-size="20" font-weight="bold">{title}</text>{"".join(blocks)}</svg>'.encode()
