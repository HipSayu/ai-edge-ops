"""Renders every .drawio file here to PNG (one image per page) with local headless Chrome. No network.

Usage: python export_images.py <diagrams_dir> <images_dir>

Reads the .drawio XML itself, so edits made in draw.io are exported too. It draws the subset of draw.io
used by these diagrams (rectangles, ellipses, diamonds, actors, swimlane tables, notes, cylinders and
straight / orthogonal / ER edges); it is not a general draw.io renderer.
"""

import html
import math
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
SCALE = 2
PAD = 30
FONT = "'Segoe UI', Arial, sans-serif"


def parse_style(text: str) -> dict[str, str]:
    style: dict[str, str] = {}
    for part in (text or "").split(";"):
        if not part:
            continue
        key, _, value = part.partition("=")
        style[key] = value if _ else "1"
    return style


class Cell:
    def __init__(self, el: ET.Element) -> None:
        self.id = el.get("id")
        self.value = el.get("value") or ""
        self.style = parse_style(el.get("style", ""))
        self.edge = el.get("edge") == "1"
        self.vertex = el.get("vertex") == "1"
        self.parent = el.get("parent")
        self.source, self.target = el.get("source"), el.get("target")
        self.x = self.y = self.w = self.h = 0.0
        self.points: list[tuple[float, float]] = []
        self.sp = self.tp = None
        geo = el.find("mxGeometry")
        if geo is None:
            return
        if self.vertex:
            self.x, self.y = float(geo.get("x", 0)), float(geo.get("y", 0))
            self.w, self.h = float(geo.get("width", 0)), float(geo.get("height", 0))
        for pt in geo.findall("mxPoint"):
            xy = (float(pt.get("x", 0)), float(pt.get("y", 0)))
            if pt.get("as") == "sourcePoint":
                self.sp = xy
            elif pt.get("as") == "targetPoint":
                self.tp = xy
        for pt in geo.findall("./Array/mxPoint"):
            self.points.append((float(pt.get("x", 0)), float(pt.get("y", 0))))


# ------------------------------------------------------------------ geometry
def center(c: Cell) -> tuple[float, float]:
    return c.x + c.w / 2, c.y + c.h / 2


def side_point(c: Cell, side: str) -> tuple[float, float]:
    cx, cy = center(c)
    return {"r": (c.x + c.w, cy), "l": (c.x, cy), "t": (cx, c.y), "b": (cx, c.y + c.h)}[side]


def side_toward(c: Cell, target: tuple[float, float]) -> str:
    cx, cy = center(c)
    dx, dy = target[0] - cx, target[1] - cy
    if abs(dx) / max(c.w / 2, 1) > abs(dy) / max(c.h / 2, 1):
        return "r" if dx > 0 else "l"
    return "b" if dy > 0 else "t"


def boundary(c: Cell, target: tuple[float, float]) -> tuple[float, float]:
    cx, cy = center(c)
    dx, dy = target[0] - cx, target[1] - cy
    if dx == dy == 0:
        return cx, cy
    hw, hh = max(c.w / 2, 1), max(c.h / 2, 1)
    if "ellipse" in c.style:
        t = 1 / math.hypot(dx / hw, dy / hh)
    elif "rhombus" in c.style:
        t = 1 / (abs(dx) / hw + abs(dy) / hh)
    else:
        t = 1 / max(abs(dx) / hw, abs(dy) / hh)
    return cx + dx * t, cy + dy * t


def orthogonal_path(src: Cell, dst: Cell, waypoints: list[tuple[float, float]]) -> list[tuple[float, float]]:
    s_side = side_toward(src, waypoints[0] if waypoints else center(dst))
    d_side = side_toward(dst, waypoints[-1] if waypoints else center(src))
    a, b = side_point(src, s_side), side_point(dst, d_side)
    s_h, d_h = s_side in "lr", d_side in "lr"

    if not waypoints:
        if s_h and d_h:
            mx = (a[0] + b[0]) / 2
            return [a, (mx, a[1]), (mx, b[1]), b]
        if not s_h and not d_h:
            my = (a[1] + b[1]) / 2
            return [a, (a[0], my), (b[0], my), b]
        return [a, (b[0], a[1]), b] if s_h else [a, (a[0], b[1]), b]

    path = [a]
    heading_h = s_h
    chain = [*waypoints, b]
    for i, q in enumerate(chain):
        p = path[-1]
        last = i == len(chain) - 1
        if p[0] != q[0] and p[1] != q[1]:
            horizontal_first = (not d_h) if last else heading_h
            path.append((q[0], p[1]) if horizontal_first else (p[0], q[1]))
        path.append(q)
        heading_h = path[-1][1] == path[-2][1]
    return dedupe(path)


