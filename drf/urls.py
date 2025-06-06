"""
URL configuration for drf project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path, include
from django.conf import settings
from django.conf.urls.static import static
from api.views import (
    GreetingView, 
    HelloWorldView, 
    UserRegistrationView, 
    UserLoginView,
    LogoutView,
    RefreshTokenView,
    ProjectCreateView,
    ProjectListView,
    ProjectUpdateView,
    ProjectDeleteView,
    MessageView,
    MessageReactionView,
    MessageAddFeedbackView,
    MessageUpdateFeedbackView,
    MessageRemoveFeedbackView,
    ProjectChatView,
    ResourceAddView,
    ResourceView
)
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Define schema view first
schema_view = get_schema_view(
    openapi.Info(
        title="DRF MVC API with PDF RAG",
        default_version='v1',
        description="""
        A Django REST Framework API that implements a Model-View-Controller (MVC) architecture with PDF processing and Retrieval-Augmented Generation (RAG) capabilities.

        ## Features
        - User Authentication (JWT)
        - Project Management
        - PDF Processing & RAG
        - Real-time Chat with Context Awareness
        - Message Feedback System

        ## Authentication
        All endpoints except registration and login require JWT authentication.
        Include the JWT token in the Authorization header or use cookies.

        ## PDF Processing
        - Supports multiple PDF uploads
        - Automatic text extraction
        - OCR for scanned documents
        - Language detection
        - Vector store creation

        ## Chat Features
        - Real-time streaming responses
        - Context-aware responses using PDF content
        - Message feedback system
        - User feedback on AI responses
        """,
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(
            email="contact@example.com",
            name="API Support",
            url="https://github.com/yourusername/drf"
        ),
        license=openapi.License(
            name="MIT License",
            url="https://opensource.org/licenses/MIT"
        ),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

# Define URL patterns
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/greet/', GreetingView.as_view(), name='greet'),
    path('api/hello/', HelloWorldView.as_view(), name='hello'),
    path('api/auth/register/', UserRegistrationView.as_view(), name='register'),
    path('api/auth/login/', UserLoginView.as_view(), name='login'),
    path('api/auth/logout/', LogoutView.as_view(), name='logout'),
    path('api/auth/refresh/', RefreshTokenView.as_view(), name='refresh'),
    path('api/projects/create/', ProjectCreateView.as_view(), name='project_create'),
    path('api/projects/', ProjectListView.as_view(), name='project_list'),
    path('api/projects/<int:project_id>/update/', ProjectUpdateView.as_view(), name='project_update'),
    path('api/projects/<int:project_id>/delete/', ProjectDeleteView.as_view(), name='project_delete'),
    path('api/projects/<int:project_id>/messages/', MessageView.as_view(), name='messages'),
    path('api/projects/<int:project_id>/messages/<int:message_id>/reaction/', MessageReactionView.as_view(), name='message_reaction'),
    path('api/projects/<int:project_id>/messages/<int:message_id>/feedback/', MessageAddFeedbackView.as_view(), name='message_feedback'),
    path('api/projects/<int:project_id>/messages/<int:message_id>/feedback/update/', MessageUpdateFeedbackView.as_view(), name='message_feedback_update'),
    path('api/projects/<int:project_id>/messages/<int:message_id>/feedback/remove/', MessageRemoveFeedbackView.as_view(), name='message_feedback_remove'),
    path('api/projects/<int:project_id>/chat/', ProjectChatView.as_view(), name='chat'),
    path('api/projects/<int:project_id>/resources/', ResourceView.as_view(), name='resource_list'),
    path('api/projects/<int:project_id>/resources/add/', ResourceAddView.as_view(), name='resource_add'),
    path('api/projects/<int:project_id>/resources/<int:resource_id>/', ResourceView.as_view(), name='resource_detail'),
    
    # Swagger URLs
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# Add media URLs in debug mode
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
