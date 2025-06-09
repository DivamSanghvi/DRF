# DRF MVC Project with PDF RAG Integration

A Django REST Framework project that implements a Model-View-Controller (MVC) architecture with PDF processing and Retrieval-Augmented Generation (RAG) capabilities.

## Features

- **User Authentication**
  - JWT-based authentication
  - User registration and login with email/password
  - **GitHub OAuth integration** - Login with GitHub account
  - Token refresh mechanism
  - Secure HTTP-only cookie storage

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
   # AI Configuration
   GEMINI_API_KEY=your_gemini_api_key
   
   # Django Configuration
   SECRET_KEY=your_django_secret_key
   JWT_SECRET_KEY=your_jwt_secret_key
   
   # GitHub OAuth Configuration
   GITHUB_CLIENT_ID=your_github_client_id
   GITHUB_CLIENT_SECRET=your_github_client_secret
   ```

5. **Set up GitHub OAuth Application**
   - Go to GitHub → Settings → Developer settings → OAuth Apps
   - Click "New OAuth App"
   - Fill in the details:
     ```
     Application name: Your App Name
     Homepage URL: http://localhost:8000
     Authorization callback URL: http://localhost:8000/api/auth/github/callback/
     ```
   - Copy the Client ID and Client Secret to your `.env` file

6. **Run migrations**
   ```bash
   python manage.py migrate
   ```

7. **Start the development server**
   ```bash
   python manage.py runserver
   ```

## API Documentation

The API documentation is available at:
- Swagger UI: `http://127.0.0.1:8000/swagger/`
- ReDoc: `http://127.0.0.1:8000/redoc/`

### Key Endpoints

#### Authentication
- `POST /api/auth/register/` - Register new user
- `POST /api/auth/login/` - User login with email/password
- `POST /api/auth/logout/` - User logout
- `POST /api/auth/refresh/` - Refresh JWT token

#### GitHub OAuth Authentication
- `GET /api/auth/github/` - Initiate GitHub OAuth login
- `GET /api/auth/github/callback/` - Handle GitHub OAuth callback

#### Projects
- `POST /api/projects/create/` - Create new project
- `GET /api/projects/` - List user's projects
- `PUT /api/projects/<id>/update/` - Update project
- `DELETE /api/projects/<id>/delete/` - Delete project

#### Resources (PDFs)
- `POST /api/projects/<id>/resources/add/` - Upload PDF files
- `GET /api/projects/<id>/resources/` - List project resources
- `GET /api/projects/<id>/resources/<resource_id>/` - Get resource details
- `PATCH /api/projects/<id>/resources/<resource_id>/` - Update resource metadata
- `DELETE /api/projects/<id>/resources/<resource_id>/` - Delete resource

#### Chat
- `POST /api/projects/<id>/chat/` - Send message to AI
- `GET /api/projects/<id>/messages/` - Get chat history
- `POST /api/projects/<id>/messages/<id>/reaction/` - Like/dislike message
- `POST /api/projects/<id>/messages/<id>/feedback/` - Add feedback
- `PUT /api/projects/<id>/messages/<id>/feedback/update/` - Update feedback
- `DELETE /api/projects/<id>/messages/<id>/feedback/remove/` - Remove feedback

## Testing the API

### Testing with ThunderClient/Postman

#### 1. Basic Health Check
```http
GET http://localhost:8000/api/hello/
```

#### 2. GitHub OAuth Testing

**Step 1: Get GitHub Authorization URL**
```http
GET http://localhost:8000/api/auth/github/
```

**Expected Response:**
```json
{
    "auth_url": "https://github.com/login/oauth/authorize?client_id=...",
    "state": "security_token"
}
```

**Step 2: Complete OAuth Flow (Browser)**
1. Copy the `auth_url` from the response
2. Paste in browser and authorize your GitHub app
3. Get redirected back with user logged in

**Step 3: Test Protected Endpoints**
```http
GET http://localhost:8000/api/projects/
```

