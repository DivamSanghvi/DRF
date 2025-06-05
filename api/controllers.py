# controllers.py
# This file contains business logic for the API app.

import os
import google.generativeai as genai
from dotenv import load_dotenv
from rest_framework.exceptions import NotFound
from .models import Project, Message
from .serializers import MessageSerializer

load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

def get_greeting(name):
    return f"Hello, {name}! Welcome to the DRF MVC project."

def chat(message: str, stream: bool = False) -> str:
    """Send a message to the AI and get response"""
    try:
        # Get AI response using gemini-1.5-flash
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Create chat with system message
        system_message = """You are a helpful AI assistant. Your responses should be:
1. Clear and concise
2. Professional but friendly
3. Focused on being helpful and informative
4. Based on the context of the conversation
5. Free from harmful or inappropriate content

Please maintain this style throughout our conversation."""
        
        chat_session = model.start_chat(history=[])
        
        if stream:
            # Return the streaming response
            return chat_session.send_message(
                f"{system_message}\n\nUser: {message}",
                stream=True
            )
        else:
            # Return the complete response as text
            response = chat_session.send_message(f"{system_message}\n\nUser: {message}")
            return response.text
        
    except Exception as e:
        return f"Error getting AI response: {str(e)}" 