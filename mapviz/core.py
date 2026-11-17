"""Glowing US heat-map renderer (numpy + Pillow only, runs on GitHub runners).

Data: US Census Bureau (public domain US Government works):
  - cb_2023_us_state_20m (cartographic boundary states)
  - CenPop2020_Mean_TR (2020 Census tract population + centre of population)
"""
from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path

import numpy as np
import shapefile
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
CENSUS = ROOT / "data" / "census"
FONT = ROOT / "assets" / "fonts" / "Anton-Regular.ttf"

LOWER48_SKIP = {"AK", "HI", "PR"}

# ---------- projection: Albers equal-area conic (USGS standard for CONUS) ----------
_P1, _P2, _P0, _L0 = map(math.radians, (29.5, 45.5, 37.5, -96.0))
_N = (math.sin(_P1) + math.sin(_P2)) / 2
_C = math.cos(_P1) ** 2 + 2 * _N * math.sin(_P1)
_R0 = math.sqrt(_C - 2 * _N * math.sin(_P0)) / _N


def albers(lon, lat):
    lon = np.radians(np.asarray(lon, float))
    lat = np.radians(np.asarray(lat, float))
    rho = np.sqrt(_C - 2 * _N * np.sin(lat)) / _N
    th = _N * (lon - _L0)
    return rho * np.sin(th), _R0 - rho * np.cos(th)


# ---------- data ----------
@lru_cache(None)
def states():
    """{abbr: [ring arrays of (x, y) albers]} for the lower 48 + DC."""
    r = shapefile.Reader(str(CENSUS / "states" / "cb_2023_us_state_20m"))
    out = {}
    for sr in r.iterShapeRecords():
        ab = sr.record["STUSPS"]
        if ab in LOWER48_SKIP:
            continue
        pts = np.array(sr.shape.points)
        parts = list(sr.shape.parts) + [len(pts)]
        rings = []
        for a, b in zip(parts[:-1], parts[1:]):
            x, y = albers(pts[a:b, 0], pts[a:b, 1])
            rings.append(np.column_stack([x, y]))
        out[ab] = rings
    return out


