# Agentic AI Personal Loan Sales System

An intelligent, production-ready loan origination system powered by multi-agent AI using LangGraph orchestration.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green)
![React](https://img.shields.io/badge/React-18.3+-61DAFB)
![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-purple)

## 🎯 Overview

This system automates the personal loan sales process through conversational AI:

1. **Sales Agent** → Collects loan requirements through natural conversation
2. **Verification Agent** → Validates KYC against CRM database  
3. **Underwriting Agent** → Evaluates eligibility using rules + ML
4. **Sanction Agent** → Generates professional PDF sanction letters

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- Docker & Docker Compose
- PostgreSQL 16+
- Redis 7+

### Local Development

```bash
# Clone repository
git clone <repository-url>
cd agentic-seller

# Start with Docker Compose
docker-compose up -d

# Or run manually:

# Backend
cd backend
pip install -r requirements.txt
cp .env.example .env  # Edit with your API keys
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

### Access
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      FRONTEND (React)                        │
│   Chat UI │ Admin Dashboard │ Status Tracker │ Doc Upload   │
└─────────────────────────────────┬───────────────────────────┘
                                  │
┌─────────────────────────────────▼───────────────────────────┐
│                    FASTAPI BACKEND                           │
│   JWT Auth │ Rate Limit │ Input Validation │ CORS            │
└─────────────────────────────────┬───────────────────────────┘
                                  │
┌─────────────────────────────────▼───────────────────────────┐
│                LANGGRAPH AGENT ORCHESTRATOR                  │
│  ┌─────────┐ ┌──────────┐ ┌────────────┐ ┌────────────┐    │
│  │  SALES  │ │   KYC    │ │UNDERWRITING│ │  SANCTION  │    │
│  │  AGENT  │ │  AGENT   │ │   AGENT    │ │   AGENT    │    │
│  └─────────┘ └──────────┘ └────────────┘ └────────────┘    │
└─────────────────────────────────┬───────────────────────────┘
                                  │
┌─────────────────────────────────▼───────────────────────────┐
│                      DATA LAYER                              │
│   PostgreSQL │ Redis │ S3/MinIO │ ChromaDB (Optional)       │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
agentic-seller/
├── backend/
│   ├── app/
│   │   ├── agents/          # LangGraph agent implementations
│   │   ├── api/v1/          # FastAPI routes
│   │   ├── core/            # Security, logging utilities
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Business logic
│   │   └── mock_data/       # Test data
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── services/
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
└── .github/workflows/ci-cd.yml
```

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/chat` | POST | Main chat (Master Agent) |
| `/api/v1/kyc/verify` | POST | KYC verification |
| `/api/v1/credit/score/{id}` | GET | Credit bureau lookup |
| `/api/v1/underwrite/decide` | POST | Underwriting decision |
| `/api/v1/sanction/generate` | POST | Generate PDF |
| `/api/v1/applications` | GET | List applications |

## 🔐 Environment Variables

```env
# LLM (required)
ANTHROPIC_API_KEY=your-claude-api-key
LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-4-20250514

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/db
REDIS_URL=redis://localhost:6379/0

# Security
JWT_SECRET_KEY=your-secret-key
SECRET_KEY=your-app-secret
```

## 📊 Underwriting Rules

1. **Credit Score** ≥ 700 (hard requirement)
2. **Pre-approved limit**: Auto-approve if within limit
3. **EMI ratio**: Monthly EMI ≤ 50% of salary
4. **Max loan**: ≤ 2x pre-approved limit (with salary verification)

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest tests/ -v --cov=app

# Load testing
locust -f tests/locustfile.py --host=http://localhost:8000
```

## 📦 Deployment

### Docker Compose (Recommended)
```bash
docker-compose -f docker-compose.yml up -d
```

### AWS ECS
See `.github/workflows/ci-cd.yml` for deployment configuration.

## 📄 License

MIT License - see LICENSE file for details.

