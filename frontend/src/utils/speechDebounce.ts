/** Delay after TTS playback before the mic is armed, so speaker tail/echo is not transcribed. */
export const SPEECH_LISTEN_DEBOUNCE_MS = 600;

/** Drop recognition results below this confidence (room noise / echo). */
export const MIN_SPEECH_CONFIDENCE = 0.5;

export function shouldAcceptTranscript(
  transcript: string,
  confidence?: number
): boolean {
  if (!transcript || !transcript.trim()) {
    return false;
  }
  if (typeof confidence === "number" && !Number.isNaN(confidence) && confidence < MIN_SPEECH_CONFIDENCE) {
    return false;
  }
  return true;
}

export function scheduleListenAfterPlayback(
  startListening: () => void,
  delayMs: number = SPEECH_LISTEN_DEBOUNCE_MS
): ReturnType<typeof setTimeout> {
  return setTimeout(startListening, delayMs);
}
