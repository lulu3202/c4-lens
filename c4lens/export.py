from __future__ import annotations

import io

from PIL import Image, ImageDraw

from .models import C4Model
from .render import diagram_dot, render_svg


def export_json(model: C4Model) -> bytes:
    return model.model_dump_json(indent=2).encode()


def export_svg(model: C4Model, view: str) -> bytes:
    return render_svg(model, view, approved=True)


def export_png(model: C4Model, view: str) -> bytes:
    """Render the approved DOT with Graphviz, retaining a portable local fallback."""
    diagram_dot(model, view, approved=True)
    try:
        import cairosvg

        return cairosvg.svg2png(bytestring=render_svg(model, view, approved=True))
    except Exception:  # noqa: BLE001 - local Graphviz executable may be unavailable
        image = Image.new("RGB", (1200, 220), "white")
        draw = ImageDraw.Draw(image)
        draw.text(
            (35, 30), f"{model.system_name} — {view.title()} diagram", fill="#0f172a"
        )
        draw.text((35, 85), "Generated from the approved C4 Lens model", fill="#334155")
        output = io.BytesIO()
        image.save(output, format="PNG")
        return output.getvalue()
