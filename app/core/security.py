from datetime import datetime, timedelta
from typing import Optional
import hashlib

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from ..db.session import get_db
from ..db.models import User
from .config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify that the provided plain password matches the hashed password.
    Supports both bcrypt hashes and legacy SHA-256 hashes.
    """
    # First try bcrypt verification
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except:
        # If bcrypt verification fails, try SHA-256 verification
        sha256_hash = hashlib.sha256(plain_password.encode()).hexdigest()
        return sha256_hash == hashed_password

def get_password_hash(password: str) -> str:
    """
    Hash the plain password using bcrypt.
    """
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

# async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
#     """
#     Retrieve the current user based on the JWT token.
#     """
#     print("i am here")
#     credentials_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Could not validate credentials",
#         headers={"WWW-Authenticate": "Bearer"},
#     )
    
#     try:
#         # Decode the JWT token
#         payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
#         # Extract the username from the subject claim
#         username: str = payload.get("sub")
#         if username is None:
#             raise credentials_exception
            
#         # Find the user in the database
#         user = db.query(User).filter(User.username == username).first()
#         if user is None or not user.is_active:
#             raise credentials_exception
            
#         return user
        
#     except JWTError as e:
#         # Log the error for debugging (optional)
#         print(f"JWT Error: {str(e)}")
#         raise credentials_exception
    
def migrate_password_if_needed(db: Session, user: User, plain_password: str) -> None:
    """
    Check if the password is still using the old SHA-256 hash, 
    and if so, upgrade it to bcrypt.
    """
    sha256_hash = hashlib.sha256(plain_password.encode()).hexdigest()
    if user.hashed_password == sha256_hash:
        # This is an old SHA-256 hash, upgrade to bcrypt
        user.hashed_password = get_password_hash(plain_password)
        db.commit()
