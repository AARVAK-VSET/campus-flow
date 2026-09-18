import os
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Explicitly load .env from the backend directory relative to this file
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

# Debug logging for the API key (masking sensitive parts)
api_key = os.getenv("OPENROUTER_API_KEY", "")
print(f"DEBUG: OPENROUTER_API_KEY is {'set' if api_key else 'NOT SET'}. Key prefix: {api_key[:10]}...")

client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

MODEL = "google/gemini-2.0-flash-001"


async def _ask_llm(system_prompt: str, user_prompt: str) -> str:
    try:
        response = await client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=1024,
            temperature=0.7,
        )
        return response.choices[0].message.content or "No insights available."
    except Exception as e:
        return f"AI analysis unavailable: {str(e)}"


async def get_medical_insights(data: dict) -> str:
    system = "You are a campus health analytics AI. Analyze medical records data and provide actionable insights, predictions for next month, and risk warnings. Be concise and use bullet points."
    user = f"""Analyze this medical records data:
- Total records: {data.get('total', 0)}
- Top issues: {data.get('by_issue', [])}
- Severity breakdown: {data.get('by_severity', [])}
- Daily visit trends: {data.get('daily_visits', [])}
- Rising trends: {data.get('trends', [])}

Provide:
1. Key patterns observed
2. Predicted diseases likely next month
3. Risk warnings
4. Recommendations"""
    return await _ask_llm(system, user)


async def get_stationery_insights(data: dict) -> str:
    system = "You are a campus supply chain analytics AI. Analyze stationery store data and provide demand forecasts, restock recommendations, and shortage warnings. Be concise and use bullet points."
    user = f"""Analyze this stationery store data:
- Total items: {data.get('total', 0)}
- Top demand items: {data.get('top_demand', [])}
- Low stock items: {data.get('low_stock', [])}
- Category breakdown: {data.get('by_category', [])}

Provide:
1. Items most likely to be purchased next
2. Predicted peak visit timings
3. Shortage risk warnings
4. Restocking recommendations"""
    return await _ask_llm(system, user)


async def get_parking_insights(data: dict) -> str:
    system = "You are a campus parking analytics AI. Analyze parking data and provide occupancy forecasts, best parking times, and slot recommendations. Be concise and use bullet points."
    user = f"""Analyze this parking data:
- Total records: {data.get('total', 0)}
- Currently occupied: {data.get('occupied', 0)}
- Currently free: {data.get('free', 0)}
- Hourly distribution: {data.get('hourly', [])}
- Slot usage: {data.get('slot_usage', [])}

Provide:
1. Peak parking hours
2. Predicted busy times for tomorrow
3. Best slots to park in
4. Recommendations for reducing congestion"""
    return await _ask_llm(system, user)


async def generate_proposal(items: list) -> str:
    system = "You are a procurement AI for a campus stationery store. Generate a professional buying proposal document for low-stock items. Include item names, recommended quantities, estimated costs, and supplier notes. Format as a clean markdown document."
    user = f"""Generate a buying proposal for these low-stock items:
{items}

Include:
1. Header with date and store name
2. Items table with: Item Name, Current Stock, Recommended Order Quantity, Estimated Unit Price, Total Cost
3. Summary with total estimated budget
4. Notes and recommendations"""
    return await _ask_llm(system, user)


async def parse_voice_command(text: str, context: str) -> dict:
    system = f"""You are an AI assistant for a campus management system. Parse user voice commands into structured actions for the {context} module.
Return a JSON object with:
- "action": one of "create", "update", "delete", "search", "analyze"
- "data": relevant fields as key-value pairs
Be precise and extract all mentioned data fields."""
    user = f"Parse this command: {text}"
async def conversational_form_filler(current_data: dict, user_input: str, context: str) -> dict:
    """
    Arjun - Multi-turn form filler.
    Analyzes current_data + user_input to update fields and decide the next question.
    """
    system = f"""You are Arjun, a helpful and polite Indian AI assistant for CampusAI. 
    Your goal is to help the user fill out a {context} record by asking questions one by one.

    Current Data: {current_data}
    
    Rules:
    1. If this is the start (data is empty), introduce yourself as Arjun and ask for the first field.
    2. Extract information from the user's input: {user_input}
    3. Update the data fields accordingly. 
    4. For Medical context, required fields are: student_name, branch, year, issue, severity.
    5. Be polite and use a "Namaste" or "Ji" occasionally where appropriate, but keep it professional.
    6. If all required fields are present, provide a summary and ask for confirmation to save.
    7. Once the user says "Yes" or confirms to the summary, return "is_confirmed": true.

    Return ONLY a JSON object with:
    - "updated_data": the full data object after extraction
    - "next_question": the natural voice response/question you will say next
    - "is_complete": true if all info is collected and we just need confirmation
    - "is_confirmed": true if the user has confirmed the summary
    """
    
    user = f"User said: {user_input}\nCurrent Data: {current_data}"
    
    import json
    raw_res = await _ask_llm(system, user)
    
    # Try to parse JSON from the LLM response (handling potential markdown blocks)
    clean_json = raw_res.replace('```json', '').replace('```', '').strip()
    try:
        return json.loads(clean_json)
    except:
        # Fallback if LLM fails to return perfect JSON
        return {
            "updated_data": current_data,
            "next_question": "I'm sorry, I'm having trouble processing that. Could you repeat?",
            "is_complete": False,
            "is_confirmed": False
        }

