"""Step 3: voice each line. ElevenLabs (better) or Kokoro (free, local)."""
import os, subprocess, tempfile

import numpy as np
import requests
import soundfile as sf

SR = 24000
GAP = 0.16  # breath between lines, seconds


def _decode_to_array(mp3_bytes: bytes):
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        f.write(mp3_bytes); src = f.name
    out = src.replace(".mp3", ".wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-ac", "1", "-ar", str(SR), out], check=True)
    a, _ = sf.read(out, dtype="float32")
    os.remove(src); os.remove(out)
    return a


def _eleven(cfg, text, prev, nxt):
    key = os.getenv("ELEVENLABS_API_KEY")
    if not key:
        raise SystemExit("Missing ELEVENLABS_API_KEY in .env (or set voice.provider = \"kokoro\" in config.toml).")
    v = cfg["voice"]
    r = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{v['elevenlabs_voice_id']}?output_format=mp3_44100_128",
        headers={"xi-api-key": key, "Content-Type": "application/json"},
        json={"text": text, "model_id": v["elevenlabs_model"], "previous_text": prev, "next_text": nxt,
              "voice_settings": {"stability": 0.45, "similarity_boost": 0.8, "style": 0.3,
                                 "speed": min(1.2, max(0.7, v.get("speed", 1.0)))}},
        timeout=120)
    if r.status_code != 200:
        raise SystemExit(f"ElevenLabs error {r.status_code}: {r.text[:300]}")
    return _decode_to_array(r.content)


_kokoro = None
def _kokoro_say(cfg, text):
    global _kokoro
    from kokoro_onnx import Kokoro
    if _kokoro is None:
        m = cfg["root"] / "models"
        if not (m / "kokoro-v1.0.onnx").exists():
            raise SystemExit("Kokoro model missing. Run: python setup_models.py")
        _kokoro = Kokoro(str(m / "kokoro-v1.0.onnx"), str(m / "voices-v1.0.bin"))
    a, sr = _kokoro.create(text, voice=cfg["voice"]["kokoro_voice"], speed=cfg["voice"].get("speed", 1.1), lang="en-us")
    return a.astype("float32")


def _trim(a):
    nz = np.where(np.abs(a) > 0.01)[0]
    if len(nz) == 0:
        return a
    return a[max(0, nz[0] - 600): nz[-1] + 1200]


def voice_script(cfg, script: dict, out_wav):
    """Adds 'dur' (seconds) to each line and writes one combined wav."""
    lines, chunks = script["lines"], []
    for i, ln in enumerate(lines):
        prev = lines[i - 1]["text"] if i else ""
        nxt = lines[i + 1]["text"] if i + 1 < len(lines) else ""
        if cfg["voice"]["provider"] == "elevenlabs":
            a = _eleven(cfg, ln["text"], prev, nxt)
        else:
            a = _kokoro_say(cfg, ln["text"])
        a = np.concatenate([_trim(a), np.zeros(int(GAP * SR), dtype="float32")])
        ln["dur"] = round(len(a) / SR, 3)
        chunks.append(a)
        print(f"  voiced {i + 1}/{len(lines)}  {ln['dur']:.2f}s")
    sf.write(out_wav, np.concatenate(chunks), SR)
    return sum(l["dur"] for l in lines)
