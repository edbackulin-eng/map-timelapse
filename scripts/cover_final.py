"""Final cover (choice C): county map, same 7 classes as the video legend, big '1790 -> 2020'."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from PIL import Image, ImageEnhance
from mapviz.core import View, albers, text
from mapviz.choro import STOPS, county_density_2020, render
from mapviz.video import BREAKS, cls
from scripts.branding2 import arrow, px, YEL, WHITE  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "out" / "cover"; OUT.mkdir(parents=True, exist_ok=True)
W, H = 1280, 720
v = View(W, H, cx=0.58, cy=0.60, fill=2.0, center=(-84.0, 37.2))
fills = {g: STOPS[cls(d)] for g, d in county_density_2020().items()}
img = render(v, fills, level="county", county_line_alpha=90)
img = ImageEnhance.Color(img).enhance(1.12)
img = ImageEnhance.Contrast(img).enhance(1.06)
text(img, (W // 2, 2), "1790 → 2020", 210, fill=YEL, anchor="ma")
text(img, (W - 26, H - 12), "EAST TO WEST", 120, fill=WHITE, anchor="rd")
a, b = px(v, -76.0, 35.0), (40, px(v, -92.0, 35.0)[1])
arrow(img, [a, b], w=30, head=90)
img.save(OUT / "thumbnail_C_final.jpg", quality=92)
img.resize((210, 118), Image.LANCZOS).save(OUT / "check_210x118.png")
print((OUT / "thumbnail_C_final.jpg").stat().st_size)
