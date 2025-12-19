# Agentic AI Personal Loan Sales System - Backend

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
uvicorn app.main:app --reload
```

## API Documentation

After running, visit: http://localhost:8000/docs

## Project Structure

```
app/
├── main.py          # FastAPI app entry
├── config.py        # Settings
├── database.py      # DB connection
├── models/          # SQLAlchemy models
├── schemas/         # Pydantic schemas
├── api/             # API routes
├── agents/          # LangGraph agents
├── services/        # Business logic
├── core/            # Utilities
└── mock_data/       # Test data
```
