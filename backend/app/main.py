from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.auth import router as auth_router
from app.api.plans import router as plans_router
from app.api.products import router as products_router
from app.api.planner import router as planner_router
from app.api.recommendations import router as recommendations_router
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="GenAI-powered smart budget planning and cross-platform recommendation system",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(plans_router, prefix=f"{settings.API_V1_STR}/plans", tags=["Saved Plans"])
app.include_router(products_router, prefix=f"{settings.API_V1_STR}/products", tags=["Product Catalog"])
app.include_router(planner_router, prefix=f"{settings.API_V1_STR}/planner", tags=["Budget Planner Engine"])
app.include_router(recommendations_router, prefix=f"{settings.API_V1_STR}/recommendations", tags=["AI Recommendations"])



@app.get("/", tags=["Root"])
def read_root():
    return {
        "project": settings.PROJECT_NAME,
        "version": "0.1.0",
        "status": "online",
        "docs_url": "/docs",
        "currency": {
            "code": settings.DEFAULT_CURRENCY,
            "symbol": settings.CURRENCY_SYMBOL,
        },
    }


@app.get(f"{settings.API_V1_STR}/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "app_env": settings.APP_ENV,
        "default_currency": settings.DEFAULT_CURRENCY,
        "currency_symbol": settings.CURRENCY_SYMBOL,
        "gemini_configured": bool(settings.GEMINI_API_KEY),
    }

