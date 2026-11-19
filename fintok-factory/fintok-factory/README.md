# FinTok Factory

Type a topic (or let it find this week's trending finance topics) and get back a finished TikTok:
script, fact check, memes, AI voiceover, animated visuals, caption, hashtags and a posting checklist.

## Easiest way to start
1. Unzip this folder somewhere on your laptop.
2. Open a terminal in the folder and run `claude` (Claude Code).
3. Say: **"Read CLAUDE.md and help me set this up."** It will walk you through installing everything
   and adding your API keys.

## What you need
- Anthropic API key (console.anthropic.com). Scripts cost a few cents per video.
- ElevenLabs API key (elevenlabs.io). The free plan works for testing, but **don't monetize free-plan videos**.
  Or use the free Kokoro voice (`python setup_models.py`, then `provider = "kokoro"` in config.toml).
- ffmpeg and Python 3.11+ (Claude Code can install these).

## Everyday use
```
python make_video.py ideas                       # see what's trending this week
python make_video.py make --trending             # pick an idea, review the script and memes, get a video
python make_video.py make --topic "is a Roth IRA worth it at 20"
python make_video.py make --trending --batch 3 --yes   # 3 videos, no review stops
```
Each video lands in `output/<date>_<topic>/` with:
- `video.mp4` - upload this
- `caption.txt` - paste as the caption
- `POST_CHECKLIST.txt` - go through it before posting (AI label, disclosure, length)
- `sources.txt` - where the facts came from

## Make it yours
- `config.toml` - channel name, voice, video length, whether to review before rendering
- `PLAYBOOK.md` - the rules every script follows (hooks, topics, what's off-limits). Edit it and every
  future video changes.
- `assets/music/` - drop royalty-free music here and it gets mixed in quietly
- `library/performance.csv` - log how videos do; new ideas lean toward your winners