def dedupe(points):
    out = [points[0]]
    for p in points[1:]:
        if p != out[-1]:
            out.append(p)
    return out


def path_midpoint(points):
    total = sum(math.dist(points[i], points[i + 1]) for i in range(len(points) - 1))
    run = 0.0
    for i in range(len(points) - 1):
        seg = math.dist(points[i], points[i + 1])
        if run + seg >= total / 2:
            t = (total / 2 - run) / seg if seg else 0
            return points[i][0] + (points[i + 1][0] - points[i][0]) * t, points[i][1] + (points[i + 1][1] - points[i][1]) * t
        run += seg
    return points[0]


# ------------------------------------------------------------------ svg pieces
def label_html(value: str) -> str:
    return html.escape(value).replace("&lt;br&gt;", "<br>")


def label_box(c: Cell, x, y, w, h, extra_style="") -> str:
    st = c.style
    if not c.value:
        return ""
    fs = float(st.get("fontSize", 12))
    font_style = int(st.get("fontStyle", 0))
    weight = "bold" if font_style & 1 else "normal"
    italic = "italic" if font_style & 2 else "normal"
    align = st.get("align", "center")
    valign = st.get("verticalAlign", "middle")
    hmap = {"left": "flex-start", "center": "center", "right": "flex-end"}[align]
    vmap = {"top": "flex-start", "middle": "center", "bottom": "flex-end"}[valign]
    wrap = "normal" if st.get("whiteSpace") == "wrap" else "nowrap"
    pad_left = float(st.get("spacingLeft", 0)) + 4
    color = st.get("fontColor", "#1a1a1a")
    return (
        f'<foreignObject x="{x}" y="{y}" width="{w}" height="{h}" style="overflow:visible">'
        f'<div xmlns="http://www.w3.org/1999/xhtml" style="width:{w}px;height:{h}px;box-sizing:border-box;display:flex;'
        f'flex-direction:column;justify-content:{vmap};align-items:{hmap};padding:2px 4px 2px {pad_left}px;'
        f'font:{italic} {weight} {fs}px/1.25 {FONT};color:{color};text-align:{align};white-space:{wrap};{extra_style}">'
        f"<div>{label_html(c.value)}</div></div></foreignObject>"
    )


def paint(st: dict[str, str]) -> str:
    fill = st.get("fillColor", "#ffffff")
    stroke = st.get("strokeColor", "#000000")
    dash = ' stroke-dasharray="6 4"' if st.get("dashed") == "1" else ""
    return f'fill="{"none" if fill == "none" else fill}" stroke="{"none" if stroke == "none" else stroke}" stroke-width="1.2"{dash}'


