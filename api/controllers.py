# controllers.py
# This file contains business logic for the API app.

import os
import google.generativeai as genai
from dotenv import load_dotenv
from rest_framework.exceptions import NotFound
from .models import Conversation, Message
from .serializers import MessageSerializer

load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

def get_greeting(name):
    return f"Hello, {name}! Welcome to the DRF MVC project."

def chat(conversation_id: int, message: str) -> dict:
    """Send a message to the AI and store the response"""
    try:
        # Get the conversation
        conversation = Conversation.objects.get(id=conversation_id)
        
        # Save user message
        user_message = Message.objects.create(
            conversation=conversation,
            role="user",
            content=message
        )
        
        # Get conversation history
        history = Message.objects.filter(conversation=conversation).order_by('created_at')
        
        # Format messages for Gemini
        formatted_messages = []
        
        # Add system message with context if this is the first message
        if not history.exists():
            system_message = {
                "role": "system",
                "parts": [{"text": """You are a helpful AI assistant. Your responses should be:
1. Clear and concise
2. Professional but friendly
3. Focused on being helpful and informative
4. Based on the context of the conversation
5. Free from harmful or inappropriate content

Please maintain this style throughout our conversation."""}]
            }
            formatted_messages.append(system_message)
        
        # Add conversation history with context
        for msg in history:
            # Add context for previous messages
            context = ""
            if msg.role == "user":
                context = "User's previous message: "
            elif msg.role == "assistant":
                context = "AI's previous response: "
            
            formatted_messages.append({
                "role": msg.role,
                "parts": [{"text": f"{context}{msg.content}"}]
            })
        
        # Add current message with context
        current_message = f"User's current message: {message}"
        
        # Get AI response using gemini-1.5-flash
        model = genai.GenerativeModel('gemini-1.5-flash')
        chat = model.start_chat(history=formatted_messages)
        response = chat.send_message(current_message)
        
        # Save AI response
        ai_message = Message.objects.create(
            conversation=conversation,
            role="assistant",
            content=response.text
        )
        
        return {
            "user_message": MessageSerializer(user_message).data,
            "ai_response": MessageSerializer(ai_message).data
        }
        
    except Conversation.DoesNotExist:
        raise NotFound("Conversation not found")
    except Exception as e:
        # Save error message
        error_message = Message.objects.create(
            conversation=conversation,
            role="assistant",
            content=f"Error getting AI response: {str(e)}"
        )
        return {
            "user_message": MessageSerializer(user_message).data,
            "ai_response": MessageSerializer(error_message).data
        } 