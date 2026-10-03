# PocketSmart AI Architecture Specification

## Overview
PocketSmart AI is an intelligent budget allocation and cross-platform recommendation web application designed for academic demonstration and real-world extensibility.

## High-Level Architecture Flow
```
User (Browser)
    │
    ▼
React + Vite Frontend (TypeScript)
    │  REST Requests (with JWT Bearer tokens)
    ▼
FastAPI Gateway & Route Handlers
    │
    ├── 1. Validation Layer (Pydantic Models)
    ├── 2. Auth & Session Management (JWT / bcrypt)
    ├── 3. Budget Engine (Deterministic Allocation with Floor & Ceiling Constraints)
    ├── 4. Recommendation Engine (Catalog Matching & Multi-Attribute Scoring)
    └── 5. GenAI Service (Google Gemini via google-genai SDK)
            │
            ├── Structured JSON Schema Enforcement
            └── Fallback to Rule-Based Engine on API Timeout/Failure
    │
    ▼
Data Persistence Layer
    │
    └── SQLAlchemy 2.0 ORM -> SQLite (local development) / PostgreSQL (future production)
```

## Component Rationale
1. **FastAPI**: Asynchronous Python web framework providing native Pydantic validation, OpenAPI documentation (`/docs`), and high performance.
2. **Deterministic Budget Safeguards**: LLMs are creative but not reliable calculators. Pure mathematical operations are computed in Python to guarantee $ \sum \text{allocated} \le \text{total} $.
3. **Google GenAI SDK (`google-genai`)**: Modern, official SDK with native structured output parsing and multimodal support for outfit images.
4. **Local Catalog Adapter**: Demonstrates cross-platform e-commerce concepts without violating third-party terms of service or relying on fragile web scrapers.
