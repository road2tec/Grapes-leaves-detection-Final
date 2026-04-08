"""
============================================
Smart Advisor Chatbot Module - Gemini 2.0 Flash
============================================
Handles conversational AI for farmer queries on diseases,
subsidies, best practices, and agri-related topics.
"""

import os
import google.generativeai as genai
from datetime import datetime
from database import get_database
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = """
You are KrishiBot – an expert Smart Agricultural Advisor for Indian farmers, 
specializing in grape cultivation and disease management.

Your role:
- Answer questions about grape diseases (Black Rot, Esca, Leaf Blight, etc.)
- Recommend treatment plans, pesticides, and dosages
- Explain government schemes & subsidies relevant to farmers (PM-KISAN, PKVY, etc.)
- Guide on carbon credits and how farmers can earn from them
- Provide mandi/market price advice and selling strategies
- Discuss crop management, irrigation, and best practices
- Help with equipment buying/selling advice

Always respond:
- In a friendly, easy-to-understand manner
- With practical, actionable advice
- In Hindi or English based on the user's language preference
- Keep responses concise but complete (max 3-4 paragraphs)
- End with a helpful follow-up suggestion when relevant

Context: This is part of the GrapevineDisease Detection System used by farmers in India.
"""


def get_chat_collection():
    db = get_database()
    return db['chat_history']


def send_message(user_id: str, message: str, session_id: str = None) -> dict:
    """
    Send a message to Gemini and return the response with history.

    Args:
        user_id: The authenticated user's ID
        message: The user's query
        session_id: Optional session ID for conversation continuity

    Returns:
        dict with response text, session_id, and timestamp
    """
    try:
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=SYSTEM_PROMPT
        )

        # Fetch last 10 messages for context if session exists
        history = []
        if session_id:
            chat_col = get_chat_collection()
            past = list(chat_col.find(
                {'user_id': user_id, 'session_id': session_id}
            ).sort('timestamp', 1).limit(10))

            for msg in past:
                history.append({'role': 'user', 'parts': [msg['user_message']]})
                history.append({'role': 'model', 'parts': [msg['bot_response']]})

        chat = model.start_chat(history=history)
        response = chat.send_message(message)
        reply = response.text

        # Generate session_id if new conversation
        if not session_id:
            session_id = f"{user_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        # Save to DB
        chat_col = get_chat_collection()
        chat_col.insert_one({
            'user_id': user_id,
            'session_id': session_id,
            'user_message': message,
            'bot_response': reply,
            'timestamp': datetime.utcnow()
        })

        return {
            'success': True,
            'response': reply,
            'session_id': session_id,
            'timestamp': datetime.utcnow().strftime('%H:%M')
        }

    except Exception as e:
        error_msg = str(e)
        print(f"[ERROR] Chatbot error: {error_msg}")
        
        # Handle Rate limits
        if '429' in error_msg or 'quota' in error_msg.lower():
            friendly_message = "⏳ Whoops! You have reached your Gemini API free-tier rate limit (too many messages). Please wait 1 minute and try again!"
        else:
            friendly_message = '⚠️ Sorry, I am unable to respond right now. Please try again.'
            
        return {
            'success': False,
            'response': friendly_message,
            'error': error_msg
        }


def get_chat_sessions(user_id: str) -> list:
    """Get list of chat sessions for a user."""
    try:
        chat_col = get_chat_collection()
        pipeline = [
            {'$match': {'user_id': user_id}},
            {'$group': {
                '_id': '$session_id',
                'last_message': {'$last': '$user_message'},
                'timestamp': {'$last': '$timestamp'},
                'count': {'$sum': 1}
            }},
            {'$sort': {'timestamp': -1}},
            {'$limit': 20}
        ]
        sessions = list(chat_col.aggregate(pipeline))
        for s in sessions:
            s['timestamp'] = s['timestamp'].strftime('%Y-%m-%d %H:%M') if s.get('timestamp') else ''
        return sessions
    except Exception as e:
        print(f"[ERROR] Getting sessions: {str(e)}")
        return []


def get_session_messages(user_id: str, session_id: str) -> list:
    """Get all messages for a specific chat session."""
    try:
        chat_col = get_chat_collection()
        msgs = list(chat_col.find(
            {'user_id': user_id, 'session_id': session_id},
            {'_id': 0}
        ).sort('timestamp', 1))
        for m in msgs:
            m['timestamp'] = m['timestamp'].strftime('%H:%M') if m.get('timestamp') else ''
        return msgs
    except Exception as e:
        print(f"[ERROR] Getting messages: {str(e)}")
        return []
