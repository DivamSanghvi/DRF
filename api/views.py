from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Greeting, Project, Message, Resource
from .controllers import get_greeting, chat
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate, get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserRegistrationSerializer, UserLoginSerializer, ProjectSerializer, MessageSerializer, ResourceSerializer
from datetime import datetime, timedelta
import logging
import jwt
from django.conf import settings
import json
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.http import StreamingHttpResponse
from .services import pdf_processor
import os

logger = logging.getLogger(__name__)
User = get_user_model()

# Create your views here.

class HelloWorldView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Get a hello world message",
        responses={
            200: openapi.Response(
                description="Success",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Hello world message')
                    }
                )
            )
        }
    )
    def get(self, request):
        return Response({"message": "Hello, World!"})

class GreetingView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        name = request.query_params.get('name', 'World')
        greeting = get_greeting(name)
        Greeting.objects.create(name=name)
        return Response({'message': greeting})

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

def set_auth_cookies(response, tokens):
    # Set access token cookie
    response.set_cookie(
        'access_token',
        tokens['access'],
        httponly=True,
        secure=False,  # Set to False for development
        samesite='Lax',
        max_age=7200  # 2 hours (120 minutes * 60 seconds)
    )
    
    # Set refresh token cookie
    response.set_cookie(
        'refresh_token',
        tokens['refresh'],
        httponly=True,
        secure=False,  # Set to False for development
        samesite='Lax',
        max_age=86400  # 24 hours
    )
    
    return response

class UserRegistrationView(APIView):
    permission_classes = (AllowAny,)

    @swagger_auto_schema(
        operation_description="Register a new user",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email', 'password'],
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, format='email', description='User email'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, format='password', description='User password')
            }
        ),
        responses={
            201: openapi.Response(
                description="User registered successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'user': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'email': openapi.Schema(type=openapi.TYPE_STRING, format='email')
                            }
                        ),
                        'message': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: "Bad Request"
        }
    )
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            tokens = get_tokens_for_user(user)
            
            response = Response({
                'user': serializer.data,
                'message': 'Registration successful'
            }, status=status.HTTP_201_CREATED)
            
            return set_auth_cookies(response, tokens)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserLoginView(APIView):
    permission_classes = (AllowAny,)

    @swagger_auto_schema(
        operation_description="Login user and get JWT tokens",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email', 'password'],
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, format='email', description='User email'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, format='password', description='User password')
            }
        ),
        responses={
            200: openapi.Response(
                description="Login successful",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Success message')
                    }
                )
            ),
            401: "Invalid credentials",
            400: "Bad Request"
        }
    )
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = authenticate(
                email=serializer.validated_data['email'],
                password=serializer.validated_data['password']
            )
            if user:
                tokens = get_tokens_for_user(user)
                
                response = Response({
                    'message': 'Login successful'
                })
                
                return set_auth_cookies(response, tokens)
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        response = Response({'message': 'Logout successful'})
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        return response

class RefreshTokenView(APIView):
    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')
        if not refresh_token:
            return Response({'error': 'No refresh token found'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            refresh = RefreshToken(refresh_token)
            tokens = {
                'access': str(refresh.access_token),
                'refresh': str(refresh)
            }
            
            response = Response({'message': 'Token refreshed successfully'})
            return set_auth_cookies(response, tokens)
        except Exception as e:
            return Response({'error': 'Invalid refresh token'}, status=status.HTTP_400_BAD_REQUEST)

class ProjectCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Create a new project",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['name'],
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='Project name')
            }
        ),
        responses={
            201: openapi.Response(
                description="Project created successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'name': openapi.Schema(type=openapi.TYPE_STRING),
                        'user': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time')
                    }
                )
            ),
            400: "Bad Request"
        }
    )
    def post(self, request):
        logger.debug(f"ProjectCreateView - User: {request.user}")
        logger.debug(f"ProjectCreateView - Auth: {request.auth}")
        logger.debug(f"ProjectCreateView - Is authenticated: {request.user.is_authenticated}")
        
        serializer = ProjectSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProjectListView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get all projects for the authenticated user",
        responses={
            200: openapi.Response(
                description="List of projects",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'name': openapi.Schema(type=openapi.TYPE_STRING),
                            'user': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time')
                        }
                    )
                )
            )
        }
    )
    def get(self, request):
        projects = Project.objects.filter(user=request.user)
        serializer = ProjectSerializer(projects, many=True)
        return Response(serializer.data)

class ProjectUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Update a project",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['name'],
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='Project name')
            }
        ),
        responses={
            200: openapi.Response(
                description="Project updated successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'name': openapi.Schema(type=openapi.TYPE_STRING),
                        'user': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time')
                    }
                )
            ),
            400: "Bad Request",
            404: "Project not found"
        }
    )
    def put(self, request, project_id):
        try:
            project = Project.objects.get(id=project_id, user=request.user)
        except Project.DoesNotExist:
            return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = ProjectSerializer(project, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProjectDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Delete a project",
        responses={
            200: openapi.Response(
                description="Project deleted successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Success message')
                    }
                )
            ),
            404: "Project not found"
        }
    )
    def delete(self, request, project_id):
        try:
            project = Project.objects.get(id=project_id, user=request.user)
            project.delete()
            return Response({'message': 'Project deleted successfully'}, status=status.HTTP_200_OK)
        except Project.DoesNotExist:
            return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)

class MessageView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get all messages for a project",
        responses={
            200: openapi.Response(
                description="List of messages",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'project': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'role': openapi.Schema(type=openapi.TYPE_STRING),
                            'content': openapi.Schema(type=openapi.TYPE_STRING),
                            'liked': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='True=liked, False=disliked, null=no action'),
                            'user_feedback_message': openapi.Schema(type=openapi.TYPE_STRING, description='User feedback on AI messages'),
                            'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time')
                        }
                    )
                )
            ),
            404: "Project not found"
        }
    )
    def get(self, request, project_id):
        try:
            project = Project.objects.get(id=project_id, user=request.user)
            messages = Message.objects.filter(project=project).order_by('created_at')
            serializer = MessageSerializer(messages, many=True)
            return Response(serializer.data)
        except Project.DoesNotExist:
            return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)

