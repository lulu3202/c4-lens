from __future__ import annotations

from html import escape
from textwrap import wrap
from xml.etree import ElementTree as ET

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


def _lines(text: str, limit: int = 26, maximum: int = 3) -> str:
    lines = wrap(text, width=limit)[:maximum]
    if len(text) > sum(len(line) for line in lines):
        lines[-1] = lines[-1].rstrip(".") + "…"
    return "<BR/>".join(escape(line) for line in lines)


def _icon_kind(item: Element) -> str:
    if item.external:
        return "external-system"
    return {"person": "person", "software_system": "software-system", "container": "container"}[item.type.value]


SVG_NAMESPACE = "http://www.w3.org/2000/svg"


def _svg_tag(name: str) -> str:
    return f"{{{SVG_NAMESPACE}}}{name}"


def _pictogram(kind: str, x: float, y: float) -> ET.Element:
    group = ET.Element(
        _svg_tag("g"),
        {
            "class": f"c4-pictogram {kind}",
            "transform": f"translate({x} {y}) scale(1.5) translate({-x} {-y})",
        },
    )
    common = {
        "fill": "none",
        "stroke": "#ffffff",
        "stroke-width": "2.5",
        "stroke-linecap": "round",
        "stroke-linejoin": "round",
    }

    def add(name: str, **attributes: str) -> None:
        group.append(ET.Element(_svg_tag(name), attributes))

    if kind == "person":
        add("circle", cx=str(x + 8), cy=str(y + 5), r="3", fill="#ffffff")
        add("path", d=f"M{x + 2} {y + 15}c1-4 3-6 6-6s5 2 6 6", **common)
    elif kind == "software-system":
        add("rect", x=str(x + 1), y=str(y + 2), width="14", height="10", rx="1.5", **common)
        add("path", d=f"M{x + 5} {y + 16}h6M{x + 8} {y + 12}v4", **common)
    elif kind == "external-system":
        add("rect", x=str(x + 1), y=str(y + 4), width="11", height="11", rx="1.5", **common)
        add("path", d=f"M{x + 9} {y + 2}h6v6M{x + 15} {y + 2} {x + 8} {y + 9}", **common)
    else:
        add("rect", x=str(x + 1), y=str(y + 2), width="14", height="4", rx="1", **common)
        add("rect", x=str(x + 1), y=str(y + 8), width="14", height="4", rx="1", **common)
        add("rect", x=str(x + 1), y=str(y + 14), width="14", height="2", rx="1", fill="#ffffff")
    return group


def _embed_icons(svg: str, model: C4Model) -> str:
    """Add native SVG pictograms into the Graphviz node groups."""
    ET.register_namespace("", SVG_NAMESPACE)
    root = ET.fromstring(svg)
    elements = {item.id: item for item in model.all_elements()}
    for node in root.iter(_svg_tag("g")):
        if "node" not in node.attrib.get("class", "").split():
            continue
        title = node.find(_svg_tag("title"))
        item = elements.get(title.text if title is not None else "")
        children = list(node)
        first_text_index = next(
            (index for index, child in enumerate(children) if child.tag == _svg_tag("text")),
            None,
        )
        text = (
            children[first_text_index]
            if first_text_index is not None
            else next((child for child in node.iter(_svg_tag("text")) if child.get("x") and child.get("y")), None)
        )
        if item is None or text is None:
            continue
        x, y = float(text.attrib["x"]) - 21, float(text.attrib["y"]) - 15
        pictogram = _pictogram(_icon_kind(item), x, y)
        if first_text_index is None:
            node.append(pictogram)
        else:
            node.insert(first_text_index, pictogram)
    return ET.tostring(root, encoding="unicode")


def _label(item: Element) -> str:
    proposed = "<BR/><FONT POINT-SIZE=\"9\">PROPOSED</FONT>" if item.provenance.value == "proposed_assumption" else ""
    external = "<BR/><FONT POINT-SIZE=\"9\">EXTERNAL</FONT>" if item.external else ""
    technology = f"<BR/><FONT POINT-SIZE=\"10\">{escape(item.technology)}</FONT>" if item.technology else ""
    return (
        "<<TABLE BORDER=\"0\" CELLBORDER=\"0\" CELLSPACING=\"0\" CELLPADDING=\"2\">"
        "<TR><TD FIXEDSIZE=\"TRUE\" WIDTH=\"46\" HEIGHT=\"22\"></TD>"
        f"<TD ALIGN=\"LEFT\" WIDTH=\"180\"><B>{_lines(item.name, 24, 2)}</B>{external}{proposed}<BR/>"
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
        pad="0.18",
        nodesep="0.35",
        ranksep="0.5",
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
        margin="0.1",
        width="2.5",
        height="0.65",
    )
    if view == "container":
        with graph.subgraph(name="cluster_target_system") as cluster:
            cluster.attr(
                label=model.system_name,
                color="#167c80",
                penwidth="2",
                style="rounded",
                margin="14",
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
                label="\\n".join(wrap(rel.description, width=20)),
                fontname="Arial",
                fontsize="9",
                fontcolor="#334155",
                color="#64748b",
                penwidth="1.2",
                minlen="1",
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
            pictogram = ET.tostring(
                _pictogram(_icon_kind(item), 96, y + 27), encoding="unicode"
            )
            blocks.append(
                f'<rect x="80" y="{y}" width="360" height="80" rx="10" fill="{color}"/>'
                f"{pictogram}"
                f'<text x="156" y="{y + 30}" fill="white" font-family="Arial" font-size="18">{escape(item.name)}</text>'
                f'<text x="156" y="{y + 57}" fill="white" font-family="Arial" font-size="13">{escape(item.description)}</text>'
            )
        title = f"{escape(model.system_name)} — {'System Context' if view == 'context' else 'Container'}"
        return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"><rect width="100%" height="100%" fill="white"/><text x="40" y="28" font-family="Arial" font-size="20" font-weight="bold">{title}</text>{"".join(blocks)}</svg>'.encode()
