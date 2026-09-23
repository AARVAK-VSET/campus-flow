from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from pydantic import BaseModel
from typing import Optional, Dict, Any
from backend.services.llm import (
    FORM_FIELDS,
    conversational_form_filler,
    required_fields_complete,
)
from backend.services.tts import cleanup_expired_audio
import os

router = APIRouter(prefix="/api/voice", tags=["Voice"])

AUDIO_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "audio_cache")


async def _generate_speech(text: str) -> str:
    from backend.services.tts import generate_speech

    return await generate_speech(text)


class VoiceProcessRequest(BaseModel):
    user_input: str
    current_data: Dict[str, Any]
    context: str = "medical"


@router.post("/process")
async def process_voice_turn(request: VoiceProcessRequest):
    """
    Arjun - Handles a single turn of conversation.
    """
    # 1. Process with LLM to get next question/updates
    if request.context not in FORM_FIELDS:
        raise HTTPException(status_code=400, detail="Unsupported voice form context")
    result = await conversational_form_filler(request.current_data, request.user_input, request.context)
    updated_data = result.get("updated_data", request.current_data)
    if not isinstance(updated_data, dict):
        updated_data = request.current_data
    fields_complete = required_fields_complete(updated_data, request.context)
    is_confirmed = bool(result.get("is_confirmed", False) and fields_complete)
    is_complete = bool(result.get("is_complete", False) and fields_complete)

    # 2. Generate audio for the next question
    next_question = result.get("next_question", "")
    audio_path = await _generate_speech(next_question)
    audio_filename = os.path.basename(audio_path)
    audio_url = f"/api/voice/audio/{audio_filename}"

    return {
        "updated_data": updated_data,
        "next_question": next_question,
        "is_complete": is_complete,
        "is_confirmed": is_confirmed,
        "audio_url": audio_url
    }


@router.get("/audio/{filename}", include_in_schema=False)
async def get_audio(filename: str):
    filepath = os.path.join(AUDIO_DIR, os.path.basename(filename))
    if not os.path.isfile(filepath):
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(
        filepath,
        media_type="audio/mpeg",
        # Sweeps any cache files past their 24h TTL once this response has
        # finished streaming. It does not delete `filepath` itself, so an
        # identical next request can still reuse the cached file (see
        # generate_speech()'s content-hash cache in services/tts.py).
        background=BackgroundTask(cleanup_expired_audio),
    )
