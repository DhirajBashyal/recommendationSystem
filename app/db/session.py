# from sqlalchemy import create_engine
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker
# from ..core.config import settings

# engine = create_engine(
#     settings.DATABASE_URL,
#     pool_pre_ping=True,  
#     pool_size=10,  
#     max_overflow=20, 
#     pool_recycle=3600, 
# )

# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

# app/db/session.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from ..core.config import settings

engine = create_engine(
    settings.DATABASE_URI, 
    pool_pre_ping=True,  
    pool_size=10,  
    max_overflow=20, 
    pool_recycle=3600, 
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()  

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()