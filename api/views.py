from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Greeting, Project, Message, Resource
from .controllers import get_greeting, chat, generate_project_name
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
from .github_oauth import GitHubOAuthService
from django.shortcuts import redirect
from django.db import transaction
import secrets
import os
from .apple_oauth import AppleOAuthService
from .tasks import process_pdf_task, process_multiple_pdfs_task

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


class GitHubOAuthInitiateView(APIView):
    """
    Initiate GitHub OAuth flow by redirecting to GitHub authorization URL
    """
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Initiate GitHub OAuth authentication flow",
        responses={
            302: openapi.Response(
                description="Redirect to GitHub authorization",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'authorization_url': openapi.Schema(type=openapi.TYPE_STRING, description='GitHub authorization URL')
                    }
                )
            ),
            500: "GitHub OAuth not configured"
        }
    )
    def get(self, request):
        try:
            # Check if GitHub OAuth is configured
            if not settings.GITHUB_CLIENT_ID or not settings.GITHUB_CLIENT_SECRET:
                return Response(
                    {'error': 'GitHub OAuth not configured on server'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Generate a random state for CSRF protection
            state = secrets.token_urlsafe(32)
            request.session['github_oauth_state'] = state
            
            # Get GitHub authorization URL
            auth_url = GitHubOAuthService.get_authorization_url(state=state)
            
            # Return the URL instead of redirecting (for API usage)
            return Response({
                'authorization_url': auth_url,
                'message': 'Redirect to the authorization_url to complete GitHub OAuth'
            })
            
        except Exception as e:
            logger.error(f"Error initiating GitHub OAuth: {e}")
            return Response(
                {'error': 'Failed to initiate GitHub OAuth'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GitHubOAuthCallbackView(APIView):
    """
    Handle GitHub OAuth callback and complete authentication
    """
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Handle GitHub OAuth callback and authenticate user",
        manual_parameters=[
            openapi.Parameter('code', openapi.IN_QUERY, description="Authorization code from GitHub", type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('state', openapi.IN_QUERY, description="State parameter for CSRF protection", type=openapi.TYPE_STRING),
        ],
        responses={
            200: openapi.Response(
                description="GitHub authentication successful",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Success message'),
                        'user': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'email': openapi.Schema(type=openapi.TYPE_STRING),
                                'first_name': openapi.Schema(type=openapi.TYPE_STRING),
                                'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                                'github_username': openapi.Schema(type=openapi.TYPE_STRING),
                                'is_github_user': openapi.Schema(type=openapi.TYPE_BOOLEAN)
                            }
                        ),
                        'created': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='True if new user was created')
                    }
                )
            ),
            400: "Bad Request - Invalid or missing parameters",
            401: "Authentication failed",
            500: "Internal server error"
        }
    )
    def get(self, request):
        try:
            # Get code and state from query parameters
            code = request.GET.get('code')
            state = request.GET.get('state')
            
            if not code:
                return Response(
                    {'error': 'Authorization code is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Verify state parameter (CSRF protection)
            stored_state = request.session.get('github_oauth_state')
            if state and stored_state and state != stored_state:
                return Response(
                    {'error': 'Invalid state parameter'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Clear the state from session
            request.session.pop('github_oauth_state', None)
            
            # Exchange code for access token
            access_token = GitHubOAuthService.exchange_code_for_token(code)
            if not access_token:
                return Response(
                    {'error': 'Failed to exchange code for access token'}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Get user data from GitHub
            github_user_data = GitHubOAuthService.get_user_data(access_token)
            if not github_user_data:
                return Response(
                    {'error': 'Failed to get user data from GitHub'}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Check if email is available
            if not github_user_data.get('email'):
                return Response(
                    {'error': 'GitHub account must have a public email address'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            email = github_user_data['email']
            github_id = str(github_user_data['id'])
            
            user_created = False
            
            with transaction.atomic():
                # Check if user exists by email or GitHub ID
                user = None
                try:
                    # First try to find by GitHub ID
                    user = User.objects.get(github_id=github_id)
                    logger.info(f"Found existing user by GitHub ID: {github_id}")
                except User.DoesNotExist:
                    try:
                        # Then try to find by email
                        user = User.objects.get(email=email)
                        logger.info(f"Found existing user by email: {email}")
                        
                        # Update existing user with GitHub info
                        user.github_id = github_id
                        user.github_username = github_user_data.get('login')
                        user.github_avatar_url = github_user_data.get('avatar_url')
                        user.is_github_user = True
                        user.save()
                        
                    except User.DoesNotExist:
                        # Create new user
                        user_data = GitHubOAuthService.parse_user_for_registration(github_user_data)
                        
                        user = User.objects.create_user(
                            email=user_data['email'],
                            first_name=user_data['first_name'],
                            last_name=user_data['last_name'],
                            github_id=user_data['github_id'],
                            github_username=user_data['github_username'],
                            github_avatar_url=user_data['github_avatar_url'],
                            is_github_user=user_data['is_github_user'],
                            is_active=user_data['is_active']
                        )
                        user_created = True
                        logger.info(f"Created new GitHub user: {email}")
            
            # Generate JWT tokens
            tokens = get_tokens_for_user(user)
            
            # Prepare response data
            response_data = {
                'message': 'GitHub authentication successful',
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'github_username': user.github_username,
                    'is_github_user': user.is_github_user
                },
                'created': user_created
            }
            
            response = Response(response_data, status=status.HTTP_200_OK)
            return set_auth_cookies(response, tokens)
            
        except Exception as e:
            logger.error(f"Error in GitHub OAuth callback: {e}")
            return Response(
                {'error': 'GitHub authentication failed'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GitHubOAuthTokenView(APIView):
    """
    GitHub OAuth callback that returns tokens directly in response body for API testing
    """
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Handle GitHub OAuth callback and return tokens in response body",
        manual_parameters=[
            openapi.Parameter('code', openapi.IN_QUERY, description="Authorization code from GitHub", type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('state', openapi.IN_QUERY, description="State parameter for CSRF protection", type=openapi.TYPE_STRING),
        ],
        responses={
            200: openapi.Response(
                description="GitHub authentication successful with tokens",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Success message'),
                        'access_token': openapi.Schema(type=openapi.TYPE_STRING, description='JWT access token'),
                        'refresh_token': openapi.Schema(type=openapi.TYPE_STRING, description='JWT refresh token'),
                        'user': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'email': openapi.Schema(type=openapi.TYPE_STRING),
                                'first_name': openapi.Schema(type=openapi.TYPE_STRING),
                                'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                                'github_username': openapi.Schema(type=openapi.TYPE_STRING),
                                'is_github_user': openapi.Schema(type=openapi.TYPE_BOOLEAN)
                            }
                        ),
                        'created': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='True if new user was created')
                    }
                )
            ),
            400: "Bad Request - Invalid or missing parameters",
            401: "Authentication failed",
            500: "Internal server error"
        }
    )
    def get(self, request):
        try:
            # Get code and state from query parameters
            code = request.GET.get('code')
            state = request.GET.get('state')
            
            if not code:
                return Response(
                    {'error': 'Authorization code is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Exchange code for access token
            access_token = GitHubOAuthService.exchange_code_for_token(code)
            if not access_token:
                return Response(
                    {'error': 'Failed to exchange code for access token'}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Get user data from GitHub
            github_user_data = GitHubOAuthService.get_user_data(access_token)
            if not github_user_data:
                return Response(
                    {'error': 'Failed to get user data from GitHub'}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Check if email is available
            if not github_user_data.get('email'):
                return Response(
                    {'error': 'GitHub account must have a public email address'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            email = github_user_data['email']
            github_id = str(github_user_data['id'])
            
            user_created = False
            
            with transaction.atomic():
                # Check if user exists by email or GitHub ID
                user = None
                try:
                    # First try to find by GitHub ID
                    user = User.objects.get(github_id=github_id)
                    logger.info(f"Found existing user by GitHub ID: {github_id}")
                except User.DoesNotExist:
                    try:
                        # Then try to find by email
                        user = User.objects.get(email=email)
                        logger.info(f"Found existing user by email: {email}")
                        
                        # Update existing user with GitHub info
                        user.github_id = github_id
                        user.github_username = github_user_data.get('login')
                        user.github_avatar_url = github_user_data.get('avatar_url')
                        user.is_github_user = True
                        user.save()
                        
                    except User.DoesNotExist:
                        # Create new user
                        user_data = GitHubOAuthService.parse_user_for_registration(github_user_data)
                        
                        user = User.objects.create_user(
                            email=user_data['email'],
                            first_name=user_data['first_name'],
                            last_name=user_data['last_name'],
                            github_id=user_data['github_id'],
                            github_username=user_data['github_username'],
                            github_avatar_url=user_data['github_avatar_url'],
                            is_github_user=user_data['is_github_user'],
                            is_active=user_data['is_active']
                        )
                        user_created = True
                        logger.info(f"Created new GitHub user: {email}")
            
            # Generate JWT tokens
            tokens = get_tokens_for_user(user)
            
            # Return tokens directly in response body for API testing
            response_data = {
                'message': 'GitHub authentication successful',
                'access_token': tokens['access'],
                'refresh_token': tokens['refresh'],
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'github_username': user.github_username,
                    'is_github_user': user.is_github_user
                },
                'created': user_created
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error in GitHub OAuth token endpoint: {e}")
            return Response(
                {'error': 'GitHub authentication failed'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ProjectCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Create a new project",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='Project name (optional - will auto-generate "Untitled1", "Untitled2", etc. if not provided)')
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

class ProjectDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get details of a specific project",
        responses={
            200: openapi.Response(
                description="Project details",
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
            404: "Project not found"
        }
    )
    def get(self, request, project_id):
        try:
            project = Project.objects.get(id=project_id, user=request.user)
            serializer = ProjectSerializer(project)
            return Response(serializer.data)
        except Project.DoesNotExist:
            return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)

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
        operation_description="Get all message conversations for a project",
        responses={
            200: openapi.Response(
                description="List of conversation messages",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Conversation ID'),
                            'project': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'user_content': openapi.Schema(type=openapi.TYPE_STRING, description='User message content'),
                            'assistant_content': openapi.Schema(type=openapi.TYPE_STRING, description='Assistant response content'),
                            'liked': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='True=liked, False=disliked, null=no action'),
                            'user_feedback_message': openapi.Schema(type=openapi.TYPE_STRING, description='User feedback on AI response'),
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

class MessageFeedbackView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get current feedback (reaction and text) for an AI response",
        responses={
            200: openapi.Response(
                description="Current feedback for the AI response",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'conversation_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Conversation ID'),
                        'user_content': openapi.Schema(type=openapi.TYPE_STRING, description='User message content'),
                        'assistant_content': openapi.Schema(type=openapi.TYPE_STRING, description='Assistant response content'),
                        'liked': openapi.Schema(
                            type=openapi.TYPE_BOOLEAN,
                            description='Current reaction status (true=liked, false=disliked, null=no reaction)'
                        ),
                        'user_feedback_message': openapi.Schema(
                            type=openapi.TYPE_STRING, 
                            description='Current feedback text (null if no feedback)'
                        ),
                        'has_feedback': openapi.Schema(
                            type=openapi.TYPE_BOOLEAN,
                            description='Whether this conversation has any feedback'
                        ),
                        'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time', description='Conversation creation time')
                    }
                )
            ),
            404: "Conversation or project not found"
        }
    )
    def get(self, request, project_id, message_id):
        try:
            project = Project.objects.get(id=project_id, user=request.user)
            message = Message.objects.get(id=message_id, project=project)
            
            # Check if conversation has any feedback
            has_feedback = message.liked is not None or message.user_feedback_message is not None
            
            return Response({
                'conversation_id': message.id,
                'user_content': message.user_content,
                'assistant_content': message.assistant_content,
                'liked': message.liked,
                'user_feedback_message': message.user_feedback_message,
                'has_feedback': has_feedback,
                'created_at': message.created_at.isoformat()
            }, status=status.HTTP_200_OK)
            
        except Project.DoesNotExist:
            return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)
        except Message.DoesNotExist:
            return Response({'error': 'Conversation not found'}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        operation_description="Add feedback (reaction and/or text) for an AI response",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'reaction': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['like', 'dislike', 'remove'],
                    description='Reaction to apply to the AI response (optional)'
                ),
                'feedback_text': openapi.Schema(
                    type=openapi.TYPE_STRING, 
                    description='Text feedback for the AI response (optional)'
                )
            }
        ),
        responses={
            200: openapi.Response(
                description="Feedback added successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Success message'),
                        'liked': openapi.Schema(
                            type=openapi.TYPE_BOOLEAN,
                            description='Current reaction status (true=liked, false=disliked, null=no reaction)'
                        ),
                        'user_feedback_message': openapi.Schema(
                            type=openapi.TYPE_STRING, 
                            description='Current feedback text'
                        )
                    }
                )
            ),
            400: "Invalid parameters",
            404: "Conversation or project not found"
        }
    )
    def post(self, request, project_id, message_id):
        try:
            project = Project.objects.get(id=project_id, user=request.user)
            message = Message.objects.get(id=message_id, project=project)
            
            reaction = request.data.get('reaction', '').lower() if request.data.get('reaction') else None
            feedback_text = request.data.get('feedback_text')
            
            # Validate reaction if provided
            if reaction and reaction not in ['like', 'dislike', 'remove']:
                return Response(
                    {'error': 'Invalid reaction type. Must be one of: like, dislike, remove'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if at least one parameter is provided
            if not reaction and not feedback_text:
                return Response(
                    {'error': 'At least one of reaction or feedback_text must be provided'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            updated_fields = []
            
            # Handle reaction
            if reaction:
                if reaction == 'like':
                    message.liked = True
                    updated_fields.append('reaction (liked)')
                elif reaction == 'dislike':
                    message.liked = False
                    updated_fields.append('reaction (disliked)')
                elif reaction == 'remove':
                    message.liked = None
                    updated_fields.append('reaction (removed)')
            
            # Handle feedback text
            if feedback_text:
                message.user_feedback_message = feedback_text
                updated_fields.append('text feedback')
            
            message.save()
            
            success_message = f"Message feedback added: {', '.join(updated_fields)}"
            
            return Response({
                'message': success_message,
                'liked': message.liked,
                'user_feedback_message': message.user_feedback_message
            }, status=status.HTTP_200_OK)
            
        except Project.DoesNotExist:
            return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)
        except Message.DoesNotExist:
            return Response({'error': 'Conversation not found'}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        operation_description="Update existing feedback (reaction and/or text) for an AI response",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'reaction': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['like', 'dislike', 'remove'],
                    description='Updated reaction for the AI response (optional)'
                ),
                'feedback_text': openapi.Schema(
                    type=openapi.TYPE_STRING, 
                    description='Updated text feedback for the AI response (optional)'
                )
            }
        ),
        responses={
            200: openapi.Response(
                description="Feedback updated successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Success message'),
                        'liked': openapi.Schema(
                            type=openapi.TYPE_BOOLEAN,
                            description='Current reaction status (true=liked, false=disliked, null=no reaction)'
                        ),
                        'user_feedback_message': openapi.Schema(
                            type=openapi.TYPE_STRING, 
                            description='Current feedback text'
                        )
                    }
                )
            ),
            400: "Invalid parameters",
            404: "Conversation or project not found"
        }
    )
    def put(self, request, project_id, message_id):
        try:
            project = Project.objects.get(id=project_id, user=request.user)
            message = Message.objects.get(id=message_id, project=project)
            
            reaction = request.data.get('reaction', '').lower() if request.data.get('reaction') else None
            feedback_text = request.data.get('feedback_text')
            
            # Validate reaction if provided
            if reaction and reaction not in ['like', 'dislike', 'remove']:
                return Response(
                    {'error': 'Invalid reaction type. Must be one of: like, dislike, remove'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if at least one parameter is provided
            if not reaction and feedback_text is None:
                return Response(
                    {'error': 'At least one of reaction or feedback_text must be provided'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            updated_fields = []
            
            # Handle reaction
            if reaction:
                if reaction == 'like':
                    message.liked = True
                    updated_fields.append('reaction (liked)')
                elif reaction == 'dislike':
                    message.liked = False
                    updated_fields.append('reaction (disliked)')
                elif reaction == 'remove':
                    message.liked = None
                    updated_fields.append('reaction (removed)')
            
            # Handle feedback text (including empty string to clear feedback)
            if feedback_text is not None:
                message.user_feedback_message = feedback_text if feedback_text.strip() else None
                updated_fields.append('text feedback')
            
            message.save()
            
            success_message = f"Message feedback updated: {', '.join(updated_fields)}"
            
            return Response({
                'message': success_message,
                'liked': message.liked,
                'user_feedback_message': message.user_feedback_message
            }, status=status.HTTP_200_OK)
            
        except Project.DoesNotExist:
            return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)
        except Message.DoesNotExist:
            return Response({'error': 'Conversation not found'}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        operation_description="Remove feedback from an AI response. If no parameters specified, removes all feedback by default.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'remove_reaction': openapi.Schema(
                    type=openapi.TYPE_BOOLEAN,
                    description='Set to true to remove reaction (like/dislike). If not specified, reaction is kept. Only specify true when you want to remove - no need to specify false.'
                ),
                'remove_feedback_text': openapi.Schema(
                    type=openapi.TYPE_BOOLEAN,
                    description='Set to true to remove text feedback. If not specified, feedback text is kept. Only specify true when you want to remove - no need to specify false.'
                ),
                'remove_all': openapi.Schema(
                    type=openapi.TYPE_BOOLEAN,
                    description='Set to true to explicitly remove all feedback (reaction + text). Overrides other parameters. Default: false'
                )
            },
            examples={
                "remove_all_default": {
                    "summary": "Remove all feedback (default)",
                    "description": "Empty body removes all feedback by default",
                    "value": {}
                },
                "remove_reaction_only": {
                    "summary": "Remove only reaction",
                    "description": "Only specify what you want to remove - other items are kept automatically",
                    "value": {"remove_reaction": True}
                },
                "remove_text_only": {
                    "summary": "Remove only text feedback",
                    "description": "Only specify what you want to remove - other items are kept automatically", 
                    "value": {"remove_feedback_text": True}
                },
                "remove_all_explicit": {
                    "summary": "Remove all feedback (explicit)",
                    "value": {"remove_all": True}
                }
            }
        ),
        responses={
            200: openapi.Response(
                description="Feedback removed successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Success message'),
                        'liked': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Current reaction status'),
                        'user_feedback_message': openapi.Schema(type=openapi.TYPE_STRING, description='Current feedback text'),
                        'removed_items': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_STRING),
                            description='List of items that were removed'
                        )
                    }
                )
            ),
            404: "Conversation or project not found"
        }
    )
    def delete(self, request, project_id, message_id):
        try:
            project = Project.objects.get(id=project_id, user=request.user)
            message = Message.objects.get(id=message_id, project=project)
            
            # Get parameters - if nothing specified, default to removing everything
            remove_reaction = request.data.get('remove_reaction')
            remove_feedback_text = request.data.get('remove_feedback_text')
            remove_all = request.data.get('remove_all', False)
            
            # Handle remove_all flag
            if remove_all:
                remove_reaction = True
                remove_feedback_text = True
            
            # If no specific parameters provided, default to removing everything
            if remove_reaction is None and remove_feedback_text is None and not remove_all:
                remove_reaction = True
                remove_feedback_text = True
            else:
                # Use explicit values or default to False if specified
                remove_reaction = remove_reaction if remove_reaction is not None else False
                remove_feedback_text = remove_feedback_text if remove_feedback_text is not None else False
            
            removed_parts = []
            
            # Remove reaction if requested
            if remove_reaction:
                if message.liked is not None:
                    message.liked = None
                    removed_parts.append('reaction')
                else:
                    removed_parts.append('reaction (was already empty)')
            
            # Remove feedback text if requested
            if remove_feedback_text:
                if message.user_feedback_message is not None:
                    message.user_feedback_message = None
                    removed_parts.append('text feedback')
                else:
                    removed_parts.append('text feedback (was already empty)')
            
            message.save()
            
            success_message = f"Removed: {', '.join(removed_parts)}"
            
            return Response({
                'message': success_message,
                'liked': message.liked,
                'user_feedback_message': message.user_feedback_message,
                'removed_items': removed_parts
            }, status=status.HTTP_200_OK)
            
        except Project.DoesNotExist:
            return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)
        except Message.DoesNotExist:
            return Response({'error': 'Conversation not found'}, status=status.HTTP_404_NOT_FOUND)

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
                        'conversation': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Conversation ID'),
                                'project': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'user_content': openapi.Schema(type=openapi.TYPE_STRING, description='User message content'),
                                'assistant_content': openapi.Schema(type=openapi.TYPE_STRING, description='Assistant response content'),
                                'liked': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Always null for new conversations'),
                                'user_feedback_message': openapi.Schema(type=openapi.TYPE_STRING, description='Always null for new conversations'),
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

        # Handle streaming logic
        stream_param = request.data.get('stream')
        should_stream = True if stream_param is None else bool(stream_param)

        if should_stream:
            def event_stream():
                try:
                    # Get AI response with streaming enabled
                    response_generator = chat(user_message_content, stream=True, project_id=project_id)
                    
                    # Create single conversation record with both user and assistant content
                    conversation = Message.objects.create(
                        project=project,
                        user_content=user_message_content,
                        assistant_content=""  # Will be updated after streaming
                    )
                    
                    # Check if this is the first conversation and project name is auto-generated
                    existing_messages_count = Message.objects.filter(project=project).count()
                    if existing_messages_count == 1 and project.name.startswith('Untitled'):
                        try:
                            # Generate new project name based on first conversation
                            old_name = project.name
                            new_name = generate_project_name(user_message_content, "")
                            project.name = new_name
                            project.save()
                            logger.info(f"Auto-renamed project {project.id} from '{old_name}' to '{new_name}'")
                        except Exception as e:
                            logger.error(f"Failed to auto-rename project {project.id}: {str(e)}")
                    
                    # Stream the AI response
                    for chunk in response_generator:
                        # Handle both bytes and string chunks
                        if isinstance(chunk, bytes):
                            chunk = chunk.decode('utf-8')
                        
                        # Remove 'data: ' prefix if present
                        if isinstance(chunk, str) and chunk.startswith('data: '):
                            chunk = chunk[6:]
                        
                        if chunk.strip():
                            # Create the response object
                            response_data = {
                                "message": chunk.strip(),
                                "role": "Pi",
                                "user_id": None,
                                "user_name": None,
                                "profile_url": None,
                                "profile_picture": None,
                                "conv_id": project.id,
                                "timestamp": datetime.now().isoformat(),
                                "status": "Start",
                                "conv_type": "llm_conversation",
                                "file_data": None,
                                "model_choice": "Pi-LLM"
                            }
                            
                            # Send the chunk as an SSE
                            yield f"data: {json.dumps(response_data)}\n\n"
                    
                    # Send the final message with status Complete
                    final_response = {
                        "message": "",
                        "role": "Pi",
                        "user_id": None,
                        "user_name": None,
                        "profile_url": None,
                        "profile_picture": None,
                        "conv_id": project.id,
                        "timestamp": datetime.now().isoformat(),
                        "status": "Complete",
                        "conv_type": "llm_conversation",
                        "file_data": None,
                        "model_choice": "Pi-LLM"
                    }
                    yield f"data: {json.dumps(final_response)}\n\n"
                    
                except Exception as e:
                    logger.error(f"Error in streaming response: {e}")
                    error_response = {
                        "message": f"Error: {str(e)}",
                        "role": "Pi",
                        "user_id": None,
                        "user_name": None,
                        "profile_url": None,
                        "profile_picture": None,
                        "conv_id": project.id,
                        "timestamp": datetime.now().isoformat(),
                        "status": "Error",
                        "conv_type": "llm_conversation",
                        "file_data": None,
                        "model_choice": "Pi-LLM"
                    }
                    yield f"data: {json.dumps({'error': error_response})}\n\n"

            response = StreamingHttpResponse(
                event_stream(),
                content_type='text/event-stream'
            )
            response['Cache-Control'] = 'no-cache'
            response['X-Accel-Buffering'] = 'no'
            return response

        else:
            # Non-streaming response
            try:
                ai_response_content = chat(user_message_content, stream=False, project_id=project_id)
            except Exception as e:
                logger.error(f"Error getting AI response: {e}")
                ai_response_content = "Sorry, I couldn't process your message at the moment."

            # Create single conversation record with both user and assistant content
            conversation = Message.objects.create(
                project=project,
                user_content=user_message_content,
                assistant_content=ai_response_content
            )
            
            # Check if this is the first conversation and project name is auto-generated
            existing_messages_count = Message.objects.filter(project=project).count()
            if existing_messages_count == 1 and project.name.startswith('Untitled'):
                try:
                    # Generate new project name based on first conversation
                    new_name = generate_project_name(user_message_content, ai_response_content)
                    project.name = new_name
                    project.save()
                    logger.info(f"Auto-renamed project {project.id} from 'Untitled*' to '{new_name}'")
                except Exception as e:
                    logger.error(f"Failed to auto-rename project {project.id}: {str(e)}")

            conversation_serializer = MessageSerializer(conversation)

            return Response({
                'conversation': conversation_serializer.data
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
        resource_ids = []
        
        for pdf_file in uploaded_files:
            # Save the PDF file
            resource = Resource.objects.create(
                user=request.user,
                project=project,
                pdf_file=pdf_file
            )
            created_resources.append(resource)
            resource_ids.append(resource.id)
        
        # Trigger Celery task for PDF processing
        if len(resource_ids) == 1:
            process_pdf_task.delay(resource_ids[0])
        else:
            process_multiple_pdfs_task.delay(resource_ids)
        
        # Serialize all created resources
        serializer = ResourceSerializer(created_resources, many=True)
        
        return Response({
            'message': f'Successfully uploaded {len(created_resources)} PDF(s). Processing started in background.',
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
    def get(self, request, project_id, resource_id=None):
        try:
            project = Project.objects.get(id=project_id)
            if resource_id:
                # Return specific resource
                try:
                    resource = Resource.objects.get(id=resource_id, project=project)
                    serializer = ResourceSerializer(resource)
                    return Response(serializer.data)
                except Resource.DoesNotExist:
                    return Response({"error": "Resource not found"}, status=status.HTTP_404_NOT_FOUND)
            else:
                # Return all resources for the project
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

class AppleOAuthInitiateView(APIView):
    """
    Initiate Apple Sign In flow by redirecting to Apple authorization URL
    """
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Initiate Apple Sign In authentication flow",
        responses={
            302: openapi.Response(
                description="Redirect to Apple authorization",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'authorization_url': openapi.Schema(type=openapi.TYPE_STRING, description='Apple authorization URL')
                    }
                )
            ),
            500: "Apple Sign In not configured"
        }
    )
    def get(self, request):
        try:
            # Check if Apple Sign In is configured
            if not all([
                settings.APPLE_CLIENT_ID,
                settings.APPLE_TEAM_ID,
                settings.APPLE_KEY_ID,
                settings.APPLE_PRIVATE_KEY
            ]):
                return Response(
                    {'error': 'Apple Sign In not configured on server'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Generate a random state for CSRF protection
            state = secrets.token_urlsafe(32)
            request.session['apple_oauth_state'] = state
            
            # Get Apple authorization URL
            auth_url = AppleOAuthService.get_authorization_url(state=state)
            
            # Return the URL instead of redirecting (for API usage)
            return Response({
                'authorization_url': auth_url,
                'message': 'Redirect to the authorization_url to complete Apple Sign In'
            })
            
        except Exception as e:
            logger.error(f"Error initiating Apple Sign In: {e}")
            return Response(
                {'error': 'Failed to initiate Apple Sign In'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AppleOAuthCallbackView(APIView):
    """
    Handle Apple Sign In callback and complete authentication
    """
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Handle Apple Sign In callback and authenticate user",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['code', 'id_token'],
            properties={
                'code': openapi.Schema(type=openapi.TYPE_STRING, description="Authorization code from Apple"),
                'id_token': openapi.Schema(type=openapi.TYPE_STRING, description="ID token from Apple"),
                'state': openapi.Schema(type=openapi.TYPE_STRING, description="State parameter for CSRF protection"),
                'user': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'name': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'firstName': openapi.Schema(type=openapi.TYPE_STRING),
                                'lastName': openapi.Schema(type=openapi.TYPE_STRING)
                            }
                        ),
                        'email': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            }
        ),
        responses={
            200: openapi.Response(
                description="Apple authentication successful",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Success message'),
                        'user': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'email': openapi.Schema(type=openapi.TYPE_STRING),
                                'first_name': openapi.Schema(type=openapi.TYPE_STRING),
                                'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                                'is_apple_user': openapi.Schema(type=openapi.TYPE_BOOLEAN)
                            }
                        ),
                        'created': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='True if new user was created')
                    }
                )
            ),
            400: "Bad Request - Invalid or missing parameters",
            401: "Authentication failed",
            500: "Internal server error"
        }
    )
    def post(self, request):
        try:
            # Get code, id_token and state from request data
            code = request.data.get('code')
            id_token = request.data.get('id_token')
            state = request.data.get('state')
            
            if not code or not id_token:
                return Response(
                    {'error': 'Authorization code and ID token are required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Verify state parameter (CSRF protection)
            stored_state = request.session.get('apple_oauth_state')
            if state and stored_state and state != stored_state:
                return Response(
                    {'error': 'Invalid state parameter'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Clear the state from session
            request.session.pop('apple_oauth_state', None)
            
            # Get user data from ID token
            apple_user_data = AppleOAuthService.get_user_data(id_token)
            if not apple_user_data:
                return Response(
                    {'error': 'Failed to get user data from Apple'}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Check if email is available
            if not apple_user_data.get('email'):
                return Response(
                    {'error': 'Apple account must have an email address'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            email = apple_user_data['email']
            apple_id = apple_user_data['apple_id']
            
            user_created = False
            
            with transaction.atomic():
                # Check if user exists by email or Apple ID
                user = None
                try:
                    # First try to find by Apple ID
                    user = User.objects.get(apple_id=apple_id)
                    logger.info(f"Found existing user by Apple ID: {apple_id}")
                except User.DoesNotExist:
                    try:
                        # Then try to find by email
                        user = User.objects.get(email=email)
                        logger.info(f"Found existing user by email: {email}")
                        
                        # Update existing user with Apple info
                        user.apple_id = apple_id
                        user.is_apple_user = True
                        user.save()
                        
                    except User.DoesNotExist:
                        # Create new user
                        user_data = AppleOAuthService.parse_user_for_registration(apple_user_data)
                        
                        user = User.objects.create_user(
                            email=user_data['email'],
                            first_name=user_data['first_name'],
                            last_name=user_data['last_name'],
                            apple_id=user_data['apple_id'],
                            is_apple_user=user_data['is_apple_user'],
                            is_active=user_data['is_active']
                        )
                        user_created = True
                        logger.info(f"Created new Apple user: {email}")
            
            # Generate JWT tokens
            tokens = get_tokens_for_user(user)
            
            # Prepare response data
            response_data = {
                'message': 'Apple authentication successful',
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'is_apple_user': user.is_apple_user
                },
                'created': user_created
            }
            
            response = Response(response_data, status=status.HTTP_200_OK)
            return set_auth_cookies(response, tokens)
            
        except Exception as e:
            logger.error(f"Error in Apple Sign In callback: {e}")
            return Response(
                {'error': 'Apple authentication failed'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AppleSignInTestView(APIView):
    """
    Test endpoint to simulate Apple Sign In flow without needing an Apple ID
    """
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Test Apple Sign In flow with mock data",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email'],
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, format='email', description='Test user email'),
                'first_name': openapi.Schema(type=openapi.TYPE_STRING, description='Test user first name'),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING, description='Test user last name')
            }
        ),
        responses={
            200: openapi.Response(
                description="Test authentication successful",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'user': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'email': openapi.Schema(type=openapi.TYPE_STRING),
                                'first_name': openapi.Schema(type=openapi.TYPE_STRING),
                                'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                                'is_apple_user': openapi.Schema(type=openapi.TYPE_BOOLEAN)
                            }
                        ),
                        'created': openapi.Schema(type=openapi.TYPE_BOOLEAN)
                    }
                )
            )
        }
    )
    def post(self, request):
        try:
            # Get test user data
            email = request.data.get('email')
            first_name = request.data.get('first_name', 'Test')
            last_name = request.data.get('last_name', 'User')
            
            if not email:
                return Response(
                    {'error': 'Email is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Generate a mock Apple ID
            apple_id = f"mock_apple_{email.split('@')[0]}"
            
            user_created = False
            
            with transaction.atomic():
                # Check if user exists
                user = None
                try:
                    # First try to find by Apple ID
                    user = User.objects.get(apple_id=apple_id)
                    logger.info(f"Found existing test user by Apple ID: {apple_id}")
                except User.DoesNotExist:
                    try:
                        # Then try to find by email
                        user = User.objects.get(email=email)
                        logger.info(f"Found existing test user by email: {email}")
                        
                        # Update existing user with Apple info
                        user.apple_id = apple_id
                        user.is_apple_user = True
                        user.save()
                        
                    except User.DoesNotExist:
                        # Create new user
                        user = User.objects.create_user(
                            email=email,
                            first_name=first_name,
                            last_name=last_name,
                            apple_id=apple_id,
                            is_apple_user=True,
                            is_active=True
                        )
                        user_created = True
                        logger.info(f"Created new test Apple user: {email}")
            
            # Generate JWT tokens
            tokens = get_tokens_for_user(user)
            
            # Prepare response data
            response_data = {
                'message': 'Test Apple authentication successful',
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'is_apple_user': user.is_apple_user
                },
                'created': user_created
            }
            
            response = Response(response_data, status=status.HTTP_200_OK)
            return set_auth_cookies(response, tokens)
            
        except Exception as e:
            logger.error(f"Error in test Apple Sign In: {e}")
            return Response(
                {'error': 'Test authentication failed'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
