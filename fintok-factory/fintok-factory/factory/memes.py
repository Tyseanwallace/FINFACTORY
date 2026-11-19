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
    liked = approved(cfg)
    menu = "\n".join(f'{t["id"]}: {t["name"]} (text boxes: {t["box_count"]})' for t in temps)
    prompt = f"""Pick meme templates for these beats in a finance TikTok.
Previously approved picks (the creator liked these, favour them when they fit):
{json.dumps(liked[-30:], indent=0)}

Available templates:
{menu}

Beats:
{json.dumps([{"line": i, "spoken": ln["text"], **ln["visual"]} for i, ln in beats], indent=1)}

For each beat return the 3 best template ids, best first, and short top/bottom text (max 6 words each,
can be empty) that works on that template. Prefer templates without famous people (cartoons,
animals, stock-photo style). Never write text that makes a real person seem to endorse anything. Return ONLY JSON:
{{"picks": [{{"line": 0, "options": [{{"id": "...", "top": "...", "bottom": "..."}}]}}]}}"""
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
            draw_meme_preview(img, o["top"], o["bottom"], prev)
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
                                 "top": o["top"], "bottom": o["bottom"]})
            _save_approved(cfg, {"id": t["id"], "name": t["name"], "idea": ln["visual"].get("idea", ""),
                                 "top": o["top"], "bottom": o["bottom"]})
        else:  # no meme approved -> fall back to a caption card
            ln["visual"] = {"type": "caption", "words": " ".join(ln["text"].split()[:5])}
    return script