@lru_cache(None)
def tracts2020():
    """(x, y, population) arrays for lower-48 tracts, 2020 Census."""
    import csv

    skip_fp = {"02", "15", "72"}
    xs, ys, ps = [], [], []
    with open(CENSUS / "CenPop2020_Mean_TR.txt", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row["STATEFP"] in skip_fp:
                continue
            xs.append(float(row["LONGITUDE"]))
            ys.append(float(row["LATITUDE"]))
            ps.append(int(row["POPULATION"]))
    x, y = albers(xs, ys)
    return x, y, np.array(ps, float)


# ---------- view: albers -> pixels ----------
class View:
    def __init__(self, w, h, cx=0.5, cy=0.5, fill=0.92, center=None):
        """Fit the lower-48 bbox into fill*frame, placed at (cx, cy) fractions."""
        allp = np.vstack([r for rings in states().values() for r in rings])
        x0, y0 = allp.min(0)
        x1, y1 = allp.max(0)
        self.s = min(w * fill / (x1 - x0), h * fill / (y1 - y0))
        mx, my = ((x0 + x1) / 2, (y0 + y1) / 2) if center is None else albers(*center)
        self.ox = w * cx - mx * self.s
        self.oy = h * cy + my * self.s
        self.w, self.h = w, h

    def px(self, x, y):
        return self.ox + np.asarray(x) * self.s, self.oy - np.asarray(y) * self.s


# ---------- image helpers ----------
def box_blur(a, r):
    if r < 1:
        return a
    for axis in (0, 1):
        c = np.cumsum(np.pad(a, [(r + 1, r) if i == axis else (0, 0) for i in range(2)]), axis=axis)
        sl_hi = [slice(None)] * 2
        sl_lo = [slice(None)] * 2
        sl_hi[axis] = slice(2 * r + 1, None)
        sl_lo[axis] = slice(None, -(2 * r + 1))
        a = (c[tuple(sl_hi)] - c[tuple(sl_lo)]) / (2 * r + 1)
    return a


def gauss(a, sigma):
    r = max(1, int(round(sigma * 0.85)))
    for _ in range(3):
        a = box_blur(a, r)
    return a


PALETTES = {
    # black/navy -> teal -> red -> orange -> yellow -> white  (heat-map look)
    "fire": [(0.00, (8, 14, 40)), (0.18, (0, 120, 150)), (0.34, (0, 215, 200)),
             (0.50, (230, 30, 60)), (0.68, (255, 110, 0)), (0.84, (255, 210, 0)),
             (1.00, (255, 255, 230))],
    "ice": [(0.00, (6, 10, 40)), (0.25, (10, 40, 170)), (0.45, (0, 170, 255)),
            (0.60, (0, 255, 190)), (0.80, (255, 235, 0)), (1.00, (255, 255, 255))],
    "magma": [(0.00, (10, 4, 30)), (0.22, (120, 0, 140)), (0.42, (235, 0, 90)),
              (0.62, (255, 90, 0)), (0.82, (255, 200, 0)), (1.00, (255, 255, 220))],
}


def colormap(v, name="fire"):
    stops = PALETTES[name]
    xs = np.array([s[0] for s in stops])
    out = np.zeros(v.shape + (3,))
    for c in range(3):
        out[..., c] = np.interp(v, xs, [s[1][c] for s in stops])
    return out


def background(w, h, inner=(10, 22, 70), outer=(0, 0, 8), cx=0.5, cy=0.45):
    yy, xx = np.mgrid[0:h, 0:w]
    d = np.sqrt(((xx / w - cx) * 1.6) ** 2 + ((yy / h - cy) * 1.0) ** 2)
    t = np.clip(d / 0.9, 0, 1)[..., None] ** 1.3
    return np.array(inner) * (1 - t) + np.array(outer) * t


def land_mask(view, ss=1):
    img = Image.new("L", (view.w * ss, view.h * ss), 0)
    d = ImageDraw.Draw(img)
    for rings in states().values():
        for r in rings:
            x, y = view.px(r[:, 0], r[:, 1])
            d.polygon(list(zip(x * ss, y * ss)), fill=255)
    if ss > 1:
        img = img.resize((view.w, view.h), Image.LANCZOS)
    return np.asarray(img, float) / 255


def borders(view, width=1, ss=2):
    img = Image.new("L", (view.w * ss, view.h * ss), 0)
    d = ImageDraw.Draw(img)
    for rings in states().values():
        for r in rings:
            x, y = view.px(r[:, 0], r[:, 1])
            pts = list(zip(x * ss, y * ss))
            d.line(pts + pts[:1], fill=255, width=max(1, int(width * ss)))
    return np.asarray(img.resize((view.w, view.h), Image.LANCZOS), float) / 255


def outline(view, width=3, ss=2):
    """Outer coastline/border of the lower 48 (edge of the land mask)."""
    m = land_mask(view, ss=2)
    e = gauss(m, width * 0.6)
    edge = np.clip(1 - np.abs(e - 0.5) * 2 / 0.5, 0, 1) * (m > 0.02)
    return edge


@lru_cache(None)
def _ref_scale():
    return View(1920, 1080).s


def heat(view, palette="fire", gain=1.0, weights=None):
    """Glowing population heat-map layer, returns (rgb float 0..255, alpha 0..1)."""
    x, y, p = tracts2020()
    if weights is not None:
        p = p * weights(x, y)
    px, py = view.px(x, y)
    grid = np.zeros((view.h, view.w))
    ok = (px >= 0) & (px < view.w) & (py >= 0) & (py < view.h)
    np.add.at(grid, (py[ok].astype(int), px[ok].astype(int)), p[ok])
    k = view.s / _ref_scale()
    dens = gauss(grid, 1.0 * k) + gauss(grid, 3.5 * k) * 0.6 + gauss(grid, 12 * k) * 0.25
    dens = dens / (k * k)  # people per 1920-frame pixel
    v = (np.log10(dens * gain + 1e-9) - 0.9) / (4.6 - 0.9)
    v = np.clip(v, 0, 1)
    rgb = colormap(v, palette)
    return rgb, np.clip(v * 2.5, 0, 1)


def bloom(rgb, sigma, amount):
    b = np.stack([gauss(rgb[..., c], sigma) for c in range(3)], -1)
    return rgb + b * amount


def compose_map(w, h, palette="fire", view=None, border_rgb=(0, 230, 255), border_alpha=0.35,
                outline_rgb=(0, 255, 240), outline_alpha=0.9, land_rgb=(14, 30, 80), gain=1.0,
                bg=None, weights=None):
    view = view or View(w, h)
    img = background(w, h) if bg is None else bg
    m = land_mask(view, ss=2)[..., None]
    img = img * (1 - m * 0.85) + np.array(land_rgb) * m * 0.85
    hr, ha = heat(view, palette, gain, weights)
    img = img * (1 - ha[..., None]) + hr * ha[..., None]
    b = borders(view, width=max(1, w / 1400))[..., None]
    img = img * (1 - b * border_alpha) + np.array(border_rgb) * b * border_alpha
    o = outline(view, width=max(2, w / 700))[..., None]
    glow_o = gauss(o[..., 0], w / 300)[..., None]
    img = img + np.array(outline_rgb) * glow_o * 0.6 * outline_alpha
    img = img * (1 - o * outline_alpha) + np.array(outline_rgb) * o * outline_alpha
    img = bloom(img, w / 120, 0.35)
    return np.clip(img, 0, 255), view


def to_image(a):
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")


# ---------- text / graphics ----------
def font(size):
    return ImageFont.truetype(str(FONT), size)


def text(img, xy, s, size, fill=(255, 230, 0), stroke=None, anchor="la", stroke_fill=(0, 0, 0),
         shadow=True):
    d = ImageDraw.Draw(img)
    f = font(size)
    stroke = stroke if stroke is not None else max(4, size // 11)
    if shadow:
        sh = Image.new("L", img.size, 0)
        ImageDraw.Draw(sh).text((xy[0] + size // 18, xy[1] + size // 14), s, font=f, fill=200,
                                anchor=anchor, stroke_width=stroke, stroke_fill=200)
        sh = sh.filter(ImageFilter.GaussianBlur(size / 14))
        img.paste((0, 0, 0), mask=sh)
    d.text(xy, s, font=f, fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=stroke_fill)
    return d.textbbox(xy, s, font=f, anchor=anchor, stroke_width=stroke)


def glow_line(img, pts, width, color, glow=True, head=None, outline_px=None):
    """Thick bright polyline with black outline, outer glow and optional arrow head."""
    w, h = img.size
    outline_px = outline_px if outline_px is not None else max(3, width // 3)
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    polys = []
    if head:
        (x0, y0), (x1, y1) = pts[-2], pts[-1]
        ang = math.atan2(y1 - y0, x1 - x0)
        L, W = head, head * 0.75
        bx, by = x1 - L * math.cos(ang), y1 - L * math.sin(ang)
        tri = [(x1, y1), (bx + W * math.sin(ang), by - W * math.cos(ang)),
               (bx - W * math.sin(ang), by + W * math.cos(ang))]
        polys.append(tri)
        pts = pts[:-1] + [(bx + 0.3 * L * math.cos(ang), by + 0.3 * L * math.sin(ang))]
    if glow:
        g = Image.new("RGBA", img.size, (0, 0, 0, 0))
        gd = ImageDraw.Draw(g)
        gd.line(pts, fill=color + (255,), width=width * 3, joint="curve")
        for p in polys:
            gd.polygon(p, fill=color + (255,))
        g = g.filter(ImageFilter.GaussianBlur(width * 1.2))
        img.paste(Image.alpha_composite(img.convert("RGBA"), g).convert("RGB"))
    d.line(pts, fill=(0, 0, 0, 255), width=width + 2 * outline_px, joint="curve")
    for p in polys:
        d.polygon(p, fill=(0, 0, 0, 255), outline=(0, 0, 0, 255), width=outline_px * 2)
    d.line(pts, fill=color + (255,), width=width, joint="curve")
    for p in polys:
        d.polygon(p, fill=color + (255,))
    img.paste(Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB"))


def bezier(p0, p1, p2, n=40):
    t = np.linspace(0, 1, n)[:, None]
    p0, p1, p2 = map(np.array, (p0, p1, p2))
    pts = (1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t ** 2 * p2
    return [tuple(p) for p in pts]
