import logging
import os
from fastapi import FastAPI, Depends, HTTPException
from starlette.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import uvicorn

from app.api import auth, recommendation, feedback, crud
from app.core.config import settings
from app.core.security import get_password_hash
from app.db.session import engine, SessionLocal
from app.db.base import Base
from app.db.models import User, Product, Category, UserPreference, UserFeedback

# Third-party libraries for generating fake data
from faker import Faker
import random
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Product Recommendation System", 
    description="LLM-based product recommendation API",
    version="1.0.0"
)

if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Mount routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(recommendation.router, prefix="/api/products", tags=["recommendations"])
app.include_router(feedback.router, prefix="/api/feedback", tags=["feedback"])
app.include_router(crud.router, prefix="/api/crud", tags=["crud"])

@app.get("/")
async def root():
    return {"message": "Welcome to the Product Recommendation System API"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/populate-db")
async def populate_database():
    """Endpoint to populate the database with sample data"""
    try:
        create_sample_data()
        return {"message": "Database populated successfully"}
    except Exception as e:
        logger.error(f"Error populating database: {e}")
        raise HTTPException(status_code=500, detail=f"Error populating database: {str(e)}")

def create_sample_data():
    """Function to add sample data to the database"""
    db = SessionLocal()
    fake = Faker()
    
    try:
        # Check if data already exists
        existing_users = db.query(User).count()
        existing_products = db.query(Product).count()
        
        if existing_users > 0 or existing_products > 0:
            logger.info("Database already contains data. Skipping sample data creation.")
            return
        
        logger.info("Starting to populate database with sample data...")
        
        # Generate 5 users
        users = []
        for i in range(5):
            # Use bcrypt hashing via security module
            hashed_password = get_password_hash(f"password{i}")
            user = User(
                username=fake.user_name(),
                email=fake.email(),
                hashed_password=hashed_password,
                is_active=True,
                created_at=datetime.now() - timedelta(days=random.randint(1, 365))
            )
            db.add(user)
            users.append(user)
        
        # Generate 10 categories
        categories = []
        category_names = [
            "Electronics", "Clothing", "Home & Kitchen", "Books", "Sports & Outdoors",
            "Beauty & Personal Care", "Toys & Games", "Grocery", "Health & Wellness", "Automotive"
        ]
        
        for name in category_names:
            category = Category(name=name)
            db.add(category)
            categories.append(category)
        
        # Commit to get IDs
        db.commit()
        
        # Generate 120 products (12 per category)
        products = []
        product_descriptions = [
            "High-quality product that will last for years.",
            "Great value for your money with excellent features.",
            "Perfect for everyday use with outstanding durability.",
            "Premium design with attention to every detail.",
            "Innovative technology meets elegant design.",
            "Best-in-class performance at an affordable price.",
            "Lightweight and portable, perfect for travel.",
            "Energy-efficient design saves you money.",
            "Handcrafted with premium materials.",
            "Award-winning design and functionality."
        ]
        
        for category in categories:
            for i in range(12):  # 12 products per category = 120 total
                product_name = f"{fake.word().capitalize()} {fake.word().capitalize()} {category.name[:-1] if category.name.endswith('s') else category.name}"
                product = Product(
                    name=product_name,
                    description=random.choice(product_descriptions),
                    price=round(random.uniform(9.99, 999.99), 2),
                    category_id=category.id,
                    image_url=f"https://example.com/images/{fake.uuid4()}.jpg",
                    embedding=",".join([str(random.uniform(-1, 1)) for _ in range(5)])  # Simple mock embedding
                )
                db.add(product)
                products.append(product)
        
        # Commit to get product IDs
        db.commit()
        
        # Generate user preferences (each user has preferences for 3-7 categories)
        for user in users:
            user_categories = random.sample(categories, random.randint(3, 7))
            for category in user_categories:
                preference = UserPreference(
                    user_id=user.id,
                    category_id=category.id,
                    preference_score=round(random.uniform(0.1, 1.0), 2)
                )
                db.add(preference)
        
        # Generate user feedback (each user reviews 5-15 products)
        for user in users:
            user_products = random.sample(products, random.randint(5, 15))
            for product in user_products:
                feedback = UserFeedback(
                    user_id=user.id,
                    product_id=product.id,
                    rating=random.randint(1, 5),
                    comment=fake.paragraph() if random.random() > 0.3 else None,
                    created_at=datetime.now() - timedelta(days=random.randint(1, 180))
                )
                db.add(feedback)
        
        # Final commit
        db.commit()
        
        logger.info(f"Successfully added {len(users)} users, {len(categories)} categories, and {len(products)} products.")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error adding sample data: {e}")
        raise
    finally:
        db.close()

# Auto-populate database on startup if environment variable is set
if os.environ.get("AUTO_POPULATE_DB", "false").lower() == "true":
    try:
        create_sample_data()
    except Exception as e:
        logger.error(f"Failed to auto-populate database: {e}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)