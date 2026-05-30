# AI Agent using Google Gemini API for task management
# Replaces OpenAI Agents SDK with Gemini

import os
import json
import httpx

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-1.5-flash"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

SYSTEM_PROMPT = """You are TaskFlow Assistant, an AI that helps users manage their to-do tasks.
You can help users add tasks, list tasks, complete tasks, delete tasks, and update tasks.

Rules:
- When user asks to add a task, respond with the task added confirmation.
- When user asks to list tasks, show them their tasks clearly.
- When user asks to complete/finish a task, confirm it's done.
- When user asks to delete/remove a task, confirm deletion.
- Keep responses short, friendly and helpful.
- Always respond in the SAME language the user writes in.

Smart suggestions:
- After EVERY response, append exactly this format on its own line at the very end:
  <!--suggestions:["suggestion 1","suggestion 2","suggestion 3"]-->
- Generate 2-3 short contextual follow-up suggestions.
- ALWAYS include the suggestions line. Never skip it.
"""


async def run_agent(user_id: str, message: str, history: list[dict]) -> str:
    """
    Run Gemini AI to handle user chat message for task management.
    """
    if not GEMINI_API_KEY:
        return "AI service not configured. Please set GEMINI_API_KEY.<!--suggestions:[\"List my tasks\",\"Add a task\",\"Help\"]-->"

    # Build conversation history for Gemini
    contents = []
    
    # Add history
    for msg in history[-10:]:  # last 10 messages for context
        role = "user" if msg["role"] == "user" else "model"
        contents.append({
            "role": role,
            "parts": [{"text": msg["content"]}]
        })
    
    # Add current message
    contents.append({
        "role": "user",
        "parts": [{"text": f"User ID: {user_id}\n\n{message}"}]
    })

    payload = {
        "system_instruction": {
            "parts": [{"text": SYSTEM_PROMPT}]
        },
        "contents": contents,
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 500,
        }
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{GEMINI_URL}?key={GEMINI_API_KEY}",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            data = response.json()
            
            # Extract text from Gemini response
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    text = parts[0].get("text", "")
                    # Ensure suggestions are present
                    if "<!--suggestions:" not in text:
                        text += '\n<!--suggestions:["List my tasks","Add a new task","Help me organize"]-->'
                    return text
            
            return "I couldn't process that request. Please try again.<!--suggestions:[\"List my tasks\",\"Add a task\",\"Help\"]-->"
            
    except httpx.HTTPStatusError as e:
        return f"AI service error. Please try again.<!--suggestions:[\"List my tasks\",\"Add a task\"]-->"
    except Exception as e:
        return f"Something went wrong. Please try again.<!--suggestions:[\"List my tasks\",\"Add a task\"]-->"
