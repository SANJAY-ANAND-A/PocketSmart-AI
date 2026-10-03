# PocketSmart AI 🧠💰

> **GenAI-powered smart budget planning and cross-platform recommendation system.**

Designed as a modern, full-stack college capstone project. PocketSmart AI helps users intelligently allocate budgets and discover curated product and service recommendations across Home Interior, Event/Party Planning, and Jewelry categories using Google Gemini AI, supported by a deterministic fallback engine.

---

## 🌟 Key Features

1. **Home Interior Budget Planner**: Room-by-room budgeting, furniture allocation, style preference matching (Modern, Minimalist, Scandinavian, Bohemian, Industrial).
2. **Party / Event Budget Planner**: Event budgeting by guest count, venue type, catering, decoration, and entertainment with budget ceiling safeguards.
3. **Jewelry Budget Planner**: Occasion-specific metal and style matching with optional multimodal outfit photo analysis via Gemini Vision.
4. **Deterministic Budget Safeguard Engine**: Guarantees that total allocations never exceed the user's defined budget ($ \sum \text{allocated} \le \text{total} $).
5. **Cross-Platform Recommendation Concept**: Architecture designed to bridge recommendations across Amazon, Flipkart, IKEA, Swiggy, Zomato, and OYO using a clean provider adapter design pattern.
6. **AI Failure Fallback Engine**: If Gemini is unreachable or unconfigured, the application seamlessly switches to rule-based allocation without downtime.

---

## 🛠️ Technology Stack

- **Frontend**: React 18 / 19, TypeScript, Vite, Responsive CSS, Lucide Icons.
- **Backend**: Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2.0.
- **Database**: SQLite (local development) with clean ORM abstraction for seamless PostgreSQL migration.
- **GenAI**: Google Gemini API via the official `google-genai` SDK.
- **Currency**: Indian Rupee (`₹` INR) as default.

---

## 🚀 Quick Start (Local Development)

### 1. Backend Setup
```bash
cd backend
python -m venv venv

# Windows PowerShell:
venv\Scripts\Activate.ps1

# Install dependencies:
pip install -r requirements.txt

# Start backend server:
uvicorn app.main:app --reload --port 8000
```
API Documentation will be available at: [http://localhost:8000/docs](http://localhost:8000/docs)

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Frontend Web App will be available at: [http://localhost:5173](http://localhost:5173)

---

## 📂 Project Structure

```
sdc_project/
├── backend/                  # FastAPI Application
│   ├── app/
│   │   ├── api/              # REST API route handlers
│   │   ├── core/             # Configuration & security
│   │   ├── models/           # SQLAlchemy database models
│   │   ├── repositories/     # Data access layer
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/         # Business logic (Gemini, Budget, Recommendations)
│   │   ├── utils/            # Helper functions
│   │   └── main.py           # Application entrypoint
│   ├── tests/                # Automated pytest suite
│   ├── requirements.txt      # Python dependencies
│   └── README.md
├── frontend/                 # React + TypeScript + Vite
│   ├── src/
│   │   ├── components/       # Reusable UI components
│   │   ├── context/          # React contexts (Auth, Toast, etc.)
│   │   ├── hooks/            # Custom React hooks
│   │   ├── pages/            # View pages (Planners, Auth, Dashboard)
│   │   ├── services/         # API clients
│   │   ├── types/            # TypeScript interfaces
│   │   └── utils/            # Utilities & formatters
│   ├── package.json
│   └── README.md
├── data/
│   └── seed/                 # Sample seed datasets
├── docs/                     # Viva, Architecture, API, & AWS docs
├── .env.example              # Sample environment configuration
├── .gitignore
├── docker-compose.yml
└── README.md
```