class MessageReactionView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Like or dislike an AI message",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['reaction'],
            properties={
                'reaction': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['like', 'dislike', 'remove'],
                    description='Type of reaction to apply to the message'
                )
            }
        ),
        responses={
            200: openapi.Response(
                description="Reaction applied successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Success message'),
                        'liked': openapi.Schema(
                            type=openapi.TYPE_BOOLEAN,
                            description='Current reaction status (true=liked, false=disliked, null=no reaction)'
                        )
                    }
                )
            ),
            400: "Cannot react to user messages or invalid reaction type",
            404: "Message or project not found"
        }
    )
    def post(self, request, project_id, message_id):
        try:
            project = Project.objects.get(id=project_id, user=request.user)
            message = Message.objects.get(id=message_id, project=project)
            
            if message.role != 'assistant':
                return Response({'error': 'Only AI messages can be reacted to'}, status=status.HTTP_400_BAD_REQUEST)
            
            reaction = request.data.get('reaction', '').lower()
            if reaction not in ['like', 'dislike', 'remove']:
                return Response(
                    {'error': 'Invalid reaction type. Must be one of: like, dislike, remove'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if reaction == 'like':
                message.liked = True
                success_message = 'Message liked successfully'
            elif reaction == 'dislike':
                message.liked = False
                success_message = 'Message disliked successfully'
            else:  # remove
                message.liked = None
                success_message = 'Reaction removed successfully'
            
            message.save()
            
            return Response({
                'message': success_message,
                'liked': message.liked
            }, status=status.HTTP_200_OK)
            
        except Project.DoesNotExist:
            return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)
        except Message.DoesNotExist:
            return Response({'error': 'Message not found'}, status=status.HTTP_404_NOT_FOUND)

class MessageAddFeedbackView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Add feedback to an AI message",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['feedback'],
            properties={
                'feedback': openapi.Schema(type=openapi.TYPE_STRING, description='User feedback message')
            }
        ),
        responses={
            200: openapi.Response(
                description="Feedback added successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Success message'),
                        'user_feedback_message': openapi.Schema(type=openapi.TYPE_STRING, description='The feedback message')
                    }
                )
            ),
            400: "Cannot add feedback to user messages or feedback already exists",
            404: "Message or project not found"
        }
    )
    def post(self, request, project_id, message_id):
        try:
            project = Project.objects.get(id=project_id, user=request.user)
            message = Message.objects.get(id=message_id, project=project)
            
            if message.role != 'assistant':
                return Response({'error': 'Only AI messages can receive feedback'}, status=status.HTTP_400_BAD_REQUEST)
            
            feedback_text = request.data.get('feedback')
            if not feedback_text:
                return Response({'error': 'Feedback text is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            if message.user_feedback_message:
                return Response({'error': 'Feedback already exists. Use update endpoint to modify.'}, status=status.HTTP_400_BAD_REQUEST)
            
            message.user_feedback_message = feedback_text
            message.save()
            
            return Response({
                'message': 'Feedback added successfully',
                'user_feedback_message': message.user_feedback_message
            }, status=status.HTTP_200_OK)
            
        except Project.DoesNotExist:
            return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)
        except Message.DoesNotExist:
            return Response({'error': 'Message not found'}, status=status.HTTP_404_NOT_FOUND)

class MessageUpdateFeedbackView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Update feedback on an AI message",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['feedback'],
            properties={
                'feedback': openapi.Schema(type=openapi.TYPE_STRING, description='Updated user feedback message')
            }
        ),
        responses={
            200: openapi.Response(
                description="Feedback updated successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Success message'),
                        'user_feedback_message': openapi.Schema(type=openapi.TYPE_STRING, description='The updated feedback message')
                    }
                )
            ),
            400: "Cannot update feedback on user messages or no feedback exists",
            404: "Message or project not found"
        }
    )
    def put(self, request, project_id, message_id):
        try:
            project = Project.objects.get(id=project_id, user=request.user)
            message = Message.objects.get(id=message_id, project=project)
            
            if message.role != 'assistant':
                return Response({'error': 'Only AI messages can receive feedback'}, status=status.HTTP_400_BAD_REQUEST)
            
            feedback_text = request.data.get('feedback')
            if not feedback_text:
                return Response({'error': 'Feedback text is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            if not message.user_feedback_message:
                return Response({'error': 'No existing feedback to update. Use add endpoint first.'}, status=status.HTTP_400_BAD_REQUEST)
            
            message.user_feedback_message = feedback_text
            message.save()
            
            return Response({
                'message': 'Feedback updated successfully',
                'user_feedback_message': message.user_feedback_message
            }, status=status.HTTP_200_OK)
            
        except Project.DoesNotExist:
            return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)
        except Message.DoesNotExist:
            return Response({'error': 'Message not found'}, status=status.HTTP_404_NOT_FOUND)

class MessageRemoveFeedbackView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Remove feedback from an AI message",
        responses={
            200: openapi.Response(
                description="Feedback removed successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Success message'),
                        'user_feedback_message': openapi.Schema(type=openapi.TYPE_STRING, description='Current feedback status (null)')
                    }
                )
            ),
            400: "Cannot remove feedback from user messages",
            404: "Message or project not found"
        }
    )
    def delete(self, request, project_id, message_id):
        try:
            project = Project.objects.get(id=project_id, user=request.user)
            message = Message.objects.get(id=message_id, project=project)
            
            if message.role != 'assistant':
                return Response({'error': 'Only AI messages can have feedback removed'}, status=status.HTTP_400_BAD_REQUEST)
            
            message.user_feedback_message = None
            message.save()
            
            return Response({
                'message': 'Feedback removed successfully',
                'user_feedback_message': message.user_feedback_message
            }, status=status.HTTP_200_OK)
            
        except Project.DoesNotExist:
            return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)
        except Message.DoesNotExist:
            return Response({'error': 'Message not found'}, status=status.HTTP_404_NOT_FOUND)