#### 3. Traditional Authentication Testing

**Register New User:**
```http
POST http://localhost:8000/api/auth/register/
Content-Type: application/json

{
    "email": "test@example.com",
    "password": "password123"
}
```

**Login:**
```http
POST http://localhost:8000/api/auth/login/
Content-Type: application/json

{
    "email": "test@example.com", 
    "password": "password123"
}
```

#### 4. Project Management Testing

**Create Project:**
```http
POST http://localhost:8000/api/projects/create/
Content-Type: application/json

{
    "name": "My Test Project"
}
```

**List Projects:**
```http
GET http://localhost:8000/api/projects/
```

#### 5. PDF Upload Testing

**Upload PDF:**
```http
POST http://localhost:8000/api/projects/1/resources/add/
Content-Type: multipart/form-data

pdf_files: [select your PDF files]
```

#### 6. Chat Testing

**Send Message:**
```http
POST http://localhost:8000/api/projects/1/chat/
Content-Type: application/json

{
    "message": "What is this document about?",
    "stream": false
}
```

### Automated Testing Script

Run the included test script:
```bash
python test_github_auth.py
```

This will test:
- ✅ Server connectivity
- ✅ GitHub OAuth endpoint functionality  
- ✅ URL generation and validation
- ✅ Existing authentication endpoints
- ✅ Swagger documentation accessibility

### Testing OAuth Flow Limitations

**Note:** OAuth flows require browser interaction, so:
- ✅ **API Clients** (ThunderClient/Postman) can test individual endpoints
- ✅ **Browser** is needed for complete OAuth flow
- ✅ **Hybrid approach** works best for comprehensive testing

## GitHub OAuth Integration Details

### How It Works
1. **User clicks "Login with GitHub"** in your frontend
2. **Frontend calls** `GET /api/auth/github/` to get authorization URL
3. **User is redirected** to GitHub for authorization
4. **GitHub redirects back** to your callback URL with authorization code
5. **Your server exchanges code** for user information
6. **User is created/logged in** and JWT tokens are set
7. **User can access** all protected endpoints

### Security Features
- **State parameter** prevents CSRF attacks
- **HTTP-only cookies** prevent XSS attacks
- **Token validation** verifies all GitHub responses
- **Email matching** links GitHub accounts to existing users

### User Flow Options
Users can authenticate using either:
- **Email/Password** (traditional method)
- **GitHub Account** (OAuth method)

Both methods result in the same JWT tokens and access levels.

## PDF Processing Features

The system supports:
- Multiple PDF uploads in a single request
- Automatic text extraction using PyMuPDF
- OCR fallback for scanned documents using EasyOCR
- Language detection and support
- Text chunking and vectorization
- Hybrid retrieval using FAISS and BM25

## Chat Features

- Real-time streaming responses
- Context-aware responses using PDF content
- Message feedback system
- User feedback on AI responses
- Conversation history tracking

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

## Environment Variables Reference

```env
# Required - AI Configuration
GEMINI_API_KEY=your_gemini_api_key

# Required - Django Configuration  
SECRET_KEY=your_django_secret_key
JWT_SECRET_KEY=your_jwt_secret_key

# Required - GitHub OAuth
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret

# Optional - JWT Token Lifetimes (in minutes/days)
JWT_ACCESS_TOKEN_LIFETIME=120
JWT_REFRESH_TOKEN_LIFETIME=1

# Optional - Debug Mode
DEBUG=True
```

## Troubleshooting

### Common Issues

**1. GitHub OAuth "Invalid redirect URI"**
- Ensure callback URL in GitHub app matches: `http://localhost:8000/api/auth/github/callback/`

**2. "GitHub OAuth not configured" error**
- Check your `.env` file has `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET`

**3. JWT token issues**
- Ensure `JWT_SECRET_KEY` is set in `.env`
- Check if cookies are being set properly

**4. PDF processing errors**
- Ensure all dependencies are installed: `pip install -r requirements.txt`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 