# controllers.py
# This file contains business logic for the API app.

import os
import google.generativeai as genai
from dotenv import load_dotenv
from rest_framework.exceptions import NotFound
from .models import Project, Message
from .serializers import MessageSerializer
from .services import pdf_processor
import logging
from django.http import StreamingHttpResponse
import time

load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

logger = logging.getLogger(__name__)

def get_greeting(name):
    return f"Hello, {name}! Welcome to the DRF MVC project."

def generate_project_name(user_message, assistant_message):
    """
    Generate a 2-4 word project name based on the first conversation.
    
    Args:
        user_message (str): The user's first message
        assistant_message (str): The assistant's response
        
    Returns:
        str: A 2-4 word project name
    """
    try:
        # Verify API key
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            logger.error("Gemini API key not found for project naming.")
            return "Untitled Project"

        # Configure Gemini API
        genai.configure(api_key=api_key)
        
        # Create a prompt for generating project name
        prompt = f"""Based on the following conversation between a user and an AI assistant, suggest a concise and relevant project name that captures the main topic or purpose of the discussion.

User message: "{user_message}"

Assistant response: "{assistant_message}"

CRITICAL REQUIREMENTS:
- Return ONLY the project name, nothing else
- The name must be EXACTLY 2-4 SEPARATE words with spaces between them
- DO NOT create compound words like "DjangoVsNode" - use separate words like "Django Node Comparison"
- DO NOT use camelCase or concatenated words
- Each word must be separated by a single space
- Make it descriptive and relevant to the conversation topic
- Use title case (capitalize each word)
- Examples of GOOD names: "Web Framework Comparison", "Math Concepts Overview", "Python Django Guide"
- Examples of BAD names: "WebFrameworkComparison", "DjangoVsNode", "PythonGuide"

Generate a project name with exactly 2-4 separate words:"""

        # Initialize the model
        models_to_try = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']
        model = None
        
        for model_name in models_to_try:
            try:
                model = genai.GenerativeModel(model_name)
                break
            except Exception as e:
                logger.warning(f"Failed to initialize {model_name}: {str(e)}")
                continue

        if not model:
            logger.error("Failed to initialize any model for project naming.")
            return "Untitled Project"

        # Generate the project name
        try:
            response = model.generate_content(prompt)
            if response and hasattr(response, 'text'):
                suggested_name = response.text.strip()
                
                # Basic validation: ensure it's 2-4 words
                words = suggested_name.split()
                
                if 2 <= len(words) <= 4:
                    return suggested_name
                elif len(words) > 4:
                    # Take first 4 words if too long
                    truncated_name = " ".join(words[:4])
                    return truncated_name
                elif len(words) == 1:
                    # Try to fix compound words by adding intelligent spacing
                    single_word = words[0]
                    
                    # Try to split common patterns (camelCase, common separators)
                    import re
                    # Split on capital letters (camelCase) but keep the capitals
                    split_attempt = re.sub(r'([a-z])([A-Z])', r'\1 \2', single_word)
                    # Split on common patterns like "Vs", "And", etc.
                    split_attempt = re.sub(r'(Vs|And|Or|To|From)', r' \1 ', split_attempt)
                    # Clean up multiple spaces
                    split_attempt = re.sub(r'\s+', ' ', split_attempt).strip()
                    
                    new_words = split_attempt.split()
                    
                    if 2 <= len(new_words) <= 4:
                        return split_attempt
                    else:
                        # If still can't fix it, try a simple fallback
                        return "Project Discussion"
                else:
                    # If too short, return a default
                    return "Project Discussion"
            else:
                logger.warning("No text response received for project naming.")
                return "Project Discussion"
                
        except Exception as e:
            logger.error(f"Error generating project name: {str(e)}")
            return "Project Discussion"
            
    except Exception as e:
        logger.error(f"Error in generate_project_name: {str(e)}")
        return "Project Discussion"

def chat(message, project_id=None, stream=False):
    try:
        # Verify API key
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            error_msg = "Gemini API key not found. Please check your .env file."
            logger.error(error_msg)
            if stream:
                def generate_error():
                    yield f"data: Error: {error_msg}\n\n"
                return generate_error()
            return f"Error: {error_msg}"

        # Configure Gemini API
        genai.configure(api_key=api_key)
        
        # Get relevant documents if project_id is provided
        context = ""
        if project_id:
            docs = pdf_processor.get_relevant_documents(message, project_id)
            if docs:
                context = "\n\n".join([doc.page_content for doc in docs])
                message = f"""You are a helpful AI assistant. I will provide you with some context from documents and a user question. Please use the context to answer the question.

Context from documents:
{context}

User question: {message}

Please provide a detailed and accurate response based on the context provided."""
            else:
                logger.warning(f"No relevant documents found for project {project_id}")
                message = f"""You are a helpful AI assistant. The user has asked: {message}

Please note that I don't have access to any specific documents to reference. I'll do my best to help based on my general knowledge."""

        # Initialize the model with retry logic
        models_to_try = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']
        model = None
        last_error = None

        for model_name in models_to_try:
            try:
                model = genai.GenerativeModel(model_name)
                # Test the model with a simple request
                test_response = model.generate_content("test")
                if test_response:
                    logger.info(f"Successfully initialized model: {model_name}")
                    break
            except Exception as e:
                last_error = e
                logger.warning(f"Failed to initialize {model_name}: {str(e)}")
                continue

        if not model:
            error_msg = f"Failed to initialize any model. Last error: {str(last_error)}"
            logger.error(error_msg)
            if stream:
                def generate_error():
                    yield f"data: Error: {error_msg}\n\n"
                return generate_error()
            return f"Error: {error_msg}"

        # Generate response with retry logic
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                if stream:
                    response = model.generate_content(message, stream=True)
                else:
                    response = model.generate_content(message)
                if response:
                    break
            except Exception as e:
                if "quota" in str(e).lower() and attempt < max_retries - 1:
                    logger.warning(f"Quota exceeded, attempt {attempt + 1} of {max_retries}")
                    time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                    continue
                else:
                    raise e
        
        if stream:
            def generate():
                try:
                    for chunk in response:
                        if hasattr(chunk, 'text'):
                            yield f"data: {chunk.text}\n\n"
                        else:
                            yield f"data: {str(chunk)}\n\n"
                except Exception as e:
                    error_msg = f"Error in streaming response: {str(e)}"
                    logger.error(error_msg)
                    yield f"data: Error: {error_msg}\n\n"
            return generate()
        else:
            try:
                if isinstance(response, str):
                    return response
                elif isinstance(response, bytes):
                    return response.decode('utf-8')
                elif hasattr(response, 'text'):
                    return response.text
                elif hasattr(response, 'parts'):
                    parts = []
                    for part in response.parts:
                        if isinstance(part, bytes):
                            parts.append(part.decode('utf-8'))
                        elif hasattr(part, 'text'):
                            parts.append(part.text)
                        else:
                            parts.append(str(part))
                    return " ".join(parts)
                else:
                    return str(response)
            except Exception as e:
                error_msg = f"Error processing response: {str(e)}"
                logger.error(error_msg)
                return f"Error: {error_msg}"

    except Exception as e:
        error_msg = f"Error in chat: {str(e)}"
        logger.error(error_msg)
        if stream:
            def generate_error():
                yield f"data: Error: {error_msg}\n\n"
            return generate_error()
        return f"Error: {error_msg}" 