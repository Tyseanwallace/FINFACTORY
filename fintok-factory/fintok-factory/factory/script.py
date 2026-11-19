"""Step 2: write the script (spoken lines + a visual for each line), then fact check it."""
import datetime as dt

from . import llm
from .config import playbook

VISUALS = """Every line gets exactly one "visual". Allowed visual types:
- {"type":"caption","words":"2-5 key words from the line"}         # bold words on white. Use often.
- {"type":"big","words":"1-2 words or a number","color":"green|red|blue|black"}
- {"type":"person","name":"Jake","color":"green|blue|red|orange","tag":"AGE 20"}   # simple cartoon character
- {"type":"duo","left":"Jake","right":"Mike","title":"short text"}                # two characters side by side
- {"type":"stat","value":"$1,000","label":"short label"}
- {"type":"list","title":"short title","items":["max 3 short items"]}
- {"type":"bars","title":"short title","bars":[{"label":"Jake","value":24000,"display":"$24K"}]}   # 2-4 bars
- {"type":"compound","mode":"line|result","title":"short title","rate":0.08,"end_age":65,
   "people":[{"name":"Jake","monthly":200,"start_age":20,"stop_age":30,"color":"green"}]}
   # numbers are calculated by code, so use this for any investing-over-time math
- {"type":"ticker","symbol":"SPY","period":"1y|5y|10y|max","title":"short title"}   # real price chart pulled live
- {"type":"comment","user":"made_up_username","text":"a funny/relatable comment","stamp":"optional red stamp text"}
- {"type":"meme","idea":"what the joke/reaction is","label":"caption shown ABOVE the meme, e.g. 'me checking my balance' (or empty)","top":"text on the image or empty","bottom":"text on the image or empty"}
   # prefer "label" (caption above the image, like meme pages do); use top/bottom only for classic two-line memes
Rules: change the visual on every line. Use a meme every 3-4 lines, wherever a sarcastic reaction lands the point.
Never put a real person's name or a real company's logo in a visual. Characters are made up."""

SYSTEM = """You write scripts for a faceless finance TikTok channel. Your scripts get people to watch
to the end: a hook that creates tension in the first 2 seconds, one idea per line, short spoken
sentences, a concrete example with numbers, a twist or payoff, and an ending that loops or makes people
comment. You never give personal investment advice, never promise returns, and never invent facts."""


def write(cfg, topic: str, angle: str = "", hook: str = "", extra: str = ""):
    words_lo = int(cfg["video"]["min_seconds"] * 3.0)
    words_hi = int(cfg["video"]["max_seconds"] * 2.9)
    prompt = f"""Today is {dt.date.today().isoformat()}.
Channel: {cfg['channel']['name']} - {cfg['channel']['niche']}. Voice: {cfg['channel']['voice_style']}.
Topic: {topic}
{('Angle: ' + angle) if angle else ''}
{('Suggested hook: ' + hook) if hook else ''}
{extra}

Channel playbook (follow it):
{playbook()}

{VISUALS}

Length: {words_lo}-{words_hi} spoken words total (needs to run at least {cfg['video']['min_seconds']} seconds).
Write numbers the way they should be SAID in "text" (e.g. "two hundred dollars"), but use digits in visuals.
Use web search to check any current facts, rates or figures you include.

Return ONLY JSON:
{{"title": "internal title",
  "lines": [{{"text": "spoken line", "visual": {{...}}}}],
  "caption": "TikTok caption, under 150 characters, curiosity-driven, no hashtags",
  "hashtags": ["3-5 specific hashtags"],
  "claims": [{{"claim": "every factual claim or number", "source": "url or 'math' or 'common knowledge'"}}]
}}"""
    data, sources = llm.ask_json(cfg, SYSTEM, prompt, web_search=True)
    data["research_sources"] = sources
    return data


CHECK_SYSTEM = """You are a strict fact checker for finance videos. You check every claim with web
search, and you check for anything that breaks TikTok rules or sounds like personal financial advice."""


def fact_check(cfg, script: dict):
    import json
    prompt = f"""Check this script. Search to verify every number and factual claim that isn't pure math.
Also flag: personal advice ("you should buy X"), guaranteed returns, misleading framing, real people or
brands shown in visuals, and anything against the playbook below.

{playbook()}

SCRIPT JSON:
{json.dumps(script, indent=1)}

Return ONLY JSON:
{{"passed": true/false,
  "issues": [{{"line": index or null, "problem": "...", "fix": "..."}}],
  "fixed_lines": null or the full corrected "lines" array (same format) if anything needed fixing}}"""
    data, sources = llm.ask_json(cfg, CHECK_SYSTEM, prompt, web_search=True)
    if data.get("fixed_lines"):
        script["lines"] = data["fixed_lines"]
    script["fact_check"] = {"passed": data.get("passed"), "issues": data.get("issues", []), "sources": sources}
    return script


def extend(cfg, script: dict, seconds: float):
    """Video came out too short: add lines (before the ending) worth about `seconds` of speech."""
    import json
    prompt = f"""This finance TikTok script runs {seconds:.0f} seconds too short to qualify for TikTok
Creator Rewards (videos must be over 1 minute). Add 1-3 new lines (about {int(seconds * 3)} spoken words)
that add real value - an extra example, a common mistake, or a quick tip - placed before the final 2 lines.
Don't pad or repeat. Keep the same style.

{VISUALS}

SCRIPT JSON:
{json.dumps(script["lines"], indent=1)}

Return ONLY JSON: {{"lines": [the full updated lines array]}}"""
    data, _ = llm.ask_json(cfg, SYSTEM, prompt)
    script["lines"] = data["lines"]
    return script
