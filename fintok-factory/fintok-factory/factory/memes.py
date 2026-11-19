"""Step 4: find a meme template for every meme beat, with a quick approve/swap review.

Templates come from Imgflip's public list of popular meme templates. Every template you approve is
saved to library/approved_memes.json and preferred next time, so your meme library builds itself.
"""
import json, time, webbrowser
from pathlib import Path

import requests

from . import llm

IMGFLIP = "https://api.imgflip.com/get_memes"


def templates(cfg):
    lib = cfg["root"] / "library"; lib.mkdir(exist_ok=True)
    cache = lib / "imgflip_templates.json"
    if cache.exists() and time.time() - cache.stat().st_mtime < 7 * 86400:
        return json.load(open(cache, encoding="utf-8"))
    data = requests.get(IMGFLIP, timeout=30).json()["data"]["memes"]
    json.dump(data, open(cache, "w", encoding="utf-8"))
    return data


def approved(cfg):
    p = cfg["root"] / "library" / "approved_memes.json"
    return json.load(open(p, encoding="utf-8")) if p.exists() else []


def _save_approved(cfg, entry):
    p = cfg["root"] / "library" / "approved_memes.json"
    items = approved(cfg)
    items.append(entry)
    json.dump(items, open(p, "w", encoding="utf-8"), indent=1)


def template_image(cfg, t) -> Path:
    d = cfg["root"] / "library" / "templates"; d.mkdir(parents=True, exist_ok=True)
    ext = Path(t["url"]).suffix or ".jpg"
    p = d / f"{t['id']}{ext}"
    if not p.exists():
        p.write_bytes(requests.get(t["url"], timeout=30).content)
    return p


def pick(cfg, script: dict, run_dir: Path):
    beats = [(i, ln) for i, ln in enumerate(script["lines"]) if ln["visual"].get("type") == "meme"]
    if not beats:
        return script
    temps = templates(cfg)
    by_id = {t["id"]: t for t in temps}
    # memes that already name a template (e.g. hand-written scripts) just need the image downloaded
    for i, ln in beats:
        v = ln["visual"]
        if v.get("template_id") in by_id and not v.get("image"):
            t = by_id[v["template_id"]]
            v.update({"template_name": t["name"], "image": str(template_image(cfg, t))})
            _save_approved(cfg, {"id": t["id"], "name": t["name"], "idea": v.get("idea", ""),
                                 "label": v.get("label", ""), "top": v.get("top", ""), "bottom": v.get("bottom", "")})
    beats = [(i, ln) for i, ln in beats if not ln["visual"].get("image")]
    if not beats:
        return script
    liked = approved(cfg)
    menu = "\n".join(f'{t["id"]}: {t["name"]} (text boxes: {t["box_count"]})' for t in temps)
    prompt = f"""Pick meme templates for these beats in a finance TikTok.
Previously approved picks (the creator liked these, favour them when they fit):
{json.dumps(liked[-30:], indent=0)}

Available templates:
{menu}

Beats:
{json.dumps([{"line": i, "spoken": ln["text"], **ln["visual"]} for i, ln in beats], indent=1)}

For each beat return the 3 best template ids, best first, plus a "label" (caption shown above the image,
max 10 words, the main joke) and optional short top/bottom text on the image (max 6 words each, usually
empty when there is a label). Prefer templates without famous people (cartoons,
animals, stock-photo style). Never write text that makes a real person seem to endorse anything. Return ONLY JSON:
{{"picks": [{{"line": 0, "options": [{{"id": "...", "label": "...", "top": "...", "bottom": "..."}}]}}]}}"""
    data, _ = llm.ask_json(cfg, "You are a meme editor with great comedic timing.", prompt)
    picks = {p["line"]: [o for o in p["options"] if o["id"] in by_id] for p in data["picks"]}

    from .scenes import draw_meme_preview
    for i, ln in beats:
        opts = picks.get(i, [])
        choice = None
        for o in opts:
            t = by_id[o["id"]]
            img = template_image(cfg, t)
            if not cfg["review"]["memes"]:
                choice = (t, o, img); break
            prev = run_dir / f"meme_preview_line{i}.png"
            draw_meme_preview(img, o.get("top", ""), o.get("bottom", ""), prev, o.get("label", ""))
            webbrowser.open(prev.resolve().as_uri())
            print(f'\nLine {i}: "{ln["text"]}"\n  Meme: {t["name"]}  | top: "{o["top"]}"  bottom: "{o["bottom"]}"')
            a = input("  [Enter]=use it  n=next option  e=edit text  c=caption card instead: ").strip().lower()
            if a == "e":
                o["top"] = input("  top text: "); o["bottom"] = input("  bottom text: "); a = ""
            if a == "c":
                break
            if a == "":
                choice = (t, o, img); break
        if choice:
            t, o, img = choice
            ln["visual"].update({"template_id": t["id"], "template_name": t["name"], "image": str(img),
                                 "label": o.get("label", ln["visual"].get("label", "")),
                                 "top": o.get("top", ""), "bottom": o.get("bottom", "")})
            _save_approved(cfg, {"id": t["id"], "name": t["name"], "idea": ln["visual"].get("idea", ""),
                                 "top": o["top"], "bottom": o["bottom"]})
        else:  # no meme approved -> fall back to a caption card
            ln["visual"] = {"type": "caption", "words": " ".join(ln["text"].split()[:5])}
    return script
