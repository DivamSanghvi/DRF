# DRF MVC Project with PDF RAG Integration

A Django REST Framework project that implements a Model-View-Controller (MVC) architecture with PDF processing and Retrieval-Augmented Generation (RAG) capabilities.

## Features

- **User Authentication**
  - JWT-based authentication
  - User registration and login
  - GitHub OAuth integration
  - Token refresh mechanism

- **Project Management**
  - Create, read, update, and delete projects
  - Smart auto-naming: projects without names get auto-generated names, then AI-powered renaming after first conversation
  - Project-specific chat conversations
  - Message history tracking

- **PDF Processing & RAG**
  - Upload and process multiple PDF files
  - Extract text using PyMuPDF and OCR (EasyOCR)
  - Language detection and support
  - Vector store creation using FAISS
  - Ensemble retrieval combining FAISS and BM25

- **Celery Background Processing**
  - Asynchronous PDF processing with Celery
  - Real-time status tracking (pending, processing, complete, failed)
  - Parallel processing of multiple PDF files
  - Automatic retry mechanisms for failed tasks

- **Chat Interface**
  - Real-time streaming responses
  - Context-aware responses using PDF content
  - Message feedback system (like/dislike)
  - User feedback on AI responses

## Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd drf
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   # On Windows
   .\venv\Scripts\activate
   # On Unix/MacOS
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the project root:
   ```
   GEMINI_API_KEY=your_gemini_api_key
   SECRET_KEY=your_django_secret_key
   
   # GitHub OAuth (optional)
   GITHUB_CLIENT_ID=your_github_app_client_id
   GITHUB_CLIENT_SECRET=your_github_app_client_secret
   GITHUB_REDIRECT_URI=http://localhost:8000/api/auth/github/callback/
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Start the development server**
   ```bash
   python manage.py runserver
   ```

7. **Start Celery worker (for PDF processing)**
   In a separate terminal, run:
   ```bash
   celery -A drf worker --loglevel=info --pool=solo
   ```
   
   > **Note**: This command must be run in the background to enable asynchronous PDF processing. Without Celery running, PDF uploads will fail to process.

## API Documentation

The API documentation is available at:
- Swagger UI: `http://127.0.0.1:8000/swagger/`
- ReDoc: `http://127.0.0.1:8000/redoc/`

### API Endpoints

#### General Endpoints
| Method | Endpoint | Description | Authentication Required |
|--------|----------|-------------|------------------------|
| GET | `/api/hello/` | Hello World message | No |
| GET | `/api/greet/?name=<name>` | Personalized greeting | No |

#### Authentication Endpoints
| Method | Endpoint | Description | Authentication Required | Request Body |
|--------|----------|-------------|------------------------|--------------|
| POST | `/api/auth/register/` | Register new user | No | `{"email": "user@example.com", "password": "password123", "password2": "password123"}` |
| POST | `/api/auth/login/` | User login with email/password | No | `{"email": "user@example.com", "password": "password123"}` |
| POST | `/api/auth/logout/` | User logout (clears cookies) | No | None |
| POST | `/api/auth/refresh/` | Refresh JWT access token | No | Uses refresh token from cookies |

#### GitHub OAuth Endpoints
| Method | Endpoint | Description | Authentication Required | Response |
|--------|----------|-------------|------------------------|----------|
| GET | `/api/auth/github/` | Get GitHub OAuth authorization URL | No | `{"auth_url": "https://github.com/login/oauth/authorize?..."}` |
| GET | `/api/auth/github/callback/` | Handle GitHub OAuth callback (sets cookies) | No | Redirected from GitHub with auth code |
| GET | `/api/auth/github/token/` | Handle GitHub OAuth callback (returns tokens) | No | `{"access_token": "...", "refresh_token": "..."}` |

#### Project Management Endpoints
| Method | Endpoint | Description | Authentication Required | Request Body |
|--------|----------|-------------|------------------------|--------------|
| POST | `/api/projects/create/` | Create new project (name optional) | Yes | `{"name": "My Project"}` or `{}` |
| GET | `/api/projects/` | List user's projects | Yes | None |
| GET | `/api/projects/<project_id>/` | Get specific project details | Yes | None |
| PUT | `/api/projects/<project_id>/update/` | Update project details | Yes | `{"name": "Updated Project Name"}` |
| DELETE | `/api/projects/<project_id>/delete/` | Delete project | Yes | None |

**Smart Project Naming**: When creating a project without a name, it auto-generates names like "Untitled1", "Untitled2", etc. After the first conversation in an untitled project, the system uses AI to automatically rename the project based on the conversation content (2-4 words, e.g., "React App Development").

#### Resource (PDF) Management Endpoints (Celery-Powered)
| Method | Endpoint | Description | Authentication Required | Request Body | Celery Task |
|--------|----------|-------------|------------------------|--------------|-------------|
| POST | `/api/projects/<project_id>/resources/add/` | Upload PDF files to project (async processing) | Yes | Form-data with `pdf_files` field(s) | `process_pdf_task` or `process_multiple_pdfs_task` |
| GET | `/api/projects/<project_id>/resources/` | List project's PDF resources with status | Yes | None | - |
| GET | `/api/projects/<project_id>/resources/<resource_id>/` | Get specific resource details with processing status | Yes | None | - |
| DELETE | `/api/projects/<project_id>/resources/<resource_id>/` | Delete resource and update vector store | Yes | None | - |

**Resource Status Tracking:**
- `pending`: Resource uploaded, waiting for processing
- `processing`: Celery is currently processing the PDF
- `complete`: PDF processed successfully and added to vector store
- `failed`: Processing failed (e.g., corrupted PDF, OCR failure)

### Optimized Message Structure

