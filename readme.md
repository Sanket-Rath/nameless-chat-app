# Nameless Chat App

An AI-powered conversational web application built using **FastAPI**, **React**, **Google Gemini 2.5 Flash**, and **PostgreSQL**. The application allows users to create multiple conversations, interact with an AI assistant, and upload documents for context-aware question answering using a Retrieval-Augmented Generation (RAG) pipeline.

---

# Features

* User Registration and Login
* JWT-based Authentication
* Multiple Conversation Management
* Persistent Chat History
* AI-powered Conversations using Gemini 2.5 Flash
* Document Upload Support
* Retrieval-Augmented Generation (RAG)
* Semantic Search using FAISS Vector Database
* Responsive React Frontend
* RESTful Backend APIs with FastAPI

---

# Technology Stack

## Frontend

* React
* Vite
* JavaScript
* CSS

## Backend

* FastAPI
* Python
* Uvicorn

## Database

* PostgreSQL (Render PostgreSQL)

## Authentication

* JWT (JSON Web Tokens)
* bcrypt

## AI Stack

* Gemini 2.5 Flash
* Gemini Embedding Model (`gemini-embedding-001`)

## RAG Components

* FAISS Vector Store
* Document Chunking
* Semantic Retrieval
* Gemini-based Response Generation

## Deployment

* Frontend: Vercel
* Backend: Render
* Database: Render PostgreSQL

---

# Project Structure

```text
nameless-chat-app/

├── backend/
│   ├── ai_service.py
│   ├── auth.py
│   ├── config.py
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   ├── rag_service.py
│   ├── schemas.py
│   ├── requirements.txt
│   ├── uploads/
│   └── vector_store/
│
├── frontend/
│   ├── public/
│   ├── src/
│   ├── package.json
│   └── vite.config.js
│
└── README.md
```

---

# Development Phases

## Phase 1 — Backend Development

* FastAPI project setup
* REST API creation
* Route management
* Gemini AI integration
* Backend architecture

---

## Phase 2 — Database & Authentication

* PostgreSQL integration
* Database schema design
* User management
* JWT authentication
* Password hashing using bcrypt
* Conversation persistence

---

## Phase 3 — Frontend Development

* React + Vite setup
* Authentication pages
* Chat interface
* Conversation sidebar
* API integration
* Responsive UI

---

## Phase 4 — RAG Integration

* Document upload
* Text extraction
* Document chunking
* Gemini embeddings generation
* FAISS vector indexing
* Semantic retrieval
* Context-aware AI responses

---

## Phase 5 — Deployment & Documentation

* Backend deployment on Render
* Frontend deployment on Vercel
* PostgreSQL deployment on Render
* Environment configuration
* Project documentation

---

# Deployment Architecture

```text
                    +--------------------+
                    |     User Browser   |
                    +---------+----------+
                              |
                              |
                              v
                    +--------------------+
                    |  Frontend (Vercel) |
                    |   React + Vite     |
                    +---------+----------+
                              |
                              |
                              v
                    +--------------------+
                    | Backend (Render)   |
                    |      FastAPI       |
                    +----+---------+-----+
                         |         |
                         |         |
              +----------+         +----------------+
              |                                   |
              v                                   v
+---------------------------+        +----------------------------+
| Render PostgreSQL         |        | Gemini 2.5 Flash API       |
| Users                     |        | Response Generation        |
| Conversations             |        |                            |
| Messages                  |        +----------------------------+
| Documents                 |
+-------------+-------------+
              |
              |
              v
+----------------------------+
| FAISS Vector Store         |
| Document Embeddings        |
| Semantic Retrieval         |
+----------------------------+
```

---

# RAG Pipeline

```text
User Uploads Document
            │
            ▼
Text Extraction
            │
            ▼
Chunking
            │
            ▼
Gemini Embeddings
(gemini-embedding-001)
            │
            ▼
FAISS Vector Store
            │
            ▼
User Query
            │
            ▼
Similarity Search
            │
            ▼
Relevant Chunks Retrieved
            │
            ▼
Gemini 2.5 Flash
            │
            ▼
AI Response
```

---

# Environment Variables

Create a `.env` file inside the `backend` directory.

```env
DATABASE_URL=

SECRET_KEY=

GEMINI_API_KEY=
```

---

# Running the Project Locally

## Step 1

Clone the repository.

```bash
git clone <repository-url>

cd nameless-chat-app
```

---

## Step 2

Create a `.env` file inside the `backend` directory and add:

```env
DATABASE_URL=

SECRET_KEY=

GEMINI_API_KEY=
```

---

## Step 3

Install backend dependencies.

```bash
cd backend

pip install -r requirements.txt
```

---

## Step 4

Return to the project root and start the backend server.

```bash
cd ..

uvicorn backend.main:app --reload
```

---

## Step 5

Open a new terminal.

```bash
cd frontend
```

---

## Step 6

Install frontend dependencies.

```bash
npm install
```

---

## Step 7

Start the frontend development server.

```bash
npm run dev
```

---

The application will now be available locally through the Vite development server, while the backend APIs will be served by FastAPI.

---

# Future Enhancements

* Source Citations for RAG Responses
* Streaming AI Responses
* Conversation Rename
* Conversation Search
* Token Usage Analytics
* Multiple Document Chat
* OCR Support for Scanned PDFs
* Conversation Summarization
* Dark Mode
* Multi-language Support

---

# License

This project is licensed under the **MIT License**.

Feel free to use, modify, and distribute this project in accordance with the terms of the MIT License.
