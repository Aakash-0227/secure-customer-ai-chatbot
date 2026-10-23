# 🔐 Secure Customer AI Chatbot

A secure, AI-powered customer support chatbot built using **FastAPI, PostgreSQL, Ollama (Llama 3.2), and Retrieval-Augmented Generation (RAG)**. The application provides customer-specific invoice assistance while protecting private customer information through authentication and data isolation.

## 🚀 Features

- **OTP Authentication:** Verify customers using one-time passwords.
- **JWT Authorization:** Protect API endpoints using JSON Web Tokens.
- **Customer-Specific Access:** Restrict invoice and knowledge retrieval to the authenticated customer.
- **Invoice Management:** Retrieve invoices and filter them by payment status.
- **AI-Powered Support:** Generate customer support responses using Ollama and Llama 3.2.
- **RAG Pipeline:** Retrieve relevant customer information using semantic search before generating answers.
- **Vector Search:** Store and search text embeddings using PostgreSQL and pgvector.
- **Database Migrations:** Manage database schema changes with Alembic.
- **Automated Testing:** Test API endpoints and customer data isolation.

## 🛠️ Technology Stack

| Component | Technology |
|---|---|
| Backend API | FastAPI |
| Programming Language | Python |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Database Migrations | Alembic |
| Authentication | OTP and JWT |
| AI Model | Ollama – Llama 3.2 |
| Embeddings | Sentence Transformers |
| Vector Search | pgvector |
| Testing | pytest |

## 🏗️ Architecture

```text
Customer
   |
   v
FastAPI Application
   |
   v
OTP Authentication / JWT
   |
   v
Customer-Scoped API
   |
   +------> PostgreSQL
   |          |
   |          +--> Customers
   |          +--> Invoices
   |          +--> Conversations
   |          +--> Messages
   |          +--> Knowledge Chunks
   |
   v
RAG Pipeline
   |
   +------> Sentence Transformer Embeddings
   |
   +------> pgvector Semantic Search
   |
   v
Ollama - Llama 3.2
   |
   v
Customer Support Response
```

## 🔄 How RAG Works

1. The customer submits a question.
2. The application identifies the authenticated customer.
3. The question is converted into an embedding.
4. PostgreSQL with pgvector retrieves relevant knowledge belonging to that customer.
5. The retrieved information is provided to the Llama 3.2 model as context.
6. The model generates a response grounded in the retrieved information.

Customer-specific filtering helps prevent one customer's knowledge records from being retrieved for another customer.

## 📁 Project Structure

```text
secure-customer-ai-chatbot/
├── alembic/
│   └── versions/
├── app/
│   ├── routes/
│   ├── services/
│   ├── tools/
│   ├── database.py
│   ├── models.py
│   ├── models_knowledge.py
│   └── main.py
├── tests/
│   ├── test_knowledge_isolation.py
│   └── test_server.py
├── .env.example
├── .gitignore
├── alembic.ini
├── requirements.txt
├── seed_data.py
├── test_invoice_indexing.py
└── test_knowledge.py
```

*Note: The structure above summarizes the main project files; additional files may exist in the repository.*

## ⚙️ Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/Aakash-0227/secure-customer-ai-chatbot.git
cd secure-customer-ai-chatbot
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Configure environment variables

Create a local `.env` file using `.env.example` as a reference. Configure your PostgreSQL connection string and a strong, randomly generated JWT secret.

Do not commit `.env` or publish database passwords, API keys, or authentication tokens.

### 5. Prepare PostgreSQL

Create a PostgreSQL database named `customer_ai_chatbot` and ensure the pgvector extension is available and enabled as required by the migrations.

Apply the database migrations:

```bash
alembic upgrade head
```

### 6. Start Ollama

Install Ollama and download the required model:

```bash
ollama pull llama3.2
```

Ensure the Ollama service is running before testing AI responses.

### 7. Seed sample data

```bash
python seed_data.py
```

Run this only after configuring the database and applying the migrations.

### 8. Start the FastAPI server

```bash
python -m uvicorn app.main:app --reload
```

Open the interactive API documentation:

- **Swagger UI:** http://127.0.0.1:8000/docs
- **Health Check:** http://127.0.0.1:8000/health

## 🔑 Main API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/auth/request-otp` | Request an OTP |
| POST | `/auth/verify-otp` | Verify OTP and obtain a JWT |
| GET | `/auth/me` | Retrieve the authenticated customer's information |
| GET | `/invoices/` | List the authenticated customer's invoices |
| GET | `/invoices/{invoice_id}` | Retrieve an authorized invoice |
| GET | `/health` | Check application health |

Conversation endpoints are available through Swagger UI. Refer to the registered API routes for their exact request formats.

Protected endpoints require the appropriate authentication credentials.

## 🧪 Testing

Run the automated test suite:

```bash
python -m pytest tests -v
```

Run the additional invoice-indexing test:

```bash
python -m pytest test_invoice_indexing.py -v
```

Run the knowledge-service test:

```bash
python -m pytest test_knowledge.py -v
```

The tests cover application health, authentication requirements, and customer-scoped knowledge retrieval. Database-dependent tests require a correctly configured PostgreSQL instance and the required embedding model.

## 🔒 Security Considerations

- Keep secrets and local environment files out of version control.
- Require authentication for protected customer endpoints.
- Apply customer ownership filters to invoice and knowledge queries.
- Use parameterized database operations through SQLAlchemy.
- Avoid logging OTPs, JWTs, passwords, or other sensitive information in production.
- Use HTTPS and secure OTP delivery for production deployments.
- Review authorization and cross-customer isolation tests before deployment.

## 🎯 Project Objective

The objective is to build a customer support assistant that combines conversational AI with secure access to customer-specific records. It demonstrates backend API development, authentication, relational database design, vector search, RAG integration, and automated testing.

## 👨‍💻 Author

**Aakash**

GitHub: [Aakash-0227](https://github.com/Aakash-0227)

Repository: [Secure Customer AI Chatbot](https://github.com/Aakash-0227/secure-customer-ai-chatbot)
