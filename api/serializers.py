from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import User, Project, Conversation, Message

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user

class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ('id', 'name', 'user', 'created_at')
        read_only_fields = ('user', 'created_at')

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ('id', 'conversation', 'role', 'content', 'created_at')
        read_only_fields = ('created_at',)

class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = ('id', 'project', 'title', 'created_at', 'updated_at', 'messages')
        read_only_fields = ('created_at', 'updated_at') 