def render_vertex(c: Cell) -> str:
    st, x, y, w, h = c.style, c.x, c.y, c.w, c.h
    shape = st.get("shape", "")
    out = []
    if "text" in st and "ellipse" not in st:
        fill = st.get("fillColor", "none")
        background = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"/>' if fill != "none" else ""
        return background + label_box(c, x, y, w, h)
    if "swimlane" in st:
        head = float(st.get("startSize", 23))
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#ffffff" stroke="{st.get("strokeColor", "#000")}" '
                   f'stroke-width="1.2"{" stroke-dasharray=\"6 4\"" if st.get("dashed") == "1" else ""}/>')
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{head}" fill="{st.get("fillColor", "#fff")}" '
                   f'stroke="{st.get("strokeColor", "#000")}" stroke-width="1.2"/>')
        head_cell = Cell(ET.Element("mxCell", {"value": c.value, "style": "fontStyle=1;fontSize=13;"}))
        out.append(label_box(head_cell, x, y, w, head))
        return "".join(out)
    if shape == "umlActor":
        cx = x + w / 2
        out.append(f'<g stroke="#000" stroke-width="1.5" fill="#fff"><circle cx="{cx}" cy="{y + h * 0.14}" r="{h * 0.14}"/>'
                   f'<line x1="{cx}" y1="{y + h * 0.28}" x2="{cx}" y2="{y + h * 0.62}"/>'
                   f'<line x1="{x}" y1="{y + h * 0.4}" x2="{x + w}" y2="{y + h * 0.4}"/>'
                   f'<line x1="{cx}" y1="{y + h * 0.62}" x2="{x}" y2="{y + h}"/>'
                   f'<line x1="{cx}" y1="{y + h * 0.62}" x2="{x + w}" y2="{y + h}"/></g>')
        out.append(label_box(c, cx - 90, y + h + 2, 180, 40, "text-align:center;") .replace("justify-content:center", "justify-content:flex-start"))
        return "".join(out)
    if shape == "cylinder3":
        ry = 12
        out.append(f'<path d="M{x},{y + ry} L{x},{y + h - ry} A{w / 2},{ry} 0 0 0 {x + w},{y + h - ry} L{x + w},{y + ry} '
                   f'A{w / 2},{ry} 0 0 0 {x},{y + ry} Z" {paint(st)}/>')
        out.append(f'<path d="M{x},{y + ry} A{w / 2},{ry} 0 0 0 {x + w},{y + ry}" fill="none" stroke="{st.get("strokeColor", "#000")}" stroke-width="1.2"/>')
    elif shape == "note":
        s = float(st.get("size", 10))
        out.append(f'<polygon points="{x},{y} {x + w - s},{y} {x + w},{y + s} {x + w},{y + h} {x},{y + h}" {paint(st)}/>')
        out.append(f'<polyline points="{x + w - s},{y} {x + w - s},{y + s} {x + w},{y + s}" fill="none" stroke="{st.get("strokeColor", "#000")}" stroke-width="1"/>')
    elif "ellipse" in st:
        out.append(f'<ellipse cx="{x + w / 2}" cy="{y + h / 2}" rx="{w / 2}" ry="{h / 2}" {paint(st)}/>')
    elif "rhombus" in st:
        out.append(f'<polygon points="{x + w / 2},{y} {x + w},{y + h / 2} {x + w / 2},{y + h} {x},{y + h / 2}" {paint(st)}/>')
    else:
        rx = min(10, min(w, h) / 4) if st.get("rounded") == "1" else 0
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" {paint(st)}/>')
    out.append(label_box(c, x, y, w, h))
    return "".join(out)


def arrow_head(kind: str, tip, direction, fill: bool, color: str) -> str:
    ux, uy = direction
    nx, ny = -uy, ux
    tx, ty = tip
    if kind == "block":
        bx, by = tx - ux * 11, ty - uy * 11
        pts = f"{tx},{ty} {bx + nx * 5.5},{by + ny * 5.5} {bx - nx * 5.5},{by - ny * 5.5}"
        return f'<polygon points="{pts}" fill="{color if fill else "#fff"}" stroke="{color}" stroke-width="1.2"/>'
    if kind == "open":
        parts = []
        for sign in (1, -1):
            ex, ey = tx - ux * 11 + nx * 6 * sign, ty - uy * 11 + ny * 6 * sign
            parts.append(f'<line x1="{tx}" y1="{ty}" x2="{ex}" y2="{ey}"/>')
        return f'<g stroke="{color}" stroke-width="1.3">{"".join(parts)}</g>'
    if kind == "ERmany":
        bx, by = tx - ux * 13, ty - uy * 13
        lines = "".join(f'<line x1="{bx}" y1="{by}" x2="{tx + nx * o}" y2="{ty + ny * o}"/>' for o in (-7, 0, 7))
        return f'<g stroke="{color}" stroke-width="1.3">{lines}</g>'
    if kind == "ERmandOne":
        bars = ""
        for d in (9, 15):
            cx, cy = tx - ux * d, ty - uy * d  # back along the line, outside the entity
            bars += f'<line x1="{cx + nx * 7}" y1="{cy + ny * 7}" x2="{cx - nx * 7}" y2="{cy - ny * 7}"/>'
        return f'<g stroke="{color}" stroke-width="1.3">{bars}</g>'
    return ""


def unit(a, b):
    d = math.dist(a, b) or 1
    return (b[0] - a[0]) / d, (b[1] - a[1]) / d


