from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import User, Project, Message, Resource
from django.db.models import Q

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'password', 'password2')
        extra_kwargs = {'password': {'write_only': True}}

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2', None)
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user

class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

class ProjectSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    
    class Meta:
        model = Project
        fields = ('id', 'name', 'user', 'created_at')
        read_only_fields = ('user', 'created_at')
    
    def create(self, validated_data):
        # If no name provided or name is empty, generate auto name
        if not validated_data.get('name') or not validated_data.get('name').strip():
            user = validated_data.get('user')
            # Find existing untitled projects for this user
            untitled_projects = Project.objects.filter(
                user=user,
                name__regex=r'^Untitled\d*$'
            ).order_by('name')
            
            # Generate next untitled number
            if not untitled_projects.exists():
                validated_data['name'] = 'Untitled1'
            else:
                # Extract numbers from existing untitled projects
                numbers = []
                for project in untitled_projects:
                    if project.name == 'Untitled':
                        numbers.append(0)
                    elif project.name.startswith('Untitled'):
                        try:
                            num = int(project.name[8:])  # Remove 'Untitled' prefix
                            numbers.append(num)
                        except ValueError:
                            continue
                
                # Find next available number
                next_num = 1
                while next_num in numbers:
                    next_num += 1
                
                validated_data['name'] = f'Untitled{next_num}'
        
        return super().create(validated_data)

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ('id', 'project', 'user_content', 'assistant_content', 'liked', 'user_feedback_message', 'created_at')
        read_only_fields = ('created_at',)

class ResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resource
        fields = ('id', 'user', 'project', 'pdf_file', 'created_at')
        read_only_fields = ('user', 'created_at') 