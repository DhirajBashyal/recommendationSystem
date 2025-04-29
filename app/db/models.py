from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(200))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    
    preferences = relationship("UserPreference", back_populates="user")
    feedback = relationship("UserFeedback", back_populates="user")
    
class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), index=True)
    description = Column(Text)
    price = Column(Float)
    category_id = Column(Integer, ForeignKey("categories.id"))
    image_url = Column(String(500))
    embedding = Column(Text, nullable=True)  
    
    category = relationship("Category", back_populates="products")
    feedback = relationship("UserFeedback", back_populates="product")
    
class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True)
    
    products = relationship("Product", back_populates="category")
    
class UserPreference(Base):
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    category_id = Column(Integer, ForeignKey("categories.id"))
    preference_score = Column(Float, default=0.0)
    
    user = relationship("User", back_populates="preferences")
    category = relationship("Category")
    
class UserFeedback(Base):
    __tablename__ = "user_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    rating = Column(Integer)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    
    user = relationship("User", back_populates="feedback")
    product = relationship("Product", back_populates="feedback")