import asyncio
import os
import sys

# Ensure backend folder is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.services.tts import generate_speech

async def test():
    print("Testing generate_speech directly...")
    text = "Namaste! I'm Arjun, and I'm here to help you create a medical record. To start, could you please provide the student's name?"
    try:
        path = await generate_speech(text)
        print("Audio saved to:", path)
        print("File size:", os.path.getsize(path), "bytes")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    asyncio.run(test())
