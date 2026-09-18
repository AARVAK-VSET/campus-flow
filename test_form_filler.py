import sys
import os
import asyncio
from dotenv import load_dotenv

# Ensure backend folder is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.services.llm import conversational_form_filler

async def test():
    print("Testing conversational_form_filler directly...")
    data = {}
    user_input = "Hello Arjun, I want to add a record."
    context = "medical"
    
    try:
        result = await conversational_form_filler(data, user_input, context)
        print("Result:", result)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    asyncio.run(test())
