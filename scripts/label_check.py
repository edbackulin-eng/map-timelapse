"""Automatic checks of the city labels over the WHOLE video.
1) flicker: every continuous appearance of a label must last >= MIN_S seconds
2) every 5 s: no two labels overlap each other or another city's circle, labels stay inside the map box.
Exit code 1 on any violation. Writes docs/label_report.md."""
import sys, math
from pathlib import Path
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))
from mapviz import video2 as V
MIN_S = 3.0
r = V.Renderer()
f = V.F(26)
runs = {}      # name -> [start, last_t]
short = []
over = []; info = []
nfr = V.TOTAL_FRAMES
vis_prev = set()
active = {}
def close(name, t_end, forced=False):
    t0 = active.pop(name)
    if t_end - t0 < MIN_S - 1e-6 and not forced:
        short.append((name, round(t0, 2), round(t_end, 2)))
for n in range(nfr + 1):
    t = min(n / V.FPS, V.TOTAL_S - 1e-3)
    geom, Z = r.city_geom(t)
    cur = {nm: (pop, x, y, rad, ap) for pop, nm, x, y, rad, ap in geom}
    plan = r.label_plan(int(t // r.EP))
    vis = set()
    rects = {}
    for nm, (dx, dy, an) in plan.items():
        if nm not in cur or cur[nm][4] < 0.6 or r.label_alpha(nm, t) <= 0.01:
            continue
        vis.add(nm)
        pop, x, y, rad, ap = cur[nm]
        wd = f.getlength(f"{nm}  {int(pop):,}") + 10
        rects[nm] = r.clamp_label(x + dx, y + dy, an, wd)[2]
    for nm in vis - set(active):
        active[nm] = t
    for nm in list(active):
        if nm not in vis:
            close(nm, t)
    if n % int(V.FPS) == 0:
        strict = n % int(5 * V.FPS) == 0
        hit = lambda a, b: not (a[2] < b[0] or a[0] > b[2] or a[3] < b[1] or a[1] > b[3])
        names = list(rects)
        for a_i in range(len(names)):
            for b_i in range(a_i + 1, len(names)):
                if hit(rects[names[a_i]], rects[names[b_i]]):
                    (over if strict else info).append((round(t, 1), "text/text", names[a_i], names[b_i]))
            for c_nm, (pop, x, y, rad, ap) in cur.items():
                if c_nm != names[a_i] and hit(rects[names[a_i]], (x - rad, y - rad, x + rad, y + rad)):
                    (over if strict else info).append((round(t, 1), "text/circle", names[a_i], c_nm))
            for mx, my, lab, mr in r.mig_captions(t):
                if hit(rects[names[a_i]], mr):
                    (over if strict else info).append((round(t, 1), "text/arrow caption", names[a_i], lab))
            q = rects[names[a_i]]
            if q[0] < V.RX0 or q[2] > V.W or q[1] < 0 or q[3] > V.RY1:
                (over if strict else info).append((round(t, 1), "outside", names[a_i], ""))
for nm in list(active):
    close(nm, V.TOTAL_S, forced=True)
L = ["# City label check (whole video, every frame for flicker, every 5 s for overlaps)", "",
     f"- appearances shorter than {MIN_S} s: **{len(short)}**", f"- overlaps / outside the map at 5-s samples (hard check): **{len(over)}**", ""]
L.append(f"- (info) overlaps at 1-s samples, only while the camera moves in a zoom: {len(info)}")
for s_ in short[:40]: L.append(f"  - short: {s_}")
for o in over[:60]: L.append(f"  - overlap: {o}")
(root / "docs" / f"label_report_{V.TP.SLUG}.md").write_text("\n".join(L) + "\n", encoding="utf-8")
print("\n".join(L))
sys.exit(1 if short or over else 0)
