from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False, index=True)
    subcategory = Column(String(100), nullable=True, index=True)
    # Platforms: Amazon, Flipkart, IKEA, Swiggy, Zomato, OYO, Local
    platform = Column(String(50), nullable=False, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id", ondelete="SET NULL"), nullable=True, index=True)
    price = Column(Float, nullable=False, index=True)  # In INR (₹)
    rating = Column(Float, default=4.0, nullable=False, index=True)
    image_url = Column(String(500), nullable=True)
    product_url = Column(String(500), nullable=True)
    tags = Column(String(500), nullable=True)  # Comma-separated tags
    style = Column(String(100), nullable=True, index=True)  # Modern, Minimalist, Traditional, etc.
    availability = Column(Boolean, default=True, nullable=False)
    is_demo = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    category = relationship("Category", back_populates="products")
    vendor = relationship("Vendor", back_populates="products")
    recommendations = relationship("Recommendation", back_populates="product", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Product id={self.id} name='{self.name}' price={self.price} platform='{self.platform}'>"
