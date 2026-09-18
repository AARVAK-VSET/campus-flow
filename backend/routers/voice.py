from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from backend.services.llm import conversational_form_filler
from backend.services.tts import generate_speech
import os

router = APIRouter(prefix="/api/voice", tags=["Voice"])

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
    result = await conversational_form_filler(request.current_data, request.user_input, request.context)
    
    # 2. Generate audio for the next question
    audio_path = await generate_speech(result["next_question"])
    audio_filename = os.path.basename(audio_path)
    audio_url = f"/audio/{audio_filename}"
    
    return {
        "updated_data": result.get("updated_data", request.current_data),
        "next_question": result.get("next_question", ""),
        "is_complete": result.get("is_complete", False),
        "is_confirmed": result.get("is_confirmed", False),
        "audio_url": audio_url
    }
