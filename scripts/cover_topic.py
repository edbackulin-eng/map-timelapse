"""Cover (1280x720) of a topic: county density map 2020 + big years + arrow. TOPIC=<module>; reads TP.COVER. -> assets/covers/<slug>.jpg"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from PIL import Image, ImageEnhance
from mapviz import topic
from mapviz.core import View, text
from mapviz.choro import STOPS, county_density_2020, render
from mapviz.video import cls
from scripts.branding2 import arrow, px, YEL, WHITE

TP = topic.load()
C = TP.COVER
root = Path(__file__).resolve().parent.parent
W, H = 1280, 720
v = View(W, H, cx=C["cx"], cy=C["cy"], fill=C["fill"], center=C["center"])
fills = {g: STOPS[cls(d)] for g, d in county_density_2020().items()}
img = render(v, fills, level="county", county_line_alpha=90)
img = ImageEnhance.Color(img).enhance(1.12)
img = ImageEnhance.Contrast(img).enhance(1.06)
text(img, (W // 2, 2), C["big"], 210, fill=YEL, anchor="ma")
text(img, (W - 26, H - 12), C["small"], 112, fill=WHITE, anchor="rd")
if C.get("arrow"):
    (a_lon, a_lat), (b_lon, b_lat) = C["arrow"]
    arrow(img, [px(v, a_lon, a_lat), px(v, b_lon, b_lat)], w=30, head=90)
out = root / "assets" / "covers"; out.mkdir(parents=True, exist_ok=True)
img.save(out / f"{TP.SLUG}.jpg", quality=92)
img.resize((210, 118), Image.LANCZOS).save(root / "out" / f"cover_check_{TP.SLUG}.png")
print((out / f"{TP.SLUG}.jpg").stat().st_size)