def render_edge(c: Cell, cells: dict[str, Cell]) -> tuple[str, list[tuple[float, float]]]:
    st = c.style
    if c.source and c.target and c.source in cells and c.target in cells:
        src, dst = cells[c.source], cells[c.target]
        if "edgeStyle" in st:
            pts = orthogonal_path(src, dst, c.points)
        else:
            first = c.points[0] if c.points else center(dst)
            last = c.points[-1] if c.points else center(src)
            pts = dedupe([boundary(src, first), *c.points, boundary(dst, last)])
    else:
        pts = dedupe([c.sp or (0, 0), *c.points, c.tp or (0, 0)])
    if len(pts) < 2:
        return "", pts

    color = st.get("strokeColor", "#333333")
    dash = ' stroke-dasharray="6 4"' if st.get("dashed") == "1" else ""
    d = "M" + " L".join(f"{x},{y}" for x, y in pts)
    out = [f'<path d="{d}" fill="none" stroke="{color}" stroke-width="1.3" stroke-linejoin="round"{dash}/>']

    end, start = st.get("endArrow", "classic"), st.get("startArrow", "none")
    end = "block" if end == "classic" else end
    if end not in ("none", ""):
        out.append(arrow_head(end, pts[-1], unit(pts[-2], pts[-1]), st.get("endFill", "1") == "1", color))
    if start not in ("none", ""):
        out.append(arrow_head(start, pts[0], unit(pts[1], pts[0]), st.get("startFill", "1") == "1", color))

    if c.value:
        mx, my = path_midpoint(pts)
        fs = float(st.get("fontSize", 11))
        text = c.value.replace("<br>", " ")
        bw = len(text) * fs * 0.58 + 10
        out.append(f'<rect x="{mx - bw / 2}" y="{my - fs * 0.85}" width="{bw}" height="{fs * 1.5}" rx="3" fill="#ffffff" fill-opacity="0.92"/>')
        out.append(f'<text x="{mx}" y="{my + fs * 0.35}" text-anchor="middle" font-family="{FONT}" font-size="{fs}" fill="#1a1a1a">{html.escape(text)}</text>')
    return "".join(out), pts


# ------------------------------------------------------------------ page → html
def render_page(diagram: ET.Element) -> tuple[str, int, int]:
    cells: dict[str, Cell] = {}
    order: list[Cell] = []
    for el in diagram.iter("mxCell"):
        c = Cell(el)
        cells[c.id] = c
        order.append(c)
    for c in order:  # children use coordinates relative to their parent container
        if c.vertex and c.parent in cells and c.parent not in ("0", "1"):
            c.x += cells[c.parent].x
            c.y += cells[c.parent].y

    body = []
    xs, ys = [], []
    for c in order:
        if c.vertex:
            body.append(render_vertex(c))
            xs += [c.x, c.x + c.w]
            ys += [c.y, c.y + c.h + (44 if c.style.get("shape") == "umlActor" else 0)]
            if c.style.get("shape") == "umlActor":
                xs += [c.x - 60, c.x + c.w + 60]
        elif c.edge:
            svg, pts = render_edge(c, cells)
            body.append(svg)
            xs += [p[0] for p in pts]
            ys += [p[1] for p in pts]

    min_x, min_y = min(xs) - PAD, min(ys) - PAD
    width, height = int(max(xs) - min_x + PAD), int(max(ys) - min_y + PAD)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="{min_x} {min_y} {width} {height}">'
           f'<rect x="{min_x}" y="{min_y}" width="{width}" height="{height}" fill="#ffffff"/>{"".join(body)}</svg>')
    return svg, width, height


def export(drawio: Path, images: Path) -> list[Path]:
    pages = ET.parse(drawio).getroot().findall("diagram")
    written = []
    for index, page in enumerate(pages, 1):
        svg, w, h = render_page(page)
        name = drawio.stem if len(pages) == 1 else f"{drawio.stem}-{index}"
        target = (images / f"{name}.png").resolve()  # Chrome resolves relative paths against its own directory
        with tempfile.TemporaryDirectory() as tmp:
            page_html = Path(tmp) / "page.html"
            page_html.write_text(f'<!doctype html><meta charset="utf-8"><style>html,body{{margin:0;background:#fff}}</style>{svg}', encoding="utf-8")
            subprocess.run(
                [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--force-device-scale-factor={SCALE}",
                 f"--window-size={w},{h + 20}", f"--screenshot={target}", page_html.as_uri()],
                check=True, capture_output=True, timeout=120,
            )
        written.append(target)
        print("wrote", target.name, f"({w}x{h})")
    return written


if __name__ == "__main__":
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    dst.mkdir(parents=True, exist_ok=True)
    for file in sorted(src.glob("*.drawio")):
        export(file, dst)
