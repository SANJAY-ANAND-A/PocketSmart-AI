from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False, index=True)
    # Platforms: Amazon, Flipkart, IKEA, Swiggy, Zomato, OYO, Local
    platform = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=True)
    contact_email = Column(String(255), nullable=True)
    rating = Column(Float, default=4.5, nullable=False)
    website_url = Column(String(500), nullable=True)
    is_demo = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    products = relationship("Product", back_populates="vendor", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Vendor id={self.id} name='{self.name}' platform='{self.platform}'>"
