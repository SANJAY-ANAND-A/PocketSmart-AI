from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    # module_type: 'home', 'party', 'jewelry'
    module_type = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    products = relationship("Product", back_populates="category", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Category id={self.id} name='{self.name}' module_type='{self.module_type}'>"
