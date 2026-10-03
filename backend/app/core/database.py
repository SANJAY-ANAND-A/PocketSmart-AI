from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

# SQLite requires 'check_same_thread': False for FastAPI threaded requests
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False,  # Set to True for verbose SQL query logging if debugging
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency that provides an independent database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all database tables defined in the SQLAlchemy models metadata."""
    # Import all models to ensure they are registered with Base.metadata
    from app.models import (  # noqa: F401
        User,
        Vendor,
        Category,
        Product,
        BudgetPlan,
        BudgetItem,
        Recommendation,
    )
    Base.metadata.create_all(bind=engine)
