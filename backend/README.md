# PocketSmart AI - Backend Service

FastAPI-powered REST API backend for PocketSmart AI.

## Requirements
- Python 3.12+
- SQLite (local development) / PostgreSQL (production)

## Setup Instructions

1. **Virtual Environment Setup:**
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Linux/macOS:
   source venv/bin/activate
   ```

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment:**
   Ensure `../.env` is populated with your settings and `GEMINI_API_KEY` (if available).

4. **Run Server:**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

5. **API Documentation:**
   - Swagger UI: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`
