from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from datetime import datetime
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

# Create your models here.

class Greeting(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Greeting for {self.name}"

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, null=True, blank=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    
    # GitHub OAuth fields
    github_id = models.CharField(max_length=20, null=True, blank=True, unique=True)
    github_username = models.CharField(max_length=39, null=True, blank=True)  # GitHub max username length
    github_avatar_url = models.URLField(null=True, blank=True)
    is_github_user = models.BooleanField(default=False)

    # Apple Sign In fields
    apple_id = models.CharField(max_length=100, null=True, blank=True, unique=True)
    is_apple_user = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

class Project(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Message(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='messages')
    user_content = models.TextField(default="", help_text="User's message content")
    assistant_content = models.TextField(default="", help_text="Assistant's response content")
    liked = models.BooleanField(null=True, blank=True, default=None, help_text="True=liked, False=disliked, None=no action")
    user_feedback_message = models.TextField(null=True, blank=True, help_text="User feedback on AI messages")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Conversation {self.id} - {self.created_at}"

class Resource(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resources')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='resources')
    pdf_file = models.FileField(upload_to='resources/pdfs/', help_text="PDF file for RAG functionality")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Resource {self.id} - {self.project.name}"
