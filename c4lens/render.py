from __future__ import annotations

from html import escape
from textwrap import wrap

from graphviz import Digraph, Source

from .models import C4Model, Element
from .validate import validate_model, validate_view, view_elements

COLORS = {
    "person": "#6d3a78",
    "software_system": "#236a8a",
    "container": "#167c80",
    "external": "#64748b",
    "proposed": "#c97818",
}


def _lines(text: str, limit: int = 28, maximum: int = 2) -> str:
    lines = wrap(text, width=limit)[:maximum]
    if len(text) > sum(len(line) for line in lines):
        lines[-1] = lines[-1].rstrip(".") + "…"
    return "<BR/>".join(escape(line) for line in lines)


def _label(item: Element) -> str:
    proposed = "<BR/><FONT POINT-SIZE=\"9\">PROPOSED</FONT>" if item.provenance.value == "proposed_assumption" else ""
    external = "<BR/><FONT POINT-SIZE=\"9\">EXTERNAL</FONT>" if item.external else ""
    technology = f"<BR/><FONT POINT-SIZE=\"10\">{escape(item.technology)}</FONT>" if item.technology else ""
    return f"<<B>{escape(item.name)}</B>{external}{proposed}<BR/><FONT POINT-SIZE=\"10\">{_lines(item.description)}</FONT>{technology}>"


def _color(item: Element, approved: bool) -> str:
    if item.provenance.value == "proposed_assumption" and not approved:
        return COLORS["proposed"]
    if item.external:
        return COLORS["external"]
    return COLORS[item.type.value]


def diagram_dot(model: C4Model, view: str, approved: bool = False) -> str:
    result = validate_model(model, approved)
    view_result = validate_view(model, view)
    if not result.valid or not view_result.valid:
        raise ValueError("; ".join([*result.errors, *view_result.errors]))
    allowed = set(view_elements(model, view))
    primary = next(
        item
        for item in model.software_systems
        if item.name == model.system_name and not item.external
    )
    if view == "container":
        allowed.discard(primary.id)
    graph = Digraph("c4", format="svg")
    title = "System Context" if view == "context" else "Container"
    graph.attr(
        rankdir="LR",
        bgcolor="white",
        pad="0.35",
        nodesep="0.55",
        ranksep="0.8",
        labelloc="t",
        label=f"{title}\\n{model.system_name}",
        fontname="Arial",
        fontsize="20",
        fontcolor="#172033",
    )
    graph.attr(
        "node",
        shape="box",
        style="rounded,filled",
        fontname="Arial",
        fontcolor="white",
        margin="0.14",
        width="2.35",
        height="0.7",
    )
    if view == "container":
        with graph.subgraph(name="cluster_target_system") as cluster:
            cluster.attr(
                label=model.system_name,
                color="#167c80",
                penwidth="2",
                style="rounded",
                margin="20",
                fontname="Arial",
                fontsize="15",
                fontcolor="#0f4f52",
            )
            for item in model.containers:
                cluster.node(item.id, _label(item), fillcolor=_color(item, approved))
    for item in model.all_elements():
        if item.id in allowed:
            graph.node(item.id, _label(item), fillcolor=_color(item, approved))
    for rel in model.relationships:
        if rel.source_id in allowed and rel.target_id in allowed:
            graph.edge(
                rel.source_id,
                rel.target_id,
                label="\\n".join(wrap(rel.description, width=24)),
                fontname="Arial",
                fontsize="10",
                fontcolor="#334155",
                color="#64748b",
                penwidth="1.2",
            )
    return graph.source


def render_svg(model: C4Model, view: str, approved: bool = False) -> bytes:
    dot = diagram_dot(model, view, approved)
    try:
        return Source(dot, format="svg").pipe()
    except Exception:  # noqa: BLE001 - Graphviz executable is optional locally
        # Useful local fallback when the Graphviz executable is not installed.
        allowed = set(view_elements(model, view))
        if view == "container":
            primary = next(
                item
                for item in model.software_systems
                if item.name == model.system_name and not item.external
            )
            allowed.discard(primary.id)
        items = [item for item in model.all_elements() if item.id in allowed]
        width, height = 1000, max(300, 130 * len(items))
        blocks = []
        for index, item in enumerate(items):
            y = 40 + index * 115
            color = _color(item, approved)
            blocks.append(
                f'<rect x="80" y="{y}" width="360" height="80" rx="10" fill="{color}"/><text x="100" y="{y + 30}" fill="white" font-family="Arial" font-size="18">{escape(item.name)}</text><text x="100" y="{y + 57}" fill="white" font-family="Arial" font-size="13">{escape(item.description)}</text>'
            )
        title = f"{escape(model.system_name)} — {'System Context' if view == 'context' else 'Container'}"
        return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"><rect width="100%" height="100%" fill="white"/><text x="40" y="28" font-family="Arial" font-size="20" font-weight="bold">{title}</text>{"".join(blocks)}</svg>'.encode()
