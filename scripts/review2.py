"""Render a frame every 5 s and write contact sheets (3x3, 640x360 each) to out/review2/."""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from PIL import Image, ImageDraw
from mapviz import video2 as V
step = float(sys.argv[1]) if len(sys.argv) > 1 else 5.0
lo = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
hi = float(sys.argv[3]) if len(sys.argv) > 3 else V.TOTAL_S
r = V.Renderer()
out = Path(__file__).resolve().parent.parent / "out" / "review2"; out.mkdir(parents=True, exist_ok=True)
ts = []; t = lo
while t < min(hi, V.TOTAL_S): ts.append(t); t += step
sheets = [ts[k:k + 9] for k in range(0, len(ts), 9)]
t0 = time.time()
for si, grp in enumerate(sheets):
    sh = Image.new("RGB", (1920, 1080), (30, 30, 30)); d = ImageDraw.Draw(sh)
    for k, t in enumerate(grp):
        fr = Image.fromarray(r.frame(int(t * V.FPS))).resize((640, 360), Image.LANCZOS)
        x, y = (k % 3) * 640, (k // 3) * 360
        sh.paste(fr, (x, y)); d.rectangle([x, y, x + 120, y + 22], fill=(0, 0, 0)); d.text((x + 4, y + 4), f"t={t:.0f}s", fill=(255, 255, 0))
    sh.save(out / f"sheet_{si:02d}.png"); print("sheet", si, f"{time.time() - t0:.0f}s", flush=True)
