# FinTok Factory - instructions for Claude Code

## What this is
A production line that turns a topic (or this week's trending finance news) into a finished,
TikTok-ready vertical video: research -> script -> fact check -> memes -> voice -> render -> caption.
Owner: Ty, a finance student. The channel teaches personal finance and investing to people in
their late teens and 20s. Ty is not a developer. Explain things in plain language, keep him in the loop
on anything that costs money, and prefer simple, working solutions over clever ones.

## How it works
- `make_video.py` - the command line entry point (see its docstring for commands).
- `config.toml` - all settings (voice provider, lengths, review steps). Keys live in `.env`.
- `PLAYBOOK.md` - content and compliance rules. It is inserted into every AI prompt. Treat it as
  the source of truth for what a good, rule-following video is.
- `factory/trends.py` - Claude + web search finds timely topic ideas.
- `factory/script.py` - writes the script as JSON (spoken line + one visual per line), fact checks
  it with web search, and extends it if the video comes out under 1 minute.
- `factory/memes.py` - picks Imgflip meme templates, lets Ty approve/swap, remembers approved ones
  in `library/approved_memes.json`.
- `factory/voice.py` - ElevenLabs (default) or Kokoro (free, local) voice, one clip per line.
- `factory/scenes.py` - draws every visual type with Pillow at 1080x1920.
- `factory/assemble.py` - encodes one file per scene, joins them, mixes voice + cut sounds + music.
- `factory/package.py` - writes caption.txt, POST_CHECKLIST.txt, sources.txt and script.json.
- Every run gets its own folder in `output/`.

## First-time setup (do this with Ty)
1. Check Python 3.11+ and ffmpeg are installed (`ffmpeg -version`). Install ffmpeg if missing
   (Mac: `brew install ffmpeg`, Windows: `winget install ffmpeg`).
2. Make a virtual environment and `pip install -r requirements.txt`.
3. Copy `.env.example` to `.env`. Ty pastes his Anthropic API key (console.anthropic.com) and his
   ElevenLabs API key (elevenlabs.io -> profile -> API keys). Never print or commit keys.
4. Web search must be enabled for his Anthropic organization in the Console (Settings -> Privacy /
   features). If the research step errors about web search, walk him through enabling it.
5. Optional free voice: `python setup_models.py`, then set `voice.provider = "kokoro"`.
6. Smoke test without any API cost: `python make_video.py make --script examples/compound_interest.json`
   (needs the Kokoro model, or ElevenLabs credits).
7. Then a real run: `python make_video.py make --trending`.

## Rules when changing this project
- Never remove or weaken the compliance pieces: fact check step, disclaimers, AI-label and disclosure
  reminders, the ElevenLabs free-plan warnings, the 1-minute minimum. If Ty asks to, explain the risk first.
- Keep all numbers in charts either computed by code (compound, ticker) or fact-checked.
- No brand logos, and no real person shown endorsing anything. Prefer meme templates without celebrities.
- After any change to rendering, render one example and look at a few frames before saying it works.
- Keep costs visible: if a change adds a paid API or raises usage, say roughly what it costs.

## Roadmap (build these with Ty, roughly in this order)
1. **Review screen:** replace the terminal meme/script review with a small local web page (one page,
   approve/swap buttons, edit text inline).
2. **Better audio:** a folder of royalty-free music (e.g. YouTube Audio Library, Pixabay Music - check
   each track's licence) and a few whoosh/pop sound effects.
3. **Word-level captions:** use ElevenLabs' `/with-timestamps` endpoint to time key words exactly and
   flash them on screen as they're spoken.
4. **More visual types:** "receipt" breakdowns, calendar countdowns, map/state comparisons, stock-photo
   b-roll from Pexels' free API for real-world scenes.
5. **Scheduling:** run `make --trending --batch 3` on a schedule (cron / Task Scheduler) so drafts are
   waiting for review each morning.
6. **Auto-posting:** TikTok's Content Posting API needs a developer app and an audit; until then, use
   TikTok's own scheduler or a tool like Metricool/Buffer. Also export to YouTube Shorts and Reels.
7. **Analytics loop:** pull performance automatically instead of the manual `library/performance.csv`.
8. **Voice clone:** when Ty upgrades ElevenLabs, clone his voice and put the voice ID in config.toml.
