"""Step 5: draw every scene. White background, bold words, simple characters, real charts."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONTS = Path(__file__).resolve().parent.parent / "assets" / "fonts"
W, H = 1080, 1920
WHITE, BLACK, GREY = (255, 255, 255), (17, 17, 17), (120, 120, 120)
COLORS = {"green": (22, 163, 74), "red": (220, 38, 38), "blue": (37, 99, 235),
          "orange": (234, 88, 12), "black": BLACK, "purple": (124, 58, 237)}
PALETTE = ["green", "blue", "orange", "purple"]
_fc = {}


def F(size, w="Bold"):
    k = (max(8, int(size)), w)
    if k not in _fc:
        name = "Anton-Regular.ttf" if w == "Anton" else f"Poppins-{w}.ttf"
        _fc[k] = ImageFont.truetype(str(FONTS / name), k[0])
    return _fc[k]


def col(c, i=0):
    return COLORS.get(c or "", COLORS[PALETTE[i % len(PALETTE)]])


# ---------- motion helpers ----------
def pop(t, d=0.22):
    if t <= 0: return 0.0
    if t >= d: return 1.0
    x = t / d; c = 1.70158
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


def ease(x):
    x = min(max(x, 0), 1)
    return 1 - (1 - x) ** 3


def text_c(d, xy, s, size, fill=BLACK, w="Bold", scale=1.0, anchor="mm", stroke=0, stroke_fill=BLACK):
    if scale > 0.01:
        d.text(xy, s, font=F(size * scale, w), fill=fill, anchor=anchor,
               stroke_width=int(stroke * scale), stroke_fill=stroke_fill)


def wrap(s, size, maxw, w="Bold"):
    lines, cur = [], ""
    for wd in str(s).split():
        t = (cur + " " + wd).strip()
        if F(size, w).getlength(t) <= maxw or not cur: cur = t
        else: lines.append(cur); cur = wd
    return lines + ([cur] if cur else [])


def fit_lines(s, size, maxw, max_lines, w="Bold"):
    while size > 40:
        ls = wrap(s, size, maxw, w)
        if len(ls) <= max_lines and all(F(size, w).getlength(l) <= maxw for l in ls): return ls, size
        size -= 8
    return wrap(s, size, maxw, w), size


def money(x):
    x = float(x)
    if abs(x) >= 1e6: return f"${x / 1e6:.1f}M"
    if abs(x) >= 1e3: return f"${round(x / 1e3)}K"
    return f"${round(x)}"


def avatar(d, cx, cy, r, color, scale=1.0, name=None):
    if scale <= 0.01: return
    r *= scale
    d.rounded_rectangle([cx - 1.25 * r, cy + .95 * r, cx + 1.25 * r, cy + 2.9 * r], radius=r, fill=color)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 220, 185), outline=BLACK, width=max(2, int(r * .06)))
    e = r * .12
    for sx in (-.35, .35):
        d.ellipse([cx + sx * r - e, cy - .1 * r - e, cx + sx * r + e, cy - .1 * r + e], fill=BLACK)
    d.arc([cx - .4 * r, cy - .05 * r, cx + .4 * r, cy + .5 * r], 20, 160, fill=BLACK, width=max(2, int(r * .07)))
    if name: text_c(d, (cx, cy + 3.35 * r), name, r * .55)


def pill(d, cx, cy, s, size, bg=BLACK, fg=WHITE, scale=1.0):
    if scale <= 0.01: return
    f = F(size * scale); tw = f.getlength(s); p = size * .5 * scale
    d.rounded_rectangle([cx - tw / 2 - p, cy - size * .75 * scale, cx + tw / 2 + p, cy + size * .75 * scale],
                        radius=size * scale, fill=bg)
    d.text((cx, cy), s, font=f, fill=fg, anchor="mm")


def footnote(d, s):
    text_c(d, (540, 1760), s, 32, GREY, "Medium")


# ---------- data prep (runs once per scene, not per frame) ----------
def compound_series(v):
    rate, end = float(v.get("rate", 0.08)), int(v.get("end_age", 65))
    people = v["people"]
    a0 = min(int(p["start_age"]) for p in people)
    series = []
    for p in people:
        b, s = 0.0, [0.0]
        for age in range(a0, end):
            for _ in range(12):
                b = b * (1 + rate / 12) + (float(p["monthly"]) if int(p["start_age"]) <= age < int(p.get("stop_age", end)) else 0)
            s.append(b)
        series.append(s)
    v["_a0"], v["_end"], v["_series"] = a0, end, series


def prepare(v):
    """Fetch/compute anything a visual needs. Returns a possibly-changed visual."""
    t = v.get("type")
    if t == "compound":
        compound_series(v)
    elif t == "ticker":
        try:
            import yfinance as yf
            h = yf.Ticker(v["symbol"]).history(period=v.get("period", "5y"))["Close"].dropna()
            if len(h) < 5: raise ValueError("no data")
            step = max(1, len(h) // 300)
            v["_closes"] = [float(x) for x in h.values[::step]]
            v["_from"], v["_to"] = h.index[0].strftime("%b %Y"), h.index[-1].strftime("%b %Y")
        except Exception as e:
            print(f"  ticker {v.get('symbol')} failed ({e}); using a caption instead")
            return {"type": "caption", "words": v.get("title") or v.get("symbol", "")}
    elif t == "meme":
        if not v.get("image"):
            return {"type": "caption", "words": v.get("label") or v.get("top") or v.get("bottom") or v.get("idea", "")}
        v["_img"] = Image.open(v["image"]).convert("RGB")
    return v


# ---------- scenes ----------
def s_caption(d, im, t, dur, v):
    ls, size = fit_lines(v["words"], 120, 920, 4)
    y0 = 960 - (len(ls) - 1) * size * .62
    for i, l in enumerate(ls):
        text_c(d, (540, y0 + i * size * 1.24), l, size, scale=pop(t - i * .1))


def s_big(d, im, t, dur, v):
    ls, size = fit_lines(v["words"], 210, 960, 2)
    for i, l in enumerate(ls):
        text_c(d, (540, 960 - (len(ls) - 1) * size * .55 + i * size * 1.1), l, size, col(v.get("color"), 0) if v.get("color") else BLACK, scale=pop(t))


def s_person(d, im, t, dur, v):
    avatar(d, 540, 760, 190, col(v.get("color")), pop(t), v.get("name"))
    if v.get("tag"): pill(d, 540, 1560, v["tag"], 80, scale=pop(t - .35))


def s_duo(d, im, t, dur, v):
    avatar(d, 330, 820, 140, col(v.get("left_color"), 0), pop(t), v.get("left"))
    avatar(d, 750, 820, 140, col(v.get("right_color"), 1), pop(t - .25), v.get("right"))
    if v.get("title"):
        ls, size = fit_lines(v["title"], 78, 960, 2)
        for i, l in enumerate(ls): text_c(d, (540, 430 + i * size * 1.2), l, size, scale=pop(t - .5))


def s_stat(d, im, t, dur, v):
    ls, size = fit_lines(v["value"], 220, 980, 1)
    text_c(d, (540, 880), ls[0], size, col(v.get("color"), 0), scale=pop(t))
    ll, s2 = fit_lines(v.get("label", ""), 64, 920, 2, "Medium")
    for i, l in enumerate(ll): text_c(d, (540, 1080 + i * 80), l, s2, GREY, "Medium", scale=pop(t - .3))


def s_list(d, im, t, dur, v):
    text_c(d, (540, 520), v.get("title", ""), 84, scale=pop(t))
    items = v.get("items", [])[:3]
    n = len(items) or 1
    for i, it in enumerate(items):
        s = pop(t - (0.35 + i * dur * .6 / n))
        if s <= .01: continue
        y = 820 + i * 260
        d.ellipse([110, y - 50, 210, y + 50], fill=col(None, i))
        text_c(d, (160, y), str(i + 1), 60, WHITE, scale=s)
        ls, size = fit_lines(it, 62, 760, 2)
        for j, l in enumerate(ls):
            text_c(d, (250, y - (len(ls) - 1) * 38 + j * 76), l, size, anchor="lm", scale=s)


def s_bars(d, im, t, dur, v):
    text_c(d, (540, 470), v.get("title", ""), 76, scale=pop(t))
    bars = v["bars"][:4]; n = len(bars)
    base, maxh = 1500, 760
    mx = max(float(b["value"]) for b in bars) or 1
    gap = 860 / n; bw = min(240, gap * .62)
    for i, b in enumerate(bars):
        appear = 0.2 + i * dur * .45 / max(1, n - 1)
        if t < appear: continue
        g = ease((t - appear) / .7); c = col(b.get("color"), i)
        cx = 110 + gap * (i + .5); h = maxh * float(b["value"]) / mx * g
        d.rounded_rectangle([cx - bw / 2, base - h, cx + bw / 2, base], radius=22, fill=c)
        text_c(d, (cx, base - h - 60), b.get("display") or money(float(b["value"]) * g), 72 if n < 4 else 56, c)
        text_c(d, (cx, base + 65), b["label"], 56 if n < 4 else 44)
    d.line([100, base, 980, base], fill=BLACK, width=6)


def s_compound(d, im, t, dur, v):
    people, series = v["people"], v["_series"]
    a0, end = v["_a0"], v["_end"]
    if v.get("mode") == "result":
        text_c(d, (540, 430), v.get("title") or f"balance at {end}", 76, scale=pop(t))
        n = len(people); gap = 960 / n
        best = max(range(n), key=lambda i: series[i][-1])
        for i, p in enumerate(people):
            cx = 60 + gap * (i + .5); c = col(p.get("color"), i)
            avatar(d, cx, 760, 110 if n <= 2 else 85, c, pop(t))
            text_c(d, (cx, 1180), money(series[i][-1]), 120 if n <= 2 else 80, c, scale=pop(t - .1 - i * .4))
            text_c(d, (cx, 1280), p["name"], 54, scale=pop(t - .1 - i * .4))
            if i == best: pill(d, cx, 1390, "WINNER", 50, bg=c, scale=pop(t - .9))
    else:
        text_c(d, (540, 420), v.get("title") or "account balance by age", 64, scale=pop(t))
        x0, x1, y0, y1 = 150, 960, 1450, 650
        mx = max(max(s) for s in series) * 1.04 or 1
        yrs = end - a0
        X = lambda i: x0 + (x1 - x0) * i / yrs
        Y = lambda val: y0 - (y0 - y1) * val / mx
        d.line([x0, y0, x1, y0], fill=BLACK, width=5); d.line([x0, y0, x0, y1 - 20], fill=BLACK, width=5)
        for a in sorted({a0, a0 + yrs // 3, a0 + 2 * yrs // 3, end}):
            text_c(d, (X(a - a0), y0 + 50), str(a), 40, GREY, "Medium")
        k = int(yrs * ease(t / (dur * .85)))
        for i, (p, s) in enumerate(zip(people, series)):
            c = col(p.get("color"), i)
            pts = [(X(j), Y(s[j])) for j in range(k + 1)]
            if len(pts) > 1: d.line(pts, fill=c, width=12, joint="curve")
            d.ellipse([pts[-1][0] - 14, pts[-1][1] - 14, pts[-1][0] + 14, pts[-1][1] + 14], fill=c)
            lx = 540 - (len(people) - 1) * 110 + i * 220
            d.ellipse([lx - 16, 514, lx + 16, 546], fill=c)
            text_c(d, (lx + 30, 532), p["name"], 46, c, anchor="lm")
    footnote(d, f"Assumes {v.get('rate', 0.08) * 100:g}% avg yearly return. Not financial advice.")


def s_ticker(d, im, t, dur, v):
    cl = v["_closes"]; up = cl[-1] >= cl[0]; c = COLORS["green" if up else "red"]
    text_c(d, (540, 420), v.get("title") or v["symbol"], 70, scale=pop(t))
    chg = (cl[-1] / cl[0] - 1) * 100
    text_c(d, (540, 540), f"{v['symbol']}  {'+' if up else ''}{chg:.0f}%", 64, c, scale=pop(t - .2))
    x0, x1, y0, y1 = 120, 960, 1400, 700
    lo, hi = min(cl), max(cl); rng = (hi - lo) or 1
    n = max(2, int(len(cl) * ease(t / (dur * .8))))
    pts = [(x0 + (x1 - x0) * i / (len(cl) - 1), y0 - (y0 - y1) * (cl[i] - lo) / rng) for i in range(n)]
    d.line(pts, fill=c, width=8, joint="curve")
    text_c(d, (x0, y0 + 60), v["_from"], 38, GREY, "Medium", anchor="lm")
    text_c(d, (x1, y0 + 60), v["_to"], 38, GREY, "Medium", anchor="rm")
    footnote(d, "Past performance doesn't guarantee future results.")


def s_comment(d, im, t, dur, v):
    s = pop(t)
    ls = wrap(v.get("text", ""), 50, 780, "Medium")[:4]
    if s > .01:
        cx, cy = 540, 820; w = 900 * s; h = (250 + 62 * len(ls)) * s
        d.rounded_rectangle([cx - w / 2 + 8, cy - h / 2 + 12, cx + w / 2 + 8, cy + h / 2 + 12], radius=36 * s, fill=(225, 225, 225))
        d.rounded_rectangle([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], radius=36 * s, fill=WHITE, outline=(210, 210, 210), width=3)
        lx, ty = cx - w / 2 + 60 * s, cy - h / 2 + 55 * s
        d.ellipse([lx, ty, lx + 80 * s, ty + 80 * s], fill=COLORS["blue"])
        d.text((lx + 105 * s, ty + 40 * s), v.get("user", "someone"), font=F(38 * s), fill=BLACK, anchor="lm")
        for i, l in enumerate(ls):
            d.text((lx, ty + (140 + i * 62) * s), l, font=F(50 * s, "Medium"), fill=BLACK, anchor="lm")
        d.text((lx, ty + (140 + len(ls) * 62 + 20) * s), "12.4K likes  ·  reply", font=F(32 * s, "Medium"), fill=GREY, anchor="lm")
    if v.get("stamp"):
        st = pop(t - dur * .45, .3)
        if st > .01:
            f = F(100); tw = int(f.getlength(v["stamp"])) + 120
            stamp = Image.new("RGBA", (tw, 260), (0, 0, 0, 0)); sd = ImageDraw.Draw(stamp)
            sd.rounded_rectangle([10, 10, tw - 10, 250], radius=30, outline=COLORS["red"], width=14)
            sd.text((tw // 2, 130), v["stamp"], font=f, fill=COLORS["red"], anchor="mm")
            stamp = stamp.rotate(-8, expand=True, resample=Image.BICUBIC)
            sc = min(st, 980 / stamp.width)
            stamp = stamp.resize((max(1, int(stamp.width * sc)), max(1, int(stamp.height * sc))))
            im.paste(stamp, (540 - stamp.width // 2, 1400 - stamp.height // 2), stamp)


def meme_card(img, top, bottom, maxw=960, maxh=1150):
    img = img.copy()
    sc = min(maxw / img.width, maxh / img.height)
    img = img.resize((int(img.width * sc), int(img.height * sc)), Image.LANCZOS)
    d = ImageDraw.Draw(img)
    for txt, at_top in ((top, True), (bottom, False)):
        if not txt: continue
        ls, size = fit_lines(txt.upper(), int(img.width * .11), img.width * .92, 2, "Anton")
        for j, l in enumerate(ls):
            y = (size * .7 + j * size * 1.1) if at_top else (img.height - size * .7 - (len(ls) - 1 - j) * size * 1.1)
            d.text((img.width / 2, y), l, font=F(size, "Anton"), fill=WHITE, anchor="mm",
                   stroke_width=max(3, size // 14), stroke_fill=BLACK)
    return img


def _meme_layout(v):
    """Caption above the image (meme-page style) when there's a label, else the image alone."""
    label = (v.get("label") or "").strip()
    if not label:
        return [], 0, meme_card(v["_img"], v.get("top", ""), v.get("bottom", "")), 930
    ls, size = fit_lines(label, 72, 940, 3)
    text_h = len(ls) * size * 1.22
    card = meme_card(v["_img"], v.get("top", ""), v.get("bottom", ""), maxh=1180 - text_h)
    total = text_h + 50 + card.height
    top_y = 960 - total / 2
    return ls, size, card, top_y + text_h + 50 + card.height / 2


