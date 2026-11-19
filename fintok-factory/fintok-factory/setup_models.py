"""Downloads the free Kokoro voice model (~350 MB) into models/. Only needed if voice.provider = "kokoro"."""
from pathlib import Path

import requests

BASE = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"
FILES = ["kokoro-v1.0.onnx", "voices-v1.0.bin"]
dest = Path(__file__).resolve().parent / "models"
dest.mkdir(exist_ok=True)
for f in FILES:
    p = dest / f
    if p.exists():
        print("already have", f); continue
    print("downloading", f, "...")
    with requests.get(BASE + f, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(p.with_suffix(".part"), "wb") as out:
            for chunk in r.iter_content(1 << 20): out.write(chunk)
    p.with_suffix(".part").rename(p)
print("Kokoro voice ready.")
