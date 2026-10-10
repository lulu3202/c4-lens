from __future__ import annotations

import html
import re
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


def _icon_kind(item: Element) -> str:
    if item.external:
        return "external-system"
    return {"person": "person", "software_system": "software-system", "container": "container"}[item.type.value]


def _pictogram(kind: str, x: float, y: float) -> str:
    common = 'fill="none" stroke="#ffffff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"'
    if kind == "person":
        geometry = f'<circle cx="{x + 8}" cy="{y + 5}" r="3" fill="#ffffff"/><path d="M{x + 2} {y + 15}c1-4 3-6 6-6s5 2 6 6" {common}/>'
    elif kind == "software-system":
        geometry = f'<rect x="{x + 1}" y="{y + 2}" width="14" height="10" rx="1.5" {common}/><path d="M{x + 5} {y + 16}h6M{x + 8} {y + 12}v4" {common}/>'
    elif kind == "external-system":
        geometry = f'<rect x="{x + 1}" y="{y + 4}" width="11" height="11" rx="1.5" {common}/><path d="M{x + 9} {y + 2}h6v6M{x + 15} {y + 2} {x + 8} {y + 9}" {common}/>'
    else:
        geometry = f'<rect x="{x + 1}" y="{y + 2}" width="14" height="4" rx="1" {common}/><rect x="{x + 1}" y="{y + 8}" width="14" height="4" rx="1" {common}/><rect x="{x + 1}" y="{y + 14}" width="14" height="2" rx="1" fill="#ffffff"/>'
    return f'<g class="c4-pictogram {kind}">{geometry}</g>'


def _embed_icons(svg: str, model: C4Model) -> str:
    """Add self-contained local pictograms after Graphviz has laid out each node."""
    elements = {item.id: item for item in model.all_elements()}
    pattern = re.compile(
        r'(?P<head><g id="node\d+" class="node">\s*<title>(?P<id>[^<]+)</title>\s*<path[^>]+/>\s*)'
        r'(?P<text><text[^>]* x="(?P<x>-?[\d.]+)" y="(?P<y>-?[\d.]+)"[^>]*>)'
    )

    def add_icon(match: re.Match[str]) -> str:
        item = elements.get(html.unescape(match.group("id")).replace("-", "-"))
        if item is None:
            return match.group(0)
        x = float(match.group("x")) - 21
        y = float(match.group("y")) - 15
        return f'{match.group("head")}{_pictogram(_icon_kind(item), x, y)}{match.group("text")}'

    return pattern.sub(add_icon, svg)


def _label(item: Element) -> str:
    proposed = "<BR/><FONT POINT-SIZE=\"9\">PROPOSED</FONT>" if item.provenance.value == "proposed_assumption" else ""
    external = "<BR/><FONT POINT-SIZE=\"9\">EXTERNAL</FONT>" if item.external else ""
    technology = f"<BR/><FONT POINT-SIZE=\"10\">{escape(item.technology)}</FONT>" if item.technology else ""
    return (
        "<<TABLE BORDER=\"0\" CELLBORDER=\"0\" CELLSPACING=\"0\" CELLPADDING=\"2\">"
        "<TR><TD FIXEDSIZE=\"TRUE\" WIDTH=\"22\" HEIGHT=\"22\"></TD>"
        f"<TD ALIGN=\"LEFT\"><B>{escape(item.name)}</B>{external}{proposed}<BR/>"
        f"<FONT POINT-SIZE=\"10\">{_lines(item.description)}</FONT>{technology}</TD></TR></TABLE>>"
    )


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
        return _embed_icons(Source(dot, format="svg").pipe().decode(), model).encode()
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
                f'<rect x="80" y="{y}" width="360" height="80" rx="10" fill="{color}"/>'
                f'{_pictogram(_icon_kind(item), 96, y + 27)}'
                f'<text x="156" y="{y + 30}" fill="white" font-family="Arial" font-size="18">{escape(item.name)}</text>'
                f'<text x="156" y="{y + 57}" fill="white" font-family="Arial" font-size="13">{escape(item.description)}</text>'
            )
        title = f"{escape(model.system_name)} — {'System Context' if view == 'context' else 'Container'}"
        return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"><rect width="100%" height="100%" fill="white"/><text x="40" y="28" font-family="Arial" font-size="20" font-weight="bold">{title}</text>{"".join(blocks)}</svg>'.encode()
