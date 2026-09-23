import hashlib
import os
import time

import edge_tts


AUDIO_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "audio_cache",
)

# Cached speech is kept for 24 hours before it becomes eligible for cleanup.
AUDIO_CACHE_TTL = 24 * 60 * 60

VOICE_MAP = {
    "en": "en-US-AriaNeural",
    "hi": "hi-IN-SwaraNeural",
    "es": "es-ES-ElviraNeural",
    "fr": "fr-FR-DeniseNeural",
    "de": "de-DE-KatjaNeural",
    "ja": "ja-JP-NanamiNeural",
    "zh": "zh-CN-XiaoxiaoNeural",
    "ko": "ko-KR-SunHiNeural",
    "pt": "pt-BR-FranciscaNeural",
    "ar": "ar-SA-ZariyahNeural",
    "ru": "ru-RU-SvetlanaNeural",
    "it": "it-IT-ElsaNeural",
}


def _cache_filename(text: str, voice: str) -> str:
    """Return a deterministic filename for a text/voice combination."""
    cache_key = f"{voice}:{text}".encode("utf-8")
    content_hash = hashlib.sha256(cache_key).hexdigest()
    return f"{content_hash}.mp3"


def cleanup_expired_audio() -> None:
    """Remove cached audio files that have exceeded the configured TTL."""
    if not os.path.isdir(AUDIO_DIR):
        return

    cutoff = time.time() - AUDIO_CACHE_TTL

    for filename in os.listdir(AUDIO_DIR):
        if not filename.endswith(".mp3"):
            continue

        filepath = os.path.join(AUDIO_DIR, filename)

        try:
            if os.path.isfile(filepath) and os.path.getmtime(filepath) < cutoff:
                os.remove(filepath)
        except FileNotFoundError:
            # The file may have been removed between listing and cleanup.
            pass


async def generate_speech(text: str, language: str = "en") -> str:
    """Generate or retrieve cached speech audio for the given text and language."""
    voice = VOICE_MAP.get(language, "en-US-AriaNeural")

    os.makedirs(AUDIO_DIR, exist_ok=True)
    cleanup_expired_audio()

    filename = _cache_filename(text, voice)
    filepath = os.path.join(AUDIO_DIR, filename)

    if os.path.isfile(filepath):
        return filepath

    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(filepath)

    return filepath
