# DRF MVC Project with PDF RAG Integration

A Django REST Framework project that implements a Model-View-Controller (MVC) architecture with PDF processing and Retrieval-Augmented Generation (RAG) capabilities.

## Features

- **User Authentication**
  - JWT-based authentication
  - User registration and login
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

### Key Endpoints

#### Authentication
- `POST /api/auth/register/` - Register new user
- `POST /api/auth/login/` - User login
- `POST /api/auth/logout/` - User logout
- `POST /api/auth/refresh/` - Refresh JWT token

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
- `POST /api/projects/<id>/messages/<id>/like/` - Like message
- `POST /api/projects/<id>/messages/<id>/dislike/` - Dislike message
- `DELETE /api/projects/<id>/messages/<id>/reaction/` - Remove reaction
- `POST /api/projects/<id>/messages/<id>/feedback/` - Add feedback
- `PUT /api/projects/<id>/messages/<id>/feedback/update/` - Update feedback
- `DELETE /api/projects/<id>/messages/<id>/feedback/remove/` - Remove feedback

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

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 