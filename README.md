# 🚀 DRF API Testing Guide

A comprehensive Django REST Framework API with JWT authentication, project management, and AI chat functionality.

## 📋 Table of Contents
- [Project Overview](#project-overview)
- [Features](#features)
- [Setup Instructions](#setup-instructions)
- [Database Information](#database-information)
- [API Endpoints](#api-endpoints)
- [Testing with Postman](#testing-with-postman)
- [Testing with Thunder Client](#testing-with-thunder-client)
- [Complete Testing Flow](#complete-testing-flow)
- [Troubleshooting](#troubleshooting)

## 🎯 Project Overview

This is a Django REST Framework (DRF) project that provides:
- User authentication with JWT tokens
- Project management system
- AI-powered chat functionality
- Message storage and retrieval
- RESTful API with Swagger documentation

## ✨ Features

- **JWT Authentication**: Secure login/logout with access & refresh tokens
- **User Registration**: Create new user accounts
- **Project Management**: Create and manage projects
- **AI Chat**: Send messages and get AI responses
- **Message History**: View all messages for a project
- **Swagger Documentation**: Interactive API documentation
- **Cookie-based Auth**: Automatic token handling via HTTP cookies

## 🛠️ Setup Instructions

### Prerequisites
- Python 3.8+
- Django 5.0.2
- Django REST Framework
- SQLite (default database)

### Installation
1. **Clone/Navigate to project directory**
   ```bash
   cd "C:\Users\yugtg\Desktop\169pi Tasks\New folder\DRF"
   ```

2. **Activate virtual environment**
   ```bash
   .venv\Scripts\activate  # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Start the server**
   ```bash
   python manage.py runserver
   ```

6. **Access the application**
   - API Base URL: `http://127.0.0.1:8000`
   - Swagger Documentation: `http://127.0.0.1:8000/swagger/`
   - Admin Panel: `http://127.0.0.1:8000/admin/`

## 🗄️ Database Information

- **Database**: SQLite
- **File Location**: `db.sqlite3` (project root)
- **Models**: User, Project, Message, Greeting

### View Database Entries
```bash
# Django shell
python manage.py shell

# In shell:
from api.models import User, Project, Message, Greeting
User.objects.all()
Greeting.objects.all()
Project.objects.all()
Message.objects.all()
```

## 🔗 API Endpoints

### 🔓 Public Endpoints (No Authentication Required)

| Method | Endpoint | Description | Body |
|--------|----------|-------------|------|
| GET | `/api/hello/` | Hello world message | None |
| GET | `/api/greet/?name=YourName` | Personalized greeting | None |

### 🔐 Authentication Endpoints

| Method | Endpoint | Description | Body |
|--------|----------|-------------|------|
| POST | `/api/auth/register/` | Register new user | `{"email": "user@example.com", "password": "123", "password2": "123"}` |
| POST | `/api/auth/login/` | User login | `{"email": "user@example.com", "password": "123"}` |
| POST | `/api/auth/logout/` | User logout | None |
| POST | `/api/auth/refresh/` | Refresh JWT token | None (uses cookies) |

### 📁 Project Endpoints (Authentication Required)

| Method | Endpoint | Description | Body |
|--------|----------|-------------|------|
| POST | `/api/projects/create/` | Create new project | `{"name": "My Project"}` |
| GET | `/api/projects/` | List all user projects | None |
| PUT | `/api/projects/{id}/update/` | Update existing project | `{"name": "Updated Project Name"}` |
| DELETE | `/api/projects/{id}/delete/` | Delete project | None |

### 💬 Message/Chat Endpoints (Authentication Required)

| Method | Endpoint | Description | Body |
|--------|----------|-------------|------|
| GET | `/api/projects/{id}/messages/` | Get all messages for project | None |
| POST | `/api/projects/{id}/chat/` | Send message to AI (streaming by default) | `{"message": "Hello AI"}` or `{"message": "Hello AI", "stream": false}` |
| POST | `/api/projects/{id}/messages/{message_id}/like/` | Like an AI message | None |
| POST | `/api/projects/{id}/messages/{message_id}/dislike/` | Dislike an AI message | None |
| DELETE | `/api/projects/{id}/messages/{message_id}/reaction/` | Remove like/dislike reaction | None |
| POST | `/api/projects/{id}/messages/{message_id}/feedback/` | Add feedback to an AI message | `{"feedback": "This was helpful!"}` |
| PUT | `/api/projects/{id}/messages/{message_id}/feedback/update/` | Update feedback on an AI message | `{"feedback": "Updated feedback text"}` |
| DELETE | `/api/projects/{id}/messages/{message_id}/feedback/remove/` | Remove feedback from an AI message | None |

### 📄 Resource Endpoints (Authentication Required)

| Method | Endpoint | Description | Body |
|--------|----------|-------------|------|
| GET | `/api/projects/{id}/resources/` | Get all PDF resources for project | None |
| POST | `/api/projects/{id}/resources/upload/` | Upload PDF resource for RAG | Form-data with `pdf_file` |
| DELETE | `/api/projects/{id}/resources/{resource_id}/delete/` | Delete PDF resource | None |

#### 📡 Chat Endpoint Details

**Default Behavior (Streaming):**
- Request: `{"message": "Your question"}`
- Response: Server-Sent Events (SSE) stream with real-time chunks

**Non-Streaming Response:**
- Request: `{"message": "Your question", "stream": false}`
- Response: Single JSON object with user_message and ai_response

**Stream Parameter Options:**
- `stream: true` or omitted → Streaming response (SSE format)
- `stream: false` → Traditional JSON response
- Also accepts: `"false"`, `"0"`, `"no"`, `"off"` as false values

## 🧪 Testing with Postman

### Setup
1. **Download Postman**: https://www.postman.com/downloads/
2. **Create a new collection**: "DRF API Tests"
3. **Set up environment variables**:
   - `base_url`: `http://127.0.0.1:8000`
   - `access_token`: (will be set automatically)

### Environment Setup
```json
{
  "base_url": "http://127.0.0.1:8000",
  "access_token": "",
  "project_id": ""
}
```

### Headers Template
For authenticated requests:
```
Content-Type: application/json
Authorization: Bearer {{access_token}}
```

## ⚡ Testing with Thunder Client (VS Code)

### Setup
1. **Install Thunder Client extension** in VS Code
2. **Create new collection**: "DRF API Tests"
3. **Set up environment**:
   ```json
   {
     "base_url": "http://127.0.0.1:8000",
     "access_token": "",
     "project_id": ""
   }
   ```

## 🎯 Complete Testing Flow

### Phase 1: Public Endpoints
#### Test 1.1: Hello World
```
Method: GET
URL: {{base_url}}/api/hello/
Headers: None
Body: None

Expected Response (200):
{
    "message": "Hello, World!"
}
```

#### Test 1.2: Greeting (Default)
```
Method: GET
URL: {{base_url}}/api/greet/
Headers: None
Body: None

Expected Response (200):
{
    "message": "Hello, World! Welcome to the DRF MVC project."
}
```

#### Test 1.3: Greeting (Custom Name)
```
Method: GET
URL: {{base_url}}/api/greet/?name=Alice
Headers: None
Body: None

Expected Response (200):
{
    "message": "Hello, Alice! Welcome to the DRF MVC project."
}
```

### Phase 2: User Authentication

#### Test 2.1: User Registration
```
Method: POST
URL: {{base_url}}/api/auth/register/
Headers:
Content-Type: application/json

Body (JSON):
{
    "email": "test@example.com",
    "password": "123",
    "password2": "123"
}

Expected Response (201):
{
    "user": {
        "id": 1,
        "email": "test@example.com"
    },
    "message": "Registration successful"
}
```

#### Test 2.2: User Login
```
Method: POST
URL: {{base_url}}/api/auth/login/
Headers:
Content-Type: application/json

Body (JSON):
{
    "email": "test@example.com",
    "password": "123"
}

Expected Response (200):
{
    "message": "Login successful"
}

Note: Tokens are automatically set in cookies
```

#### Test 2.3: Token Refresh
```
Method: POST
URL: {{base_url}}/api/auth/refresh/
Headers: None (uses cookies)
Body: None

Expected Response (200):
{
    "message": "Token refreshed successfully"
}
```

#### Test 2.4: User Logout
```
Method: POST
URL: {{base_url}}/api/auth/logout/
Headers: None
Body: None

Expected Response (200):
{
    "message": "Logout successful"
}
```

### Phase 3: Project Management

#### Test 3.1: Login First (Required for authenticated endpoints)
```
Method: POST
URL: {{base_url}}/api/auth/login/
Headers:
Content-Type: application/json

Body (JSON):
{
    "email": "test@example.com",
    "password": "123"
}
```

#### Test 3.2: Create Project
```
Method: POST
URL: {{base_url}}/api/projects/create/
Headers:
Content-Type: application/json
Authorization: Bearer {{access_token}}

Body (JSON):
{
    "name": "My AI Chat Project"
}

Expected Response (201):
{
    "id": 1,
    "name": "My AI Chat Project",
    "user": 1,
    "created_at": "2025-06-04T18:30:00.123456Z"
}

Save project_id: 1 for next tests
```

#### Test 3.3: List All Projects
```
Method: GET
URL: {{base_url}}/api/projects/
Headers:
Authorization: Bearer {{access_token}}
Body: None

Expected Response (200):
[
    {
        "id": 1,
        "name": "My AI Chat Project",
        "user": 1,
        "created_at": "2025-06-04T18:30:00.123456Z"
    }
]
```

#### Test 3.4: Update Project
```
Method: PUT
URL: {{base_url}}/api/projects/1/update/
Headers:
Content-Type: application/json
Authorization: Bearer {{access_token}}

Body (JSON):
{
    "name": "Updated AI Chat Project"
}

Expected Response (200):
{
    "id": 1,
    "name": "Updated AI Chat Project",
    "user": 1,
    "created_at": "2025-06-04T18:30:00.123456Z"
}

Note: Only the user who created the project can update it
```

#### Test 3.5: Delete Project
```
Method: DELETE
URL: {{base_url}}/api/projects/1/delete/
Headers:
Authorization: Bearer {{access_token}}
Body: None

Expected Response (200):
{
    "message": "Project deleted successfully"
}

Note: This permanently deletes the project and all its messages
Warning: Only the user who created the project can delete it
```

### Phase 4: Chat Functionality

⚠️ **Important: Streaming is the default behavior for chat responses!**

The chat endpoint supports two modes:
- **Streaming (Default)**: Real-time response chunks via Server-Sent Events (SSE)
- **Non-Streaming**: Traditional single JSON response

#### Test 4.1: Send Message with Default Streaming
```
Method: POST
URL: {{base_url}}/api/projects/1/chat/
Headers:
Content-Type: application/json
Authorization: Bearer {{access_token}}

Body (JSON):
{
    "message": "Hello AI, how are you?"
}

Expected Response (Streaming - SSE format):
data: {"chunk": "Hello"}

data: {"chunk": "! I'm"}

data: {"chunk": " doing"}

data: {"chunk": " well,"}

data: {"chunk": " thank"}

data: {"chunk": " you"}

data: {"chunk": " for"}

data: {"chunk": " asking"}

data: {"chunk": "..."}

data: {"done": true, "message": {"id": 2, "project": 1, "role": "assistant", "content": "Hello! I'm doing well, thank you for asking...", "liked": null, "created_at": "2025-06-04T18:31:01.123456Z"}}

Note: Response is streamed in real-time as chunks
```

#### Test 4.1b: Send Message with Explicit Streaming
```
Method: POST
URL: {{base_url}}/api/projects/1/chat/
Headers:
Content-Type: application/json
Authorization: Bearer {{access_token}}

Body (JSON):
{
    "message": "Hello AI, how are you?",
    "stream": true
}

Expected Response: Same as above (streaming format)
```

#### Test 4.1c: Send Message with Non-Streaming Response
```
Method: POST
URL: {{base_url}}/api/projects/1/chat/
Headers:
Content-Type: application/json
Authorization: Bearer {{access_token}}

Body (JSON):
{
    "message": "Hello AI, how are you?",
    "stream": false
}

Expected Response (200 - Single JSON):
{
    "user_message": {
        "id": 1,
        "project": 1,
        "role": "user",
        "content": "Hello AI, how are you?",
        "liked": null,
        "created_at": "2025-06-04T18:31:00.123456Z"
    },
    "ai_response": {
        "id": 2,
        "project": 1,
        "role": "assistant",
        "content": "Hello! I'm doing well, thank you for asking...",
        "liked": null,
        "created_at": "2025-06-04T18:31:01.123456Z"
    }
}
```

#### 📡 How to Consume Streaming Responses

**JavaScript (EventSource API):**
```javascript
// For streaming responses
const eventSource = new EventSource('/api/projects/1/chat/');

eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.chunk) {
        // Handle streaming chunk
        console.log('Received chunk:', data.chunk);
        // Append to your UI in real-time
    } else if (data.done) {
        // Handle complete message
        console.log('Complete message:', data.message);
        eventSource.close();
    } else if (data.error) {
        // Handle error
        console.error('Error:', data.error);
        eventSource.close();
    }
};

eventSource.onerror = (error) => {
    console.error('EventSource error:', error);
    eventSource.close();
};
```

**Postman Testing:**
- **Streaming**: You'll see multiple lines of SSE data in the response
- **Non-Streaming**: You'll see a single JSON object response

#### Test 4.2: Send Another Message (Streaming)
```
Method: POST
URL: {{base_url}}/api/projects/1/chat/
Headers:
Content-Type: application/json
Authorization: Bearer {{access_token}}

Body (JSON):
{
    "message": "What can you help me with?"
}

Expected Response (Streaming - SSE format):
data: {"chunk": "I"}

data: {"chunk": " can"}

data: {"chunk": " help"}

data: {"chunk": " you"}

data: {"chunk": " with"}

data: {"chunk": " a"}

data: {"chunk": " variety"}

data: {"chunk": " of"}

data: {"chunk": " tasks..."}

data: {"done": true, "message": {"id": 4, "project": 1, "role": "assistant", "content": "I can help you with a variety of tasks...", "liked": null, "created_at": "2025-06-04T18:32:01.123456Z"}}

Note: Response is streamed in real-time as chunks
```

#### Test 4.3: Get All Messages for Project
```
Method: GET
URL: {{base_url}}/api/projects/1/messages/
Headers:
Authorization: Bearer {{access_token}}
Body: None

Expected Response (200):
[
    {
        "id": 1,
        "project": 1,
        "role": "user",
        "content": "Hello AI, how are you?",
        "liked": null,
        "created_at": "2025-06-04T18:31:00.123456Z"
    },
    {
        "id": 2,
        "project": 1,
        "role": "assistant",
        "content": "Hello! I'm doing well, thank you for asking...",
        "liked": null,
        "created_at": "2025-06-04T18:31:01.123456Z"
    },
    {
        "id": 3,
        "project": 1,
        "role": "user",
        "content": "What can you help me with?",
        "liked": null,
        "created_at": "2025-06-04T18:32:00.123456Z"
    },
    {
        "id": 4,
        "project": 1,
        "role": "assistant",
        "content": "I can help you with a variety of tasks...",
        "liked": null,
        "created_at": "2025-06-04T18:32:01.123456Z"
    }
]
```

#### Test 4.4: Like an AI Message
```
Method: POST
URL: {{base_url}}/api/projects/1/messages/2/like/
Headers:
Authorization: Bearer {{access_token}}
Body: None

Expected Response (200):
{
    "message": "Message liked successfully",
    "liked": true
}

Note: Only AI messages (role='assistant') can be liked/disliked
```

#### Test 4.5: Dislike an AI Message
```
Method: POST
URL: {{base_url}}/api/projects/1/messages/4/dislike/
Headers:
Authorization: Bearer {{access_token}}
Body: None

Expected Response (200):
{
    "message": "Message disliked successfully",
    "liked": false
}
```

#### Test 4.6: Remove Reaction from AI Message
```
Method: DELETE
URL: {{base_url}}/api/projects/1/messages/2/reaction/
Headers:
Authorization: Bearer {{access_token}}
Body: None

Expected Response (200):
{
    "message": "Reaction removed successfully",
    "liked": null
}
```

#### Test 4.7: Verify Reactions in Message List
```
Method: GET
URL: {{base_url}}/api/projects/1/messages/
Headers:
Authorization: Bearer {{access_token}}
Body: None

Expected Response (200):
[
    {
        "id": 1,
        "project": 1,
        "role": "user",
        "content": "Hello AI, how are you?",
        "liked": null,
        "created_at": "2025-06-04T18:31:00.123456Z"
    },
    {
        "id": 2,
        "project": 1,
        "role": "assistant",
        "content": "Hello! I'm doing well, thank you for asking...",
        "liked": null,
        "created_at": "2025-06-04T18:31:01.123456Z"
    },
    {
        "id": 3,
        "project": 1,
        "role": "user",
        "content": "What can you help me with?",
        "liked": null,
        "created_at": "2025-06-04T18:32:00.123456Z"
    },
    {
        "id": 4,
        "project": 1,
        "role": "assistant",
        "content": "I can help you with a variety of tasks...",
        "liked": false,
        "created_at": "2025-06-04T18:32:01.123456Z"
    }
]

Note: Message 2 reaction was removed (null), Message 4 is disliked (false)
```

#### Test 4.8: Try to Like User Message (Error Case)
```
Method: POST
URL: {{base_url}}/api/projects/1/messages/1/like/
Headers:
Authorization: Bearer {{access_token}}
Body: None

Expected Response (400):
{
    "error": "Only AI messages can be liked"
}
```

### Phase 4.6: Message Feedback

#### Test 4.9: Add Feedback to AI Message
```
Method: POST
URL: {{base_url}}/api/projects/1/messages/2/feedback/
Headers:
Content-Type: application/json
Authorization: Bearer {{access_token}}

Body (JSON):
{
    "feedback": "This response was very helpful and detailed!"
}

Expected Response (200):
{
    "message": "Feedback added successfully",
    "user_feedback_message": "This response was very helpful and detailed!"
}

Note: Only AI messages (role='assistant') can receive feedback
```

#### Test 4.10: Update Feedback on AI Message
```
Method: PUT
URL: {{base_url}}/api/projects/1/messages/2/feedback/update/
Headers:
Content-Type: application/json
Authorization: Bearer {{access_token}}

Body (JSON):
{
    "feedback": "Updated: This response was extremely helpful and very detailed!"
}

Expected Response (200):
{
    "message": "Feedback updated successfully",
    "user_feedback_message": "Updated: This response was extremely helpful and very detailed!"
}
```

#### Test 4.11: Remove Feedback from AI Message
```
Method: DELETE
URL: {{base_url}}/api/projects/1/messages/2/feedback/remove/
Headers:
Authorization: Bearer {{access_token}}
Body: None

Expected Response (200):
{
    "message": "Feedback removed successfully",
    "user_feedback_message": null
}
```

#### Test 4.12: Try to Add Feedback to User Message (Error Case)
```
Method: POST
URL: {{base_url}}/api/projects/1/messages/1/feedback/
Headers:
Content-Type: application/json
Authorization: Bearer {{access_token}}

Body (JSON):
{
    "feedback": "This shouldn't work"
}

Expected Response (400):
{
    "error": "Only AI messages can receive feedback"
}
```

#### Test 4.13: Try to Add Feedback When Feedback Already Exists (Error Case)
```
Method: POST
URL: {{base_url}}/api/projects/1/messages/4/feedback/
Headers:
Content-Type: application/json
Authorization: Bearer {{access_token}}

Body (JSON):
{
    "feedback": "First feedback"
}

Expected Response (200):
{
    "message": "Feedback added successfully",
    "user_feedback_message": "First feedback"
}

# Then try to add again
Method: POST
URL: {{base_url}}/api/projects/1/messages/4/feedback/
Headers:
Content-Type: application/json
Authorization: Bearer {{access_token}}

Body (JSON):
{
    "feedback": "Second feedback"
}

Expected Response (400):
{
    "error": "Feedback already exists. Use update endpoint to modify."
}
```

#### Test 4.14: Verify Feedback in Message List
```
Method: GET
URL: {{base_url}}/api/projects/1/messages/
Headers:
Authorization: Bearer {{access_token}}
Body: None

Expected Response (200):
[
    {
        "id": 1,
        "project": 1,
        "role": "user",
        "content": "Hello AI, how are you?",
        "liked": null,
        "user_feedback_message": null,
        "created_at": "2025-06-04T18:31:00.123456Z"
    },
    {
        "id": 2,
        "project": 1,
        "role": "assistant",
        "content": "Hello! I'm doing well, thank you for asking...",
        "liked": null,
        "user_feedback_message": null,
        "created_at": "2025-06-04T18:31:01.123456Z"
    },
    {
        "id": 3,
        "project": 1,
        "role": "user",
        "content": "What can you help me with?",
        "liked": null,
        "user_feedback_message": null,
        "created_at": "2025-06-04T18:32:00.123456Z"
    },
    {
        "id": 4,
        "project": 1,
        "role": "assistant",
        "content": "I can help you with a variety of tasks...",
        "liked": false,
        "user_feedback_message": "First feedback",
        "created_at": "2025-06-04T18:32:01.123456Z"
    }
]

Note: Message 2 feedback was removed (null), Message 4 has feedback
```

### Phase 4.7: Resource Management (PDF RAG)

#### Test 4.15: Get Project Resources (Initially Empty)
```
Method: GET
URL: {{base_url}}/api/projects/1/resources/
Headers:
Authorization: Bearer {{access_token}}
Body: None

Expected Response (200):
[]

Note: Initially empty array since no resources have been uploaded yet
```

#### Test 4.16: Upload PDF Resource
```
Method: POST
URL: {{base_url}}/api/projects/1/resources/upload/
Headers:
Authorization: Bearer {{access_token}}
Body: Form-data
pdf_file: [Select a PDF file]

Expected Response (201):
{
    "id": 1,
    "user": 1,
    "project": 1,
    "pdf_file": "/media/resources/pdfs/your_file.pdf",
    "created_at": "2025-06-05T02:45:00.123456Z"
}

Note: Use form-data, not JSON. Select a PDF file for the pdf_file field.
```

#### Test 4.17: Get Project Resources (After Upload)
```
Method: GET
URL: {{base_url}}/api/projects/1/resources/
Headers:
Authorization: Bearer {{access_token}}
Body: None

Expected Response (200):
[
    {
        "id": 1,
        "user": 1,
        "project": 1,
        "pdf_file": "/media/resources/pdfs/your_file.pdf",
        "created_at": "2025-06-05T02:45:00.123456Z"
    }
]

Note: Shows the uploaded PDF resource in the list
```

#### Test 4.18: Try to Upload Non-PDF File (Error Case)
```
Method: POST
URL: {{base_url}}/api/projects/1/resources/upload/
Headers:
Authorization: Bearer {{access_token}}
Body: Form-data
pdf_file: [Select a non-PDF file like .txt or .jpg]

Expected Response (400):
{
    "error": "Only PDF files are allowed"
}
```

#### Test 4.19: Try to Upload Without File (Error Case)
```
Method: POST
URL: {{base_url}}/api/projects/1/resources/upload/
Headers:
Authorization: Bearer {{access_token}}
Body: Form-data
(no pdf_file field)

Expected Response (400):
{
    "error": "PDF file is required"
}
```

#### Test 4.20: Delete PDF Resource
```
Method: DELETE
URL: {{base_url}}/api/projects/1/resources/1/delete/
Headers:
Authorization: Bearer {{access_token}}
Body: None

Expected Response (200):
{
    "message": "Resource deleted successfully"
}

Note: Replace "1" with the actual resource ID from the upload response
```

#### Test 4.21: Try to Delete Non-existent Resource (Error Case)
```
Method: DELETE
URL: {{base_url}}/api/projects/1/resources/999/delete/
Headers:
Authorization: Bearer {{access_token}}
Body: None

Expected Response (404):
{
    "error": "Resource not found"
}
```

### Phase 5: Multiple Projects Testing

#### Test 5.1: Create Second Project
```
Method: POST
URL: {{base_url}}/api/projects/create/
Headers:
Content-Type: application/json
Authorization: Bearer {{access_token}}

Body (JSON):
{
    "name": "Second Project"
}

Expected Response (201):
{
    "id": 2,
    "name": "Second Project",
    "user": 1,
    "created_at": "2025-06-04T18:33:00.123456Z"
}
```

#### Test 5.2: Chat in Second Project
```
Method: POST
URL: {{base_url}}/api/projects/2/chat/
Headers:
Content-Type: application/json
Authorization: Bearer {{access_token}}

Body (JSON):
{
    "message": "This is a message in the second project"
}

Expected Response (200):
{
    "user_message": {
        "id": 5,
        "project": 2,
        "role": "user",
        "content": "This is a message in the second project",
        "created_at": "2025-06-04T18:33:30.123456Z"
    },
    "ai_response": {
        "id": 6,
        "project": 2,
        "role": "assistant",
        "content": "I understand this is your second project...",
        "created_at": "2025-06-04T18:33:31.123456Z"
    }
}
```

#### Test 5.3: Verify Project Isolation
```
Method: GET
URL: {{base_url}}/api/projects/2/messages/
Headers:
Authorization: Bearer {{access_token}}
Body: None

Expected Response (200):
[
    {
        "id": 5,
        "project": 2,
        "role": "user",
        "content": "This is a message in the second project",
        "created_at": "2025-06-04T18:33:30.123456Z"
    },
    {
        "id": 6,
        "project": 2,
        "role": "assistant",
        "content": "I understand this is your second project...",
        "created_at": "2025-06-04T18:33:31.123456Z"
    }
]
```

## 🔧 Error Handling Tests

### Test Error Cases

#### Test E1: Invalid Login
```
Method: POST
URL: {{base_url}}/api/auth/login/
Body: {"email": "wrong@email.com", "password": "wrongpass"}

Expected Response (401):
{
    "error": "Invalid credentials"
}
```

#### Test E2: Missing Authentication
```
Method: POST
URL: {{base_url}}/api/projects/create/
Headers: (No Authorization header)
Body: {"name": "Test"}

Expected Response (401):
{
    "detail": "Authentication credentials were not provided."
}
```

#### Test E3: Project Not Found
```
Method: GET
URL: {{base_url}}/api/projects/999/messages/
Headers: Authorization: Bearer {{access_token}}

Expected Response (404):
{
    "error": "Project not found"
}
```

#### Test E4: Password Mismatch
```
Method: POST
URL: {{base_url}}/api/auth/register/
Body: {"email": "test2@example.com", "password": "123", "password2": "456"}

Expected Response (400):
{
    "password": ["Password fields didn't match."]
}
```

## 🛠️ Troubleshooting

### Common Issues

#### 1. Server Not Running
**Error**: Connection refused
**Solution**: 
```bash
python manage.py runserver
```

#### 2. Authentication Errors
**Error**: "Authentication credentials were not provided"
**Solutions**:
- Login first: `POST /api/auth/login/`
- Check Authorization header: `Bearer {token}`
- Verify cookies are being sent

#### 3. Database Issues
**Error**: Database locked or migration errors
**Solutions**:
```bash
python manage.py makemigrations
python manage.py migrate
```

#### 4. CORS Issues
**Error**: Cross-origin request blocked
**Solution**: Already configured with `CORS_ALLOW_ALL_ORIGINS = True`

#### 5. Token Expired
**Error**: Token is invalid or expired
**Solution**: Use refresh token endpoint:
```
POST /api/auth/refresh/
```

### Status Codes Reference

| Code | Status | Description |
|------|--------|-------------|
| 200 | OK | Success |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid data sent |
| 401 | Unauthorized | Authentication required |
| 404 | Not Found | Resource not found |
| 500 | Internal Server Error | Server error |

## 📊 Expected Response Formats

### Success Response
```json
{
    "data": {...},
    "message": "Operation successful"
}
```

### Error Response
```json
{
    "error": "Error description",
    "detail": "More specific error information"
}
```

### Validation Error Response
```json
{
    "field_name": ["Error message for this field"],
    "another_field": ["Another error message"]
}
```

## 🎯 Testing Checklist

- [ ] ✅ Hello World endpoint works
- [ ] ✅ Greeting endpoint works (default and custom name)
- [ ] ✅ User registration works
- [ ] ✅ User login works
- [ ] ✅ Token refresh works
- [ ] ✅ User logout works
- [ ] ✅ Project creation works
- [ ] ✅ Project listing works
- [ ] ✅ AI chat works (streaming and non-streaming)
- [ ] ✅ Message retrieval works
- [ ] ✅ Message like/dislike functionality works
- [ ] ✅ Message feedback functionality works (add/update/remove)
- [ ] ✅ PDF resource upload and delete functionality works
- [ ] ✅ Multiple projects work independently
- [ ] ✅ Authentication errors handled properly
- [ ] ✅ 404 errors handled properly
- [ ] ✅ Validation errors handled properly

## 🚀 Quick Start Commands

```bash
# Start server
python manage.py runserver

# Create superuser (for admin access)
python manage.py createsuperuser

# Access endpoints
curl -X GET "http://127.0.0.1:8000/api/hello/"
curl -X GET "http://127.0.0.1:8000/api/greet/?name=Test"

# Register user
curl -X POST "http://127.0.0.1:8000/api/auth/register/" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"123","password2":"123"}'

# Login
curl -X POST "http://127.0.0.1:8000/api/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"123"}'
```

## 📚 Additional Resources

- **Swagger Documentation**: `http://127.0.0.1:8000/swagger/`
- **ReDoc Documentation**: `http://127.0.0.1:8000/redoc/`
- **Django Admin**: `http://127.0.0.1:8000/admin/`
- **Django REST Framework Docs**: https://www.django-rest-framework.org/
- **Postman Documentation**: https://learning.postman.com/
- **Thunder Client Docs**: https://www.thunderclient.com/

---

**Happy Testing! 🎉**

For any issues or questions, check the troubleshooting section or refer to the error handling examples above. 