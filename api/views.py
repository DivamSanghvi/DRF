from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Greeting
from .controllers import get_greeting
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserRegistrationSerializer, UserLoginSerializer
from datetime import datetime, timedelta

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
        secure=True,  # for HTTPS
        samesite='Lax',
        max_age=300  # 5 minutes
    )
    
    # Set refresh token cookie
    response.set_cookie(
        'refresh_token',
        tokens['refresh'],
        httponly=True,
        secure=True,  # for HTTPS
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
