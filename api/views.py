from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Greeting, Project, Conversation, Message
from .controllers import get_greeting, chat
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate, get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserRegistrationSerializer, UserLoginSerializer, ProjectSerializer, ConversationSerializer, MessageSerializer
from datetime import datetime, timedelta
import logging
import jwt
from django.conf import settings
import json

logger = logging.getLogger(__name__)
User = get_user_model()

# Create your views here.

class HelloWorldView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"message": "Hello, World!"})

class GreetingView(APIView):
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
        max_age=300  # 5 minutes
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

    def post(self, request):
        logger.debug(f"ProjectCreateView - User: {request.user}")
        logger.debug(f"ProjectCreateView - Auth: {request.auth}")
        logger.debug(f"ProjectCreateView - Is authenticated: {request.user.is_authenticated}")
        
        serializer = ProjectSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ConversationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        """Get all conversations for a project"""
        try:
            project = Project.objects.get(id=project_id, user=request.user)
            conversations = Conversation.objects.filter(project=project)
            serializer = ConversationSerializer(conversations, many=True)
            return Response(serializer.data)
        except Project.DoesNotExist:
            return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, project_id):
        """Create a new conversation"""
        try:
            project = Project.objects.get(id=project_id, user=request.user)
            conversation = Conversation.objects.create(project=project)
            serializer = ConversationSerializer(conversation)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Project.DoesNotExist:
            return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)

class ConversationChatView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, project_id, conversation_id):
        """Send a message to the AI and get response"""
        try:
            # Verify project belongs to user
            project = Project.objects.get(id=project_id, user=request.user)
            
            # Get conversation
            conversation = Conversation.objects.get(id=conversation_id, project=project)
            
            # Get message from request
            message = request.data.get('message')
            if not message:
                return Response(
                    {"error": "Message is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Send message to AI and get response
            response = chat(conversation_id, message)
            
            return Response(response, status=status.HTTP_200_OK)
            
        except Project.DoesNotExist:
            return Response(
                {"error": "Project not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Conversation.DoesNotExist:
            return Response(
                {"error": "Conversation not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