class ProjectChatView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Send a message to the AI and get response",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['message'],
            properties={
                'message': openapi.Schema(type=openapi.TYPE_STRING, description='Message to send to AI'),
                'stream': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Whether to stream the response', default=True)
            }
        ),
        responses={
            200: openapi.Response(
                description="Chat response",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'user_message': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'project': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'role': openapi.Schema(type=openapi.TYPE_STRING),
                                'content': openapi.Schema(type=openapi.TYPE_STRING),
                                'liked': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Always null for user messages'),
                                'user_feedback_message': openapi.Schema(type=openapi.TYPE_STRING, description='Always null for user messages'),
                                'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time')
                            }
                        ),
                        'ai_response': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'project': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'role': openapi.Schema(type=openapi.TYPE_STRING),
                                'content': openapi.Schema(type=openapi.TYPE_STRING),
                                'liked': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='True=liked, False=disliked, null=no action'),
                                'user_feedback_message': openapi.Schema(type=openapi.TYPE_STRING, description='User feedback on AI messages'),
                                'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time')
                            }
                        )
                    }
                )
            ),
            400: "Bad Request",
            404: "Project not found"
        }
    )
    def post(self, request, project_id):
        try:
            project = Project.objects.get(id=project_id, user=request.user)
        except Project.DoesNotExist:
            return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)

        user_message_content = request.data.get('message')
        if not user_message_content:
            return Response({'error': 'Message content is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Create user message
        user_message = Message.objects.create(
            project=project,
            role='user',
            content=user_message_content
        )

        # Handle streaming logic
        stream_param = request.data.get('stream')
        should_stream = True if stream_param is None else bool(stream_param)

        if should_stream:
            def event_stream():
                try:
                    # Create AI message first
                    ai_message = Message.objects.create(
                        project=project,
                        role='assistant',
                        content=''
                    )
                    
                    # Get streaming response from AI with project context
                    stream = chat(user_message_content, stream=True, project_id=project_id)
                    
                    # Stream each chunk
                    full_response = ''
                    current_sentence = ''
                    
                    for chunk in stream:
                        if hasattr(chunk, 'text'):
                            chunk_text = chunk.text
                        else:
                            chunk_text = str(chunk)
                            
                        if chunk_text:
                            # Clean up the chunk text
                            chunk_text = chunk_text.replace('\\n', '\n').replace('\\"', '"')
                            
                            # Add to current sentence
                            current_sentence += chunk_text
                            
                            # Check if we have a complete sentence or punctuation
                            if any(p in current_sentence for p in ['.', '!', '?', '\n']):
                                # Split on punctuation
                                parts = []
                                temp = ''
                                for char in current_sentence:
                                    temp += char
                                    if char in ['.', '!', '?', '\n']:
                                        parts.append(temp)
                                        temp = ''
                                if temp:
                                    parts.append(temp)
                                
                                # Send each part with a small delay
                                for part in parts:
                                    if part.strip():
                                        full_response += part
                                        # Update the message content
                                        ai_message.content = full_response
                                        ai_message.save()
                                        
                                        # Send the chunk as an SSE with proper formatting
                                        yield f"data: {json.dumps({'chunk': part.strip()})}\n\n"
                                        
                                        # Add a small delay to simulate typing
                                        import time
                                        time.sleep(0.1)  # 100ms delay for more natural typing
                                
                                current_sentence = temp
                    
                    # Send any remaining text
                    if current_sentence.strip():
                        full_response += current_sentence
                        ai_message.content = full_response
                        ai_message.save()
                        yield f"data: {json.dumps({'chunk': current_sentence.strip()})}\n\n"
                    
                    # Send the final message data
                    ai_message_serializer = MessageSerializer(ai_message)
                    yield f"data: {json.dumps({'done': True, 'message': ai_message_serializer.data})}\n\n"
                    
                except Exception as e:
                    logger.error(f"Error in streaming response: {e}")
                    # Update the AI message with error
                    if 'ai_message' in locals():
                        ai_message.content = f"Error: {str(e)}"
                        ai_message.save()
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"

            response = StreamingHttpResponse(
                event_stream(),
                content_type='text/event-stream'
            )
            response['Cache-Control'] = 'no-cache'
            response['X-Accel-Buffering'] = 'no'
            return response

        else:
            # Non-streaming response handling remains the same
            try:
                ai_response_content = chat(user_message_content, stream=False, project_id=project_id)
            except Exception as e:
                logger.error(f"Error getting AI response: {e}")
                ai_response_content = "Sorry, I couldn't process your message at the moment."

            ai_message = Message.objects.create(
                project=project,
                role='assistant',
                content=ai_response_content
            )

            user_message_serializer = MessageSerializer(user_message)
            ai_message_serializer = MessageSerializer(ai_message)

            return Response({
                'user_message': user_message_serializer.data,
                'ai_response': ai_message_serializer.data
            })

class ResourceAddView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Add one or more PDF resources to a project",
        manual_parameters=[
            openapi.Parameter('project_id', openapi.IN_PATH, description="Project ID", type=openapi.TYPE_INTEGER),
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['pdf_files'],
            properties={
                'pdf_files': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_BINARY),
                    description='List of PDF files to upload'
                )
            }
        ),
        responses={
            201: openapi.Response(
                description="Resources added successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'resources': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'user': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'project': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'pdf_file': openapi.Schema(type=openapi.TYPE_STRING, description='File URL'),
                                    'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time')
                                }
                            )
                        )
                    }
                )
            ),
            400: "Bad Request",
            404: "Project not found"
        }
    )
    def post(self, request, project_id):
        try:
            project = Project.objects.get(id=project_id, user=request.user)
        except Project.DoesNotExist:
            return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)

        # Check if files were uploaded
        if 'pdf_files' not in request.FILES:
            return Response({'error': 'PDF files are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        uploaded_files = request.FILES.getlist('pdf_files')
        if not uploaded_files:
            return Response({'error': 'No PDF files were uploaded'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate all files are PDFs
        for file in uploaded_files:
            if not file.name.lower().endswith('.pdf'):
                return Response(
                    {'error': f'Only PDF files are allowed. Found: {file.name}'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Create resources for each PDF
        created_resources = []
        all_docs = []
        
        for pdf_file in uploaded_files:
            # Save the PDF file
            resource = Resource.objects.create(
                user=request.user,
                project=project,
                pdf_file=pdf_file
            )
            created_resources.append(resource)
            
            # Process the PDF and get documents
            pdf_path = resource.pdf_file.path
            docs = pdf_processor.process_pdf(pdf_path)
            if docs:
                all_docs.extend(docs)
        
        # Create or update vector store for the project
        if all_docs:
            pdf_processor.save_or_update_vector_store(all_docs, project_id)
        
        # Serialize all created resources
        serializer = ResourceSerializer(created_resources, many=True)
        
        return Response({
            'message': f'Successfully uploaded and processed {len(created_resources)} PDF(s)',
            'resources': serializer.data
        }, status=status.HTTP_201_CREATED)

class ResourceView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="List all resources for a project",
        responses={
            200: openapi.Response(
                description="List of resources",
                schema=ResourceSerializer(many=True)
            ),
            404: "Project not found"
        }
    )
    def get(self, request, project_id):
        try:
            project = Project.objects.get(id=project_id)
            resources = Resource.objects.filter(project=project)
            serializer = ResourceSerializer(resources, many=True)
            return Response(serializer.data)
        except Project.DoesNotExist:
            return Response({"error": "Project not found"}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        operation_description="Delete a specific resource",
        responses={
            204: "Resource deleted successfully",
            404: "Resource not found"
        }
    )
    def delete(self, request, project_id, resource_id):
        try:
            resource = Resource.objects.get(id=resource_id, project_id=project_id)
            
            # Delete the PDF file from storage
            if resource.pdf_file:
                if os.path.isfile(resource.pdf_file.path):
                    os.remove(resource.pdf_file.path)
            
            # Delete the resource from database
            resource.delete()
            
            # Update vector store by removing the resource's documents
            pdf_processor.remove_resource_from_vector_store(project_id, resource_id)
            
            return Response(status=status.HTTP_202_ACCEPTED)
        except Resource.DoesNotExist:
            return Response({"error": "Resource not found"}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        operation_description="Update a resource's metadata",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='New name for the resource'),
                'description': openapi.Schema(type=openapi.TYPE_STRING, description='New description for the resource')
            }
        ),
        responses={
            200: openapi.Response(
                description="Updated resource",
                schema=ResourceSerializer()
            ),
            404: "Resource not found"
        }
    )
    def patch(self, request, project_id, resource_id):
        try:
            resource = Resource.objects.get(id=resource_id, project_id=project_id)
            serializer = ResourceSerializer(resource, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Resource.DoesNotExist:
            return Response({"error": "Resource not found"}, status=status.HTTP_404_NOT_FOUND)
