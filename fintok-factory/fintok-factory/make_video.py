"""FinTok Factory - topic in, finished TikTok out.

  python make_video.py ideas                      # find trending finance topics this week
  python make_video.py make --trending            # research trends, pick the best idea, make the video
  python make_video.py make --topic "why your 401k match is free money"
  python make_video.py make --trending --batch 3  # make 3 videos from this week's best ideas
  python make_video.py make --script examples/compound_interest.json   # render a ready-made script
  add --yes to skip the review steps (fully hands-off)
"""
import argparse, datetime as dt, json, re, sys

from factory import config


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:50] or "video"


def est_seconds(script):
    return sum(len(l["text"].split()) for l in script["lines"]) / 3.0


def review_script(script, run_dir):
    p = run_dir / "script_draft.json"
    while True:
        json.dump(script, open(p, "w", encoding="utf-8"), indent=1)
        print(f"\n--- SCRIPT: {script.get('title', '')}  (~{est_seconds(script):.0f}s) ---")
        for i, l in enumerate(script["lines"]):
            print(f"{i:>2}. {l['text']}\n      [{l['visual'].get('type')}] {json.dumps({k: v for k, v in l['visual'].items() if k != 'type'})[:90]}")
        fc = script.get("fact_check")
        if fc:
            print(f"\nFact check passed: {fc.get('passed')}")
            for iss in fc.get("issues", []): print(f"  - line {iss.get('line')}: {iss.get('problem')} -> {iss.get('fix')}")
        a = input("\n[Enter]=approve  e=I edited script_draft.json, reload  r=rewrite  q=quit: ").strip().lower()
        if a == "": return script, "ok"
        if a == "e": script = json.load(open(p, encoding="utf-8")); continue
        if a == "r": return script, "rewrite"
        if a == "q": sys.exit(0)


def make_one(cfg, topic=None, idea=None, script_path=None, auto=False):
    from factory import script as sc, voice, memes, assemble, package
    stamp = dt.datetime.now().strftime("%Y-%m-%d_%H%M")
    name = topic or (idea or {}).get("topic") or (script_path and script_path.stem) or "video"
    run_dir = cfg["root"] / "output" / f"{stamp}_{slug(name)}"
    run_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n=== {name} ===\nfolder: {run_dir}")

    if script_path:
        s = json.load(open(script_path, encoding="utf-8"))
    else:
        extra = ""
        while True:
            print("Writing script (with research)...")
            s = sc.write(cfg, topic or idea["topic"], (idea or {}).get("angle", ""), (idea or {}).get("hook", ""), extra)
            if est_seconds(s) < cfg["video"]["min_seconds"]:
                print("  script is short of 1 minute - extending")
                s = sc.write(cfg, topic or idea["topic"], (idea or {}).get("angle", ""), (idea or {}).get("hook", ""),
                             extra + f"\nThe last draft was too short (~{est_seconds(s):.0f}s). Add another example or beat so it runs {cfg['video']['min_seconds']}-80 seconds.")
            print("Fact checking...")
            s = sc.fact_check(cfg, s)
            if auto or not cfg["review"]["script"]:
                break
            s, status = review_script(s, run_dir)
            if status == "ok": break
            extra = "\nThe creator rejected the last draft. Take a clearly different approach."

    if any(l["visual"].get("type") == "meme" and not l["visual"].get("image") for l in s["lines"]):
        print("Picking memes...")
        if auto:
            cfg["review"]["memes"] = False
        s = memes.pick(cfg, s, run_dir)

    print("Voicing...")
    secs = voice.voice_script(cfg, s, run_dir / "voice.wav")
    print(f"  voiceover is {secs:.1f}s")
    if secs < cfg["video"]["min_seconds"] and not script_path:
        print("  under the minimum length - adding a beat and re-voicing")
        s = sc.extend(cfg, s, cfg["video"]["min_seconds"] - secs + 3)
        secs = voice.voice_script(cfg, s, run_dir / "voice.wav")
        print(f"  voiceover is now {secs:.1f}s")

    print("Rendering...")
    final = assemble.render(cfg, s, run_dir / "voice.wav", run_dir)
    package.write_post_files(cfg, s, run_dir, secs)
    print(f"\nDONE -> {final}\nCaption + checklist are in the same folder.")
    return final


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["ideas", "make"])
    ap.add_argument("--topic"); ap.add_argument("--script")
    ap.add_argument("--trending", action="store_true")
    ap.add_argument("--batch", type=int, default=1)
    ap.add_argument("--yes", action="store_true", help="skip all review steps")
    a = ap.parse_args()
    cfg = config.load()
    if a.yes:
        cfg["review"]["memes"] = False; cfg["review"]["script"] = False

    if a.cmd == "ideas" or a.trending:
        from factory import trends
        print("Researching what's trending in finance this week...")
        ideas, path = trends.find_ideas(cfg)
        for i, it in enumerate(ideas):
            print(f"\n{i}. {it['topic']}  (trend {it.get('trend_strength')}/5, evergreen {it.get('evergreen')}/5)\n   hook: {it['hook']}\n   why now: {it['why_now']}")
        print(f"\nSaved to {path}")
        if a.cmd == "ideas":
            return
        if a.yes or a.batch > 1:
            picks = ideas[:a.batch]
        else:
            nums = input("\nWhich idea(s)? e.g. 0 or 0,2: ").strip() or "0"
            picks = [ideas[int(n)] for n in nums.split(",")]
        for idea in picks:
            make_one(cfg, idea=idea, auto=a.yes)
    elif a.script:
        from pathlib import Path
        make_one(cfg, script_path=Path(a.script), auto=True)
    elif a.topic:
        for _ in range(a.batch):
            make_one(cfg, topic=a.topic, auto=a.yes)
    else:
        ap.error("make needs --topic, --trending or --script")


if __name__ == "__main__":
    main()