**Conversation Efficiency**: The system now stores user-assistant message pairs in a single database record for optimal performance. Each conversation turn (user message + AI response) creates one record with a single ID, reducing database hits from 2 to 1 per exchange.

**Conversation Format**:
```json
{
    "id": 1,
    "project": 123,
    "user_content": "User's question or message",
    "assistant_content": "AI's response to the user",
    "liked": null,
    "user_feedback_message": null,
    "created_at": "2024-01-01T12:00:00Z"
}
```

#### Chat & Messaging Endpoints
| Method | Endpoint | Description | Authentication Required | Request Body |
|--------|----------|-------------|------------------------|--------------|
| POST | `/api/projects/<project_id>/chat/` | Send message to AI (streaming response) | Yes | `{"message": "Your question here"}` |
| GET | `/api/projects/<project_id>/messages/` | Get conversation history for project | Yes | None |

#### Message Feedback Endpoints
| Method | Endpoint | Description | Authentication Required | Request Body Examples |
|--------|----------|-------------|------------------------|----------------------|
| GET | `/api/projects/<project_id>/messages/<conversation_id>/feedback/` | Get current feedback for a conversation | Yes | None |
| POST | `/api/projects/<project_id>/messages/<conversation_id>/feedback/` | Add reaction and/or text feedback | Yes | `{"reaction": "like"}`, `{"feedback_text": "Helpful response"}`, or `{"reaction": "dislike", "feedback_text": "Not accurate"}` |
| PUT | `/api/projects/<project_id>/messages/<conversation_id>/feedback/` | Update existing reaction and/or feedback | Yes | `{"reaction": "like"}`, `{"feedback_text": "Updated feedback"}`, or both |
| DELETE | `/api/projects/<project_id>/messages/<conversation_id>/feedback/` | Remove feedback (smart removal) | Yes | `{}` (all), `{"remove_reaction": true}` (reaction only), `{"remove_feedback_text": true}` (text only) |

**Feedback Options:**
- **Reactions**: `"like"`, `"dislike"`, or `"remove"` (to clear reaction)
- **Text Feedback**: Any string to provide detailed feedback on AI responses
- **Smart Deletion**: Only specify what you want to remove - other items are automatically preserved

#### Documentation Endpoints
| Method | Endpoint | Description | Authentication Required |
|--------|----------|-------------|------------------------|
| GET | `/swagger/` | Swagger UI documentation | No |
| GET | `/redoc/` | ReDoc documentation | No |
| GET | `/swagger.json` | OpenAPI JSON schema | No |
| GET | `/swagger.yaml` | OpenAPI YAML schema | No |

## Celery Background Processing

This application uses **Celery** for asynchronous background processing of PDF files. When users upload PDFs, the heavy processing tasks (text extraction, OCR, vector store creation) are handled in the background without blocking the API response.

### How It Works

1. **PDF Upload**: User uploads PDF files via `/api/projects/<project_id>/resources/add/`
2. **Immediate Response**: API returns immediately with resource records in `pending` status
3. **Background Processing**: Celery workers pick up the tasks and process PDFs
4. **Status Updates**: Resource status changes to `processing` → `complete` or `failed`
5. **Vector Store Integration**: Completed PDFs are automatically added to the project's vector store for RAG

### Celery Tasks

- **`process_pdf_task(resource_id)`**: Processes a single PDF file
- **`process_multiple_pdfs_task(resource_ids)`**: Processes multiple PDF files in parallel

### Configuration

Celery is configured to use SQLite as both broker and result backend for development:
```python
CELERY_BROKER_URL = 'sqla+sqlite:///celery.sqlite'
CELERY_RESULT_BACKEND = 'db+sqlite:///celery.sqlite'
```

### Running Celery

**Important**: You must run the Celery worker in a separate terminal for PDF processing to work:

```bash
# In your project directory (with virtual environment activated)
celery -A drf worker --loglevel=info --pool=solo
```

**Production Note**: For production deployment, consider using Redis or RabbitMQ as the message broker and configure proper worker management.

## GitHub OAuth Setup & Testing

### Prerequisites
1. Create a GitHub OAuth App at https://github.com/settings/applications/new
2. Set Authorization callback URL to: `http://localhost:8000/api/auth/github/callback/`
3. Add your GitHub app credentials to `.env` file

### Testing GitHub OAuth

#### Method 1: API Testing (ThunderClient/Postman)
```bash
# 1. Initiate OAuth
GET http://localhost:8000/api/auth/github/

# 2. Copy 'authorization_url' from response and visit in browser
# 3. Authorize the application on GitHub
# 4. Copy 'code' parameter from callback URL

# 5. Get tokens directly (easier for API testing)
GET http://localhost:8000/api/auth/github/token/?code=YOUR_CODE_HERE

# 6. Use access_token for authenticated requests
GET http://localhost:8000/api/projects/
Authorization: Bearer YOUR_ACCESS_TOKEN_HERE
```

#### Method 2: Browser Testing
```bash
# 1. Visit: http://localhost:8000/api/auth/github/
# 2. Copy authorization URL and visit in new tab
# 3. Authorize application
# 4. Check browser cookies (access_token, refresh_token)
# 5. Use cookies for subsequent API calls
```

### OAuth Flow Features
- **Smart User Management**: Links GitHub accounts to existing email users or creates new users
- **Security**: CSRF protection via state parameter, secure cookie settings
- **Token Consistency**: Same JWT tokens as email/password authentication
- **Seamless Integration**: GitHub users get full access to all protected endpoints

## Dependencies

Key packages used:
- Django & Django REST Framework
- PyMuPDF (fitz) for PDF processing
- EasyOCR for OCR capabilities
- LangChain for text processing
- FAISS for vector storage
- Sentence Transformers for embeddings
- Gemini API for AI responses
- Requests for GitHub OAuth API calls

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 