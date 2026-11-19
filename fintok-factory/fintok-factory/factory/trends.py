"""Step 1: find finance topics that are getting attention right now."""
import csv, datetime as dt, json

from . import llm
from .config import playbook

SYSTEM = """You are the research lead for a finance TikTok channel. You find topics that are
getting attention THIS WEEK and that the channel can explain in 60-90 seconds better than anyone.
Use web search. Prefer: money news people are confused about, viral money debates, upcoming dated
events (Fed meetings, earnings, tax deadlines, paycheck/holiday spending seasons), and evergreen
topics with a fresh news hook. Avoid: stock picks, crypto pumps, get-rich-quick, anything that needs
a license to advise on, politics framed as partisan."""


def past_winners(cfg, n=5):
    """Top videos you logged in library/performance.csv, so new ideas lean toward what works."""
    path = cfg["root"] / "library" / "performance.csv"
    if not path.exists():
        return []
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    def score(r):
        try: return float(r.get("avg_watch_pct") or 0) * 2 + float(r.get("views") or 0) / 10000
        except ValueError: return 0
    return [r.get("title", "") for r in sorted(rows, key=score, reverse=True)[:n]]


def find_ideas(cfg, count=8):
    today = dt.date.today().isoformat()
    winners = past_winners(cfg)
    prompt = f"""Today is {today}. Channel: {cfg['channel']['name']}. Niche: {cfg['channel']['niche']}.
Audience country: {cfg['channel']['audience_country']}.
{('Our best performing past videos: ' + '; '.join(winners)) if winners else ''}

Channel playbook (follow it):
{playbook()}

Search the web, then return ONLY JSON:
{{"ideas": [{{
  "topic": "short topic",
  "angle": "the specific take or story that makes it interesting",
  "hook": "first sentence spoken, under 12 words, creates curiosity or tension",
  "why_now": "what is happening this week that makes this timely",
  "evergreen": 1-5,
  "trend_strength": 1-5,
  "risk_notes": "anything that could break TikTok rules or need careful wording"
}}]}}
Give {count} ideas, best first."""
    data, sources = llm.ask_json(cfg, SYSTEM, prompt, web_search=True)
    ideas = data["ideas"]
    out = cfg["root"] / "output" / f"ideas_{today}.json"
    out.parent.mkdir(exist_ok=True)
    json.dump({"ideas": ideas, "sources": sources}, open(out, "w", encoding="utf-8"), indent=2)
    return ideas, out
