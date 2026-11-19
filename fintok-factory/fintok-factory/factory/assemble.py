"""Step 6: render each scene to video, join them, and lay the voice, cut sounds and music under it."""
import os, random, subprocess
from pathlib import Path

import numpy as np
import soundfile as sf

from . import scenes

W, H = scenes.W, scenes.H


def _encode_scene(v, dur, nframes, fps, out):
    tmp = str(out).replace(".mp4", ".tmp.mp4")
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(fps), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
                          "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for f in range(nframes):
        p.stdin.write(scenes.frame(v, f / fps, dur).tobytes())
    p.stdin.close()
    if p.wait() != 0:
        raise RuntimeError(f"ffmpeg failed on {out}")
    os.replace(tmp, out)


def render(cfg, script, voice_wav, run_dir: Path):
    fps = cfg["video"]["fps"]
    parts_dir = run_dir / "scenes"; parts_dir.mkdir(exist_ok=True)
    lines = script["lines"]
    starts = np.cumsum([0] + [l["dur"] for l in lines])
    parts = []
    for i, ln in enumerate(lines):
        v = scenes.prepare(dict(ln["visual"]))
        f0, f1 = round(starts[i] * fps), round(starts[i + 1] * fps)
        out = parts_dir / f"s{i:02d}.mp4"
        _encode_scene(v, ln["dur"], f1 - f0, fps, out)
        parts.append(out)
        print(f"  scene {i + 1}/{len(lines)} ({v.get('type')})")

    # audio: voice + soft pop on each cut
    voice, sr = sf.read(voice_wav, dtype="float32")
    t = np.arange(int(.07 * sr)) / sr
    blip = 0.10 * np.sin(2 * np.pi * (900 - 4000 * t) * t) * np.exp(-t * 60)
    for s in starts[:-1]:
        a = int(s * sr); seg = voice[a:a + len(blip)]
        voice[a:a + len(seg)] += blip[:len(seg)]
    mix = run_dir / "mix.wav"
    sf.write(mix, np.clip(voice, -1, 1), sr)

    lst = run_dir / "scenes.txt"
    lst.write_text("".join(f"file '{p.resolve().as_posix()}'\n" for p in parts))
    silent = run_dir / "video_only.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(silent)], check=True)

    final = run_dir / "video.mp4"
    music = sorted(p for p in (cfg["root"] / "assets" / "music").glob("*") if p.suffix.lower() in (".mp3", ".wav", ".m4a"))
    vol = cfg["video"].get("music_volume", 0)
    if music and vol > 0:
        track = random.choice(music)
        cmd = ["ffmpeg", "-v", "error", "-y", "-i", str(silent), "-i", str(mix), "-stream_loop", "-1", "-i", str(track),
               "-filter_complex", f"[2:a]volume={vol}[m];[1:a][m]amix=inputs=2:duration=first:normalize=0[a]",
               "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", str(final)]
    else:
        cmd = ["ffmpeg", "-v", "error", "-y", "-i", str(silent), "-i", str(mix), "-map", "0:v", "-map", "1:a",
               "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", str(final)]
    subprocess.run(cmd, check=True)
    silent.unlink(missing_ok=True)
    return final
