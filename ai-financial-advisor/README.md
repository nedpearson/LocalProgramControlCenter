# AI Financial Advisor

A FastAPI-based AI financial advisor service.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` and configure:
```bash
cp .env.example .env
```

3. Run the service:
```bash
uvicorn app.main:app --host 127.0.0.1 --port 5020 --reload
```

## API Endpoints

- `GET /` - Service info
- `GET /health` - Health check
- `GET /api/advice` - Get financial advice
