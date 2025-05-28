from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Greeting
from .controllers import get_greeting

# Create your views here.

class HelloWorldView(APIView):
    def get(self, request):
        return Response({"message": "Hello, World!"})

class GreetingView(APIView):
    def get(self, request):
        name = request.query_params.get('name', 'World')
        greeting = get_greeting(name)
        Greeting.objects.create(name=name)
        return Response({'message': greeting})
