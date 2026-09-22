"""Regression checks for voice-assistant listen debounce (issue #17)."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
ASSISTANT = (ROOT / "frontend" / "src" / "components" / "VoiceAssistant.tsx").read_text(
    encoding="utf-8"
)
DEBOUNCE = (ROOT / "frontend" / "src" / "utils" / "speechDebounce.ts").read_text(
    encoding="utf-8"
)


def test_debounce_delay_is_at_least_400ms():
    match = re.search(r"SPEECH_LISTEN_DEBOUNCE_MS\s*=\s*(\d+)", DEBOUNCE)
    assert match, "SPEECH_LISTEN_DEBOUNCE_MS must be defined"
    assert int(match.group(1)) >= 400


def test_playback_end_schedules_listen_instead_of_starting_immediately():
    assert "scheduleListenAfterPlayback" in ASSISTANT
    assert "SPEECH_LISTEN_DEBOUNCE_MS" in ASSISTANT
    # The old feedback loop: audio.onended immediately called startListening().
    assert not re.search(
        r"audio\.onended\s*=\s*\(\)\s*=>\s*\{\s*setIsSpeaking\(false\);\s*startListening\(\)",
        ASSISTANT,
    )


def test_low_confidence_transcripts_are_rejected():
    assert "shouldAcceptTranscript" in DEBOUNCE
    assert "MIN_SPEECH_CONFIDENCE" in DEBOUNCE
    assert "shouldAcceptTranscript" in ASSISTANT
