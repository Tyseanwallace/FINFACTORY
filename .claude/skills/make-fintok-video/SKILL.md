---
name: make-fintok-video
description: Make a finished FinTok video end to end (trending topic -> sarcastic script -> memes -> voice -> render -> frame check -> caption/checklist -> commit). Use when Ty asks for a new video, a remake in a different style, or a re-render. Works with or without an Anthropic API key.
---

# Make a FinTok video

Project lives in `fintok-factory/fintok-factory/`. Read its `CLAUDE.md` and `PLAYBOOK.md` first;
PLAYBOOK is the source of truth for tone and compliance. Run Python from `.venv/bin/python`
(create it with `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt` if missing).

## 1. Pick the topic
- Search this week's personal-finance news (WebSearch). Good pegs: Fed/NY Fed reports, IRS limit
  changes, tax deadlines, holiday spending, viral money debates. Avoid stock picks, crypto hype, politics.
- Confirm every number against a primary source (newyorkfed.org, federalreserve.gov, irs.gov).

## 2. Write the script (no API key needed)
- Save to `scripts/<topic>.json`, same format as `examples/compound_interest.json`.
- Tone (PLAYBOOK §2): sarcastic, deadpan, informative. Every joke carries a real number. Punch at
  banks/systems/situations, never at viewers. Made-up characters ("Maya, 24").
- Short lines, new visual every line. 240-260 spoken words = ~85-93 s (must stay 62-95 s).
- Any math (payoff, compound growth) is computed in Python first, never guessed. Put it in `claims`.
- Memes every 3-4 lines: `{"type":"meme","template_id":"<imgflip id>","label":"caption above image"}`.
  Proven celebrity-free templates: 55311130 This Is Fine, 163573 Imagination Spongebob,
  148909805 Monkey Puppet, 4087833 Waiting Skeleton, 247375501 Buff Doge vs Cheems,
  155067746 Surprised Pikachu. Avoid multi-panel templates whose text boxes sit on blank halves
  (e.g. Tuxedo Pooh) and anything with real people. `library/approved_memes.json` lists past picks.
- Add `research_sources` (title + url) and a `fact_check` block noting what was checked by hand.

## 3. Preview memes before spending voice credits
Render one frame per meme scene with `scenes.prepare` + `scenes.frame` and look at them.

## 4. Voice + render
```
ELEVENLABS_API_KEY=proxy-injected .venv/bin/python make_video.py make --script scripts/<topic>.json
```
- In cloud sessions the proxy injects the real ElevenLabs key; the env var is only a placeholder.
  On Ty's laptop the key is in `.env`. Free fallback: `voice.provider = "kokoro"` + `python setup_models.py`.
- ~1,300 ElevenLabs characters per video. Say so before running.
- Ty's own voiceover: one clip per line (`01.m4a`...) -> use clip lengths as each line's `dur`.

## 5. Check frames (required)
Grab one frame per scene (75% into each line, using `dur` from `output/<run>/script.json`), tile them,
and look. Known past bugs: text running off-screen, tags overlapping names, meme text on blank areas.
To fix a render without paying for voice again, re-run only `assemble.render(cfg, script, voice.wav, run_dir)`.

## 6. Deliver
- Commit `video.mp4`, `caption.txt`, `POST_CHECKLIST.txt`, `sources.txt`, `script.json` and the script.
  Intermediates (scene clips, wav) are gitignored. Push to the session branch and send the files to Ty.
- Remind him: AI-content label on, free ElevenLabs plan = don't monetize, watch it once before posting.

## Improving this skill
When something new works (a new visual, a better meme, a fixed bug), add it here in the same commit.
