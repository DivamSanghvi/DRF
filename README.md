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
  - Project-specific chat conversations
  - Message history tracking

- **PDF Processing & RAG**
  - Upload and process multiple PDF files
  - Extract text using PyMuPDF and OCR (EasyOCR)
  - Language detection and support
  - Vector store creation using FAISS
  - Ensemble retrieval combining FAISS and BM25

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
| POST | `/api/projects/create/` | Create new project | Yes | `{"name": "My Project"}` |
| GET | `/api/projects/` | List user's projects | Yes | None |
| PUT | `/api/projects/<project_id>/update/` | Update project details | Yes | `{"name": "Updated Project Name"}` |
| DELETE | `/api/projects/<project_id>/delete/` | Delete project | Yes | None |

#### Resource (PDF) Management Endpoints
| Method | Endpoint | Description | Authentication Required | Request Body |
|--------|----------|-------------|------------------------|--------------|
| POST | `/api/projects/<project_id>/resources/add/` | Upload PDF files to project | Yes | Form-data with `pdf_file` field(s) |
| GET | `/api/projects/<project_id>/resources/` | List project's PDF resources | Yes | None |
| GET | `/api/projects/<project_id>/resources/<resource_id>/` | Get specific resource details | Yes | None |
| PATCH | `/api/projects/<project_id>/resources/<resource_id>/` | Update resource metadata | Yes | `{"metadata": "..."}` |
| DELETE | `/api/projects/<project_id>/resources/<resource_id>/` | Delete resource | Yes | None |

#### Chat & Messaging Endpoints
| Method | Endpoint | Description | Authentication Required | Request Body |
|--------|----------|-------------|------------------------|--------------|
| POST | `/api/projects/<project_id>/chat/` | Send message to AI (streaming response) | Yes | `{"message": "Your question here"}` |
| GET | `/api/projects/<project_id>/messages/` | Get chat history for project | Yes | None |

#### Message Feedback Endpoints
| Method | Endpoint | Description | Authentication Required | Request Body |
|--------|----------|-------------|------------------------|--------------|
| POST | `/api/projects/<project_id>/messages/<message_id>/feedback/` | Add reaction and/or text feedback | Yes | `{"reaction": "like", "feedback_text": "This was helpful"}` |
| PUT | `/api/projects/<project_id>/messages/<message_id>/feedback/` | Update existing reaction and/or feedback | Yes | `{"reaction": "dislike", "feedback_text": "Updated feedback"}` |
| DELETE | `/api/projects/<project_id>/messages/<message_id>/feedback/` | Remove feedback (all or specific parts) | Yes | `{"remove_reaction": true, "remove_feedback_text": false}` or `{}` for all |

#### Documentation Endpoints
| Method | Endpoint | Description | Authentication Required |
|--------|----------|-------------|------------------------|
| GET | `/swagger/` | Swagger UI documentation | No |
| GET | `/redoc/` | ReDoc documentation | No |
| GET | `/swagger.json` | OpenAPI JSON schema | No |
| GET | `/swagger.yaml` | OpenAPI YAML schema | No |

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