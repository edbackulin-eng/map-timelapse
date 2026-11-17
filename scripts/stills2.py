import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from PIL import Image
from mapviz import video2 as V
t0 = time.time(); r = V.Renderer(); print("init", round(time.time() - t0, 1), "s")
out = Path(__file__).resolve().parent.parent / "out" / "stills2"; out.mkdir(parents=True, exist_ok=True)
ts = [float(x) for x in sys.argv[1:]] or [5, 30]
for t in ts:
    t1 = time.time(); fr = r.frame(int(t * V.FPS)); dt = time.time() - t1
    Image.fromarray(fr).save(out / f"t{t:07.2f}.png"); print(t, f"{dt:.2f}s")
print("TOTAL_S", V.TOTAL_S, "frames", V.TOTAL_FRAMES)
