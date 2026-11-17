"""Branding v2 (bright choropleth style) for America Over Time (@AmericaOverTime).

python scripts/branding2.py [--preview]  -> out/branding2/*.png
All numbers on the images are read from Census files at render time (no typed-in figures).
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from mapviz.core import View, albers, bezier, glow_line, text, font  # noqa: E402
from mapviz.choro import (STATE_NAMES, STOPS, apportionment, class_color,  # noqa: E402
                          county_density_2020, legend, num, render)

OUT = Path(__file__).resolve().parent.parent / "out" / "branding2"
OUT.mkdir(parents=True, exist_ok=True)
YEL, WHITE = (255, 222, 0), (255, 255, 255)

CO_BREAKS = [5, 15, 40, 100, 250, 1000]
CO_LABELS = ["UNDER 5", "5–15", "15–40", "40–100", "100–250", "250–1,000", "1,000+"]
ST_BREAKS = [15, 40, 75, 125, 250, 500]


def county_fills():
    return {g: class_color(v, CO_BREAKS) for g, v in county_density_2020().items()}


def state_density(ab, year=2020):
    return num(apportionment()[(STATE_NAMES[ab], year)]["Resident Population Density"])


def state_fills(year=2020):
    return {ab: class_color(state_density(ab, year), ST_BREAKS) for ab in STATE_NAMES}


def px(view, lon, lat):
    x, y = albers(lon, lat)
    a, b = view.px(x, y)
    return float(a), float(b)


def arrow(img, pts, w=24, head=70, color=YEL):
    glow_line(img, pts, w, color, glow=False, head=head, outline_px=7)


# ---------------- thumbnails ----------------
def thumb_a():
    W, H = 1280, 720
    v = View(W, H, cx=0.52, cy=0.56, fill=1.06)
    img = render(v, county_fills(), level="county")
    e, w = px(v, -77.0, 39.6), px(v, -116.5, 39.6)
    arrow(img, bezier(e, ((e[0] + w[0]) / 2, e[1] - 120), w))
    text(img, (W // 2, 4), "AMERICA FILLS UP", 150, fill=WHITE, anchor="ma")
    text(img, (24, H - 10), "1790 → 2020", 150, fill=YEL, anchor="ld")
    return img


def thumb_b():
    W, H = 1280, 720
    v = View(W, H, cx=0.50, cy=0.60, fill=0.98)
    img = render(v, state_fills(), level="state")
    us = int(num(apportionment()[("United States", 2020)]["Resident Population"]))
    nj = state_density("NJ")
    text(img, (22, 6), f"{round(us / 1e6)} MILLION", 160, fill=WHITE)
    text(img, (26, 200), "1790 → 2020", 120, fill=YEL)
    t = px(v, -74.5, 40.1)
    lab = (W - 18, H - 14)
    text(img, (lab[0], lab[1] - 92), "NEW JERSEY", 88, fill=WHITE, anchor="rd")
    text(img, lab, f"{nj:,.0f} / SQ MI", 88, fill=YEL, anchor="rd")
    arrow(img, [(lab[0] - 120, lab[1] - 200), (t[0] + 14, t[1] + 16)], w=22, head=62)
    return img


def thumb_c():
    W, H = 1280, 720
    v = View(W, H, cx=0.58, cy=0.60, fill=2.0, center=(-84.0, 37.2))
    img = render(v, county_fills(), level="county", county_line_alpha=90)
    text(img, (W // 2, 2), "1790 → 2020", 210, fill=YEL, anchor="ma")
    text(img, (W - 26, H - 12), "EAST TO WEST", 120, fill=WHITE, anchor="rd")
    a, b = px(v, -76.0, 35.0), (40, px(v, -92.0, 35.0)[1])
    arrow(img, [a, b], w=30, head=90)
    return img


# ---------------- banner 2560x1440 ----------------
SAFE = (507, 508, 2053, 931)


def banner():
    W, H = 2560, 1440
    v = View(W, H, cx=0.5, cy=0.50, fill=0.98)
    img = render(v, county_fills(), level="county", county_line_alpha=60)
    panel = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(panel).rounded_rectangle([560, 560, 2000, 880], radius=40, fill=(8, 18, 60, 225),
                                            outline=YEL + (255,), width=8)
    img = Image.alpha_composite(img.convert("RGBA"), panel).convert("RGB")
    text(img, (W // 2, 690), "AMERICA OVER TIME", 196, fill=YEL, anchor="mm", shadow=False)
    text(img, (W // 2, 825), "ANIMATED MAPS  •  REAL CENSUS DATA", 64, fill=WHITE, anchor="mm",
         shadow=False)
    return img


# ---------------- avatar 800x800 ----------------
def avatar():
    S = 800
    v = View(S, S, cx=0.5, cy=0.5, fill=0.84)
    img = render(v, state_fills(), level="state", state_line_w=6)
    text(img, (S // 2, S // 2 + 10), "AOT", 270, fill=YEL, anchor="mm", stroke=22)
    return img


# ---------------- checks ----------------
def circle(img, size):
    im = img.resize((size * 4, size * 4), Image.LANCZOS)
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).ellipse([0, 0, im.size[0] - 1, im.size[1] - 1], fill=255)
    bg = Image.new("RGB", im.size, (255, 255, 255))
    bg.paste(im, mask=m)
    return bg.resize((size, size), Image.LANCZOS)


def sheet(items, path, pad=20, label_h=30, bg=(235, 235, 235)):
    w = sum(im.size[0] for _, im in items) + pad * (len(items) + 1)
    h = max(im.size[1] for _, im in items) + pad * 2 + label_h
    s = Image.new("RGB", (w, h), bg)
    d = ImageDraw.Draw(s)
    x = pad
    for lab, im in items:
        d.text((x, pad), lab, fill=(0, 0, 0), font=font(22))
        s.paste(im, (x, pad + label_h))
        x += im.size[0] + pad
    s.save(path)


def legend_sheet():
    img = Image.new("RGB", (520, 420), (40, 60, 110))
    legend(img, (24, 20), CO_LABELS, "PEOPLE PER SQ MI", size=1.2)
    return img


def main():
    th = {"thumb_A": thumb_a(), "thumb_B": thumb_b(), "thumb_C": thumb_c()}
    bn = banner()
    av = avatar()
    for k, im in th.items():
        im.save(OUT / f"{k}.png")
    bn.convert("RGB").save(OUT / "banner.jpg", quality=93)
    av.save(OUT / "avatar.png")
    sheet([(k, im.resize((640, 360), Image.LANCZOS)) for k, im in th.items()], OUT / "sheet_thumbs.png")
    sheet([(k, im.resize((210, 118), Image.LANCZOS)) for k, im in th.items()],
          OUT / "check_thumbs_210x118.png")
    sheet([("banner (whole, TV)", bn.resize((853, 480), Image.LANCZOS)),
           ("safe area 1546x423 (phone)", bn.crop(SAFE).resize((773, 212), Image.LANCZOS))],
          OUT / "check_banner.png")
    sheet([("400", circle(av, 400)), ("98", circle(av, 98)), ("48", circle(av, 48))],
          OUT / "check_avatar.png")
    legend_sheet().save(OUT / "legend_scale.png")


if __name__ == "__main__":
    main()