def s_meme(d, im, t, dur, v):
    if "_layout" not in v:
        v["_layout"] = _meme_layout(v)
    ls, size, c, cy = v["_layout"]
    y0 = cy - c.height / 2 - 50 - len(ls) * size * 1.22
    for i, l in enumerate(ls):
        text_c(d, (540, y0 + (i + .5) * size * 1.22), l, size, scale=pop(t))
    s = pop(t - (.12 if ls else 0))
    if s <= .01: return
    c2 = c.resize((max(1, int(c.width * s)), max(1, int(c.height * s))))
    im.paste(c2, (540 - c2.width // 2, int(cy - c2.height / 2)))


def draw_meme_preview(img_path, top, bottom, out, label=""):
    v = {"_img": Image.open(img_path).convert("RGB"), "top": top, "bottom": bottom, "label": label}
    frame(dict(v, type="meme"), 1.0, 1.0, zoom=False).resize((540, 960)).save(out)


SCENES = {"caption": s_caption, "big": s_big, "person": s_person, "duo": s_duo, "stat": s_stat,
          "list": s_list, "bars": s_bars, "compound": s_compound, "ticker": s_ticker,
          "comment": s_comment, "meme": s_meme}


def frame(v, t, dur, zoom=True):
    im = Image.new("RGB", (W, H), WHITE)
    d = ImageDraw.Draw(im)
    SCENES.get(v.get("type"), s_caption)(d, im, t, dur, v if v.get("type") in SCENES else {"words": v.get("words", "")})
    if zoom and dur > 0:  # slow push-in keeps still scenes from feeling static
        z = 1 + 0.035 * min(1, t / max(dur, 0.1))
        cw, ch = int(W / z), int(H / z)
        im = im.crop(((W - cw) // 2, (H - ch) // 2, (W - cw) // 2 + cw, (H - ch) // 2 + ch)).resize((W, H), Image.BILINEAR)
    return im
