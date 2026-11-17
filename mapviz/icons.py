"""Vector icons drawn in code (no images, no AI). icon(draw, name, cx, cy, s) draws inside an s x s box."""
import math

YEL, WHITE, BLACK, RED, BLUE, GREEN, BROWN = (255, 222, 0), (255, 255, 255), (15, 15, 25), (235, 40, 40), (40, 110, 255), (60, 210, 90), (150, 95, 40)


def _poly(d, pts, fill, w=3):
    d.polygon(pts, fill=fill, outline=BLACK, width=w)


def icon(d, name, cx, cy, s):
    k = s / 100.0
    P = lambda x, y: (cx + x * k, cy + y * k)   # box coordinates -50..50
    w = max(2, int(3 * k))
    if name == "scroll":
        _poly(d, [P(-30, -38), P(30, -38), P(30, 38), P(-30, 38)], (250, 235, 190), w)
        d.ellipse([*P(-38, -46), *P(-22, -30)], fill=(220, 195, 130), outline=BLACK, width=w)
        d.ellipse([*P(22, 30), *P(38, 46)], fill=(220, 195, 130), outline=BLACK, width=w)
        for y in (-22, -8, 6, 20):
            d.line([P(-20, y), P(20, y)], fill=BROWN, width=w)
    elif name == "boat":
        _poly(d, [P(-44, 6), P(44, 6), P(30, 30), P(-30, 30)], BROWN, w)
        _poly(d, [P(-22, -16), P(22, -16), P(22, 6), P(-22, 6)], WHITE, w)
        d.line([P(0, -16), P(0, -40)], fill=BLACK, width=w + 1)
        _poly(d, [P(0, -40), P(26, -32), P(0, -24)], RED, w)
        d.arc([*P(-46, 26), *P(-14, 44)], 180, 360, fill=BLUE, width=w + 1)
        d.arc([*P(-14, 26), *P(18, 44)], 180, 360, fill=BLUE, width=w + 1)
        d.arc([*P(18, 26), *P(50, 44)], 180, 360, fill=BLUE, width=w + 1)
    elif name == "star":
        pts = []
        for i in range(10):
            r = 46 if i % 2 == 0 else 19
            a = -math.pi / 2 + i * math.pi / 5
            pts.append(P(r * math.cos(a), r * math.sin(a)))
        _poly(d, pts, YEL, w)
    elif name == "pick":
        d.line([P(-30, 40), P(24, -20)], fill=BROWN, width=int(10 * k))
        d.line([P(-30, 40), P(24, -20)], fill=(190, 130, 60), width=int(6 * k))
        d.arc([*P(-8, -50), *P(52, 10)], 200, 340, fill=BLACK, width=int(13 * k))
        d.arc([*P(-8, -50), *P(52, 10)], 205, 335, fill=(190, 195, 205), width=int(8 * k))
        _poly(d, [P(-44, 30), P(-34, 22), P(-26, 32), P(-34, 44)], YEL, w)
    elif name == "house":
        _poly(d, [P(-34, -4), P(0, -40), P(34, -4)], RED, w)
        _poly(d, [P(-26, -4), P(26, -4), P(26, 38), P(-26, 38)], (240, 220, 170), w)
        _poly(d, [P(-8, 12), P(8, 12), P(8, 38), P(-8, 38)], BROWN, w)
        _poly(d, [P(10, 0), P(20, 0), P(20, 10), P(10, 10)], BLUE, max(1, w - 1))
    elif name == "train":
        _poly(d, [P(-44, -8), P(14, -8), P(14, 22), P(-44, 22)], (60, 60, 70), w)
        _poly(d, [P(14, -28), P(40, -28), P(40, 22), P(14, 22)], RED, w)
        _poly(d, [P(-36, -26), P(-26, -26), P(-26, -8), P(-36, -8)], (60, 60, 70), w)
        d.ellipse([*P(-40, 14), *P(-18, 36)], fill=YEL, outline=BLACK, width=w)
        d.ellipse([*P(-12, 14), *P(10, 36)], fill=YEL, outline=BLACK, width=w)
        d.ellipse([*P(18, 14), *P(40, 36)], fill=YEL, outline=BLACK, width=w)
        d.line([P(-48, 38), P(46, 38)], fill=BLACK, width=w + 1)
    elif name == "fence":
        for x in (-34, -12, 12, 34):
            _poly(d, [P(x - 6, -30), P(x + 6, -30), P(x + 6, 40), P(x - 6, 40)], (200, 150, 90), w)
        d.line([P(-44, -12), P(44, -12)], fill=BLACK, width=w + 5)
        d.line([P(-44, -12), P(44, -12)], fill=YEL, width=w + 1)
        d.line([P(-44, 14), P(44, 14)], fill=BLACK, width=w + 5)
        d.line([P(-44, 14), P(44, 14)], fill=YEL, width=w + 1)
    elif name == "ship":
        _poly(d, [P(-44, 6), P(44, 6), P(32, 32), P(-32, 32)], (40, 60, 120), w)
        _poly(d, [P(-26, -14), P(24, -14), P(24, 6), P(-26, 6)], WHITE, w)
        _poly(d, [P(-8, -34), P(10, -34), P(10, -14), P(-8, -14)], RED, w)
        d.ellipse([*P(8, -50), *P(24, -36)], fill=(230, 230, 235), outline=BLACK, width=max(1, w - 1))
        d.arc([*P(-46, 26), *P(-14, 44)], 180, 360, fill=BLUE, width=w + 1)
        d.arc([*P(-14, 26), *P(18, 44)], 180, 360, fill=BLUE, width=w + 1)
        d.arc([*P(18, 26), *P(50, 44)], 180, 360, fill=BLUE, width=w + 1)
    elif name == "arrows":
        for dx, dy, col in ((-18, 12, BLUE), (14, -14, (255, 120, 0))):
            d.line([P(dx - 20, dy + 22), P(dx + 18, dy - 8)], fill=BLACK, width=int(12 * k))
            d.line([P(dx - 20, dy + 22), P(dx + 18, dy - 8)], fill=col, width=int(7 * k))
            _poly(d, [P(dx + 30, dy - 18), P(dx + 8, dy - 18), P(dx + 22, dy + 6)], col, w)
    elif name == "wind":
        for i, y in enumerate((-26, 0, 26)):
            x0 = -42 + i * 6
            d.line([P(x0, y), P(30, y)], fill=(210, 190, 140), width=int(8 * k))
            d.arc([*P(18, y - 18), *P(52, y + 4)], 270, 100, fill=(210, 190, 140), width=int(8 * k))
    elif name == "shield":
        pts = [P(-38, -34), P(38, -34), P(38, 8), P(0, 46), P(-38, 8)]
        _poly(d, pts, BLUE, w)
        _poly(d, [P(-38, -34), P(38, -34), P(38, -14), P(-38, -14)], RED, w)
        d.line([P(-6, -4), P(-6, 24)], fill=WHITE, width=int(9 * k))
        d.line([P(-6, -4), P(10, -4)], fill=WHITE, width=int(6 * k))
        d.line([P(-6, 24), P(10, 24)], fill=WHITE, width=int(6 * k))
    elif name == "snow":
        for a_ in (0, 60, 120):
            r = math.radians(a_)
            d.line([P(46 * math.cos(r), 46 * math.sin(r)), P(-46 * math.cos(r), -46 * math.sin(r))], fill=BLACK, width=int(11 * k))
            d.line([P(46 * math.cos(r), 46 * math.sin(r)), P(-46 * math.cos(r), -46 * math.sin(r))], fill=(150, 215, 255), width=int(6 * k))
        d.ellipse([*P(-9, -9), *P(9, 9)], fill=WHITE, outline=BLACK, width=w)
    elif name == "rocket":
        _poly(d, [P(0, -46), P(14, -14), P(14, 24), P(-14, 24), P(-14, -14)], WHITE, w)
        _poly(d, [P(-14, 4), P(-30, 34), P(-14, 24)], RED, w)
        _poly(d, [P(14, 4), P(30, 34), P(14, 24)], RED, w)
        d.ellipse([*P(-7, -12), *P(7, 2)], fill=BLUE, outline=BLACK, width=w)
        _poly(d, [P(-9, 26), P(9, 26), P(0, 48)], (255, 150, 0), w)
    elif name == "sun":
        for i in range(12):
            a = i * math.pi / 6
            d.line([P(30 * math.cos(a), 30 * math.sin(a)), P(48 * math.cos(a), 48 * math.sin(a))], fill=BLACK, width=int(11 * k))
            d.line([P(30 * math.cos(a), 30 * math.sin(a)), P(48 * math.cos(a), 48 * math.sin(a))], fill=(255, 160, 0), width=int(6 * k))
        d.ellipse([*P(-26, -26), *P(26, 26)], fill=YEL, outline=BLACK, width=w + 1)
