"""Step 7: write the caption, hashtags and a posting checklist next to the video."""
import json


def write_post_files(cfg, script, run_dir, seconds):
    tags = list(dict.fromkeys(script.get("hashtags", []) + cfg["posting"]["base_hashtags"]))[:6]
    tags = [t if t.startswith("#") else "#" + t for t in tags]
    lines = [script.get("caption", "").strip(), "", "Not financial advice. For education only."]
    eleven_free = cfg["voice"]["provider"] == "elevenlabs" and cfg["voice"].get("elevenlabs_plan") == "free"
    if eleven_free:
        lines.append("Voice by ElevenLabs.")
    lines += ["", " ".join(tags)]
    (run_dir / "caption.txt").write_text("\n".join(lines), encoding="utf-8")

    checks = [
        f"[ ] Length is {seconds:.0f}s " + ("(OK, over 1 minute)" if seconds >= 60 else "(UNDER 1 MIN - won't earn Creator Rewards)"),
        "[ ] Watched it once start to finish - every number and meme looks right",
        "[ ] Turn ON 'AI-generated content' in TikTok's post settings (AI voice = realistic AI audio)",
        "[ ] If the video promotes ANY product, brand or your own business: turn on 'Content disclosure'",
        "[ ] Pick a trending sound only if it's commercially cleared (or keep original audio)",
        "[ ] Pin a comment that asks a question to start replies",
        "[ ] After 48h, log views + avg watch % in library/performance.csv",
    ]
    if eleven_free:
        checks.insert(1, "[ ] FREE ElevenLabs plan: don't monetize this video (no Creator Rewards, sponsors or affiliate links)")
    fc = script.get("fact_check", {})
    if fc and not fc.get("passed", True):
        checks.insert(0, "[ ] FACT CHECK FLAGGED ISSUES - read fact_check in script.json before posting")
    (run_dir / "POST_CHECKLIST.txt").write_text("\n".join(checks), encoding="utf-8")

    srcs = script.get("research_sources", []) + fc.get("sources", [])
    seen, out = set(), []
    for s in srcs:
        if s["url"] not in seen:
            seen.add(s["url"]); out.append(f"{s['title']}\n  {s['url']}")
    (run_dir / "sources.txt").write_text("\n".join(out) or "(no web sources)", encoding="utf-8")
    json.dump({k: v for k, v in script.items()}, open(run_dir / "script.json", "w", encoding="utf-8"), indent=1, default=str)
