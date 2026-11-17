"""Channel branding drafts: 3 thumbnails, 3 banners, 3 avatars + phone-size check sheet.

python scripts/branding.py  -> out/branding/*.png
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from mapviz.core import (View, albers, compose_map, bezier, glow_line, text, to_image,  # noqa: E402
                         font)

OUT = Path(__file__).resolve().parent.parent / "out" / "branding"
OUT.mkdir(parents=True, exist_ok=True)
YEL, WHITE, CYAN, PINK = (255, 225, 0), (255, 255, 255), (0, 240, 255), (255, 40, 120)


def lonlat_px(view, lon, lat):
    x, y = albers(lon, lat)
    px, py = view.px(x, y)
    return float(px), float(py)


# ---------------- thumbnails 1280x720 ----------------
def thumb_a():
    W, H = 1280, 720
    a, v = compose_map(W, H, "fire", view=View(W, H, cx=0.47, cy=0.60, fill=0.86), gain=1.6)
    img = to_image(a)
    ny = lonlat_px(v, -74.0, 40.7)
    la = lonlat_px(v, -118.2, 34.0)
    pts = bezier((ny[0] - 20, ny[1] + 5), ((ny[0] + la[0]) / 2, ny[1] - 170), (la[0] + 30, la[1] - 25))
    glow_line(img, pts, 22, CYAN, head=70)
    text(img, (W // 2, 6), "AMERICA LIGHTS UP", 140, fill=WHITE, anchor="ma")
    text(img, (W - 30, H - 14), "1790 → 2020", 150, fill=YEL, anchor="rd")
    return img


def thumb_b():
    W, H = 1280, 720
    a, v = compose_map(W, H, "ice", view=View(W, H, cx=0.56, cy=0.55, fill=1.0), gain=0.6,
                       outline_rgb=(255, 230, 0), border_rgb=(120, 200, 255))
    img = to_image(a)
    # bright ring around the Boston-Washington corridor
    c = lonlat_px(v, -75.2, 40.2)
    d = ImageDraw.Draw(img)
    for wdt, col in ((26, (0, 0, 0)), (14, PINK)):
        d.ellipse([c[0] - 95, c[1] - 120, c[0] + 95, c[1] + 120], outline=col, width=wdt)
    text(img, (34, 30), "1790", 190, fill=WHITE)
    text(img, (34, 240), "→ 2020", 190, fill=YEL)
    text(img, (34, H - 24), "WHERE AMERICA LIVES", 108, fill=WHITE, anchor="ld")
    return img


def thumb_c():
    W, H = 1280, 720
    a, v = compose_map(W, H, "magma", view=View(W, H, cx=0.5, cy=0.63, fill=0.80),
                       outline_rgb=(0, 255, 200), border_rgb=(255, 120, 200))
    img = to_image(a)
    text(img, (W // 2, 8), "1790 → 2020", 200, fill=YEL, anchor="ma")
    text(img, (W // 2, H - 14), "EAST TO WEST", 120, fill=WHITE, anchor="md")
    e = lonlat_px(v, -76.5, 38.5)
    w = lonlat_px(v, -121.5, 38.5)
    glow_line(img, [(e[0], e[1] + 20), (w[0] + 70, w[1] + 20)], 26, (0, 255, 120), head=80)
    return img


# ---------------- banners 2560x1440 (safe 1546x423 centred) ----------------
SAFE = (507, 508, 2053, 931)


def banner(name, tagline, palette, layout):
    W, H = 2560, 1440
    if layout == "center":
        view = View(W, H, cx=0.5, cy=0.5, fill=0.62)
    elif layout == "right":
        view = View(W, H, cx=0.66, cy=0.5, fill=0.52)
    else:
        view = View(W, H, cx=0.5, cy=0.52, fill=0.80)
    a, v = compose_map(W, H, palette, view=view, gain=(1.3 if palette == "magma" else 3.5))
    img = to_image(a)
    if layout == "center":
        # dark band so the name stays readable over the bright map
        band = Image.new("L", (W, H), 0)
        ImageDraw.Draw(band).rectangle([0, 600, W, 840], fill=150)
        from PIL import ImageFilter
        img.paste((0, 0, 10), mask=band.filter(ImageFilter.GaussianBlur(40)))
        text(img, (W // 2, 700), name.upper(), 190, fill=YEL, anchor="mm")
        text(img, (W // 2, 860), tagline, 64, fill=WHITE, anchor="mm")
    elif layout == "right":
        text(img, (SAFE[0] + 10, 640), name.upper(), 170, fill=YEL, anchor="lm")
        text(img, (SAFE[0] + 14, 820), tagline, 60, fill=WHITE, anchor="lm")
    else:
        text(img, (W // 2, 640), name.upper(), 200, fill=WHITE, anchor="mm",
             stroke_fill=(0, 0, 0))
        text(img, (W // 2, 830), tagline, 66, fill=YEL, anchor="mm")
    return img


# ---------------- avatars 800x800 ----------------
def circle_mask(img):
    m = Image.new("L", img.size, 0)
    ImageDraw.Draw(m).ellipse([0, 0, img.size[0] - 1, img.size[1] - 1], fill=255)
    bg = Image.new("RGB", img.size, (0, 0, 0))
    bg.paste(img, mask=m)
    return bg


def avatar_a():
    S = 800
    a, _ = compose_map(S, S, "fire", view=View(S, S, fill=0.86), gain=0.8)
    return to_image(a)


def avatar_b(mono):
    S = 800
    a, _ = compose_map(S, S, "ice", view=View(S, S, fill=0.95))
    img = to_image(a)
    text(img, (S // 2, S // 2 + 10), mono, 330, fill=YEL, anchor="mm")
    return img


def avatar_c():
    S = 800
    a, v = compose_map(S, S, "magma", view=View(S, S, fill=0.86), gain=0.8,
                       outline_rgb=(0, 255, 220))
    img = to_image(a)
    e = lonlat_px(v, -77, 39.5)
    w = lonlat_px(v, -120.5, 39.5)
    glow_line(img, bezier(e, ((e[0] + w[0]) / 2, e[1] - 200), w), 30, (255, 240, 0), head=90)
    return img


def sheet(items, size, cols, path, label_h=26):
    w, h = size
    rows = (len(items) + cols - 1) // cols
    s = Image.new("RGB", (cols * (w + 20) + 20, rows * (h + 20 + label_h) + 20), (40, 40, 40))
    d = ImageDraw.Draw(s)
    for i, (lab, im) in enumerate(items):
        r, c = divmod(i, cols)
        x, y = 20 + c * (w + 20), 20 + r * (h + 20 + label_h)
        s.paste(im.resize((w, h), Image.LANCZOS), (x, y + label_h))
        d.text((x, y), lab, fill=(255, 255, 255), font=font(20))
    s.save(path)


def main():
    thumbs = {"thumb_A": thumb_a(), "thumb_B": thumb_b(), "thumb_C": thumb_c()}
    banners = {
        "banner_A": banner("America Over Time", "ANIMATED MAPS  •  REAL CENSUS DATA", "fire", "center"),
        "banner_B": banner("Lit Up Atlas", "AMERICA'S HISTORY, ANIMATED ON THE MAP", "ice", "right"),
        "banner_C": banner("Heatmap History", "TIMELAPSE MAPS OF THE UNITED STATES", "magma", "wide"),
    }
    avatars = {"avatar_A": avatar_a(), "avatar_B": avatar_b("AOT"), "avatar_C": avatar_c()}
    for k, im in {**thumbs, **banners, **avatars}.items():
        im.save(OUT / f"{k}.png")
    # phone checks: thumbnails at 210x118, avatars at 98 px circles, banners as phone crop
    sheet([(k, im) for k, im in thumbs.items()], (210, 118), 3, OUT / "check_thumbs_210x118.png")
    sheet([(k, circle_mask(im)) for k, im in avatars.items()], (98, 98), 3, OUT / "check_avatars_98.png")
    sheet([(k, im.crop(SAFE)) for k, im in banners.items()], (773, 212), 1,
          OUT / "check_banners_safe_area.png")
    sheet([(k, im) for k, im in thumbs.items()], (640, 360), 3, OUT / "sheet_thumbs.png")
    sheet([(k, im) for k, im in banners.items()], (853, 480), 3, OUT / "sheet_banners.png")
    sheet([(k, circle_mask(im)) for k, im in avatars.items()], (400, 400), 3, OUT / "sheet_avatars.png")


if __name__ == "__main__":
    main()
