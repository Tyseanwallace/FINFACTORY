"""ElevenLabs SDK client. The key comes from ELEVENLABS_API_KEY (set in .env), never from code."""
import os

from elevenlabs.client import ElevenLabs

from . import config  # noqa: F401  (loads .env)


def client() -> ElevenLabs:
    return ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
