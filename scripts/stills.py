import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from PIL import Image
from mapviz import video as V
r = V.Renderer()
out = Path(__file__).resolve().parent.parent / "out" / "stills"; out.mkdir(parents=True, exist_ok=True)
ts = [float(x) for x in sys.argv[1:]] or [3, 15, 30]
for t in ts:
    t0 = time.time(); fr = r.frame(int(t * V.FPS)); dt = time.time() - t0
    Image.fromarray(fr).save(out / f"t{t:07.2f}.png"); print(t, f"{dt:.2f}s")
print("TOTAL_S", V.TOTAL_S, "frames", V.TOTAL_FRAMES)
