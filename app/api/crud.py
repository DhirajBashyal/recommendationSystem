# from fastapi import APIRouter, Depends, HTTPException, status, Query
# from sqlalchemy.orm import Session
# from typing import List, Optional
# from pydantic import BaseModel

# from ..db.models import User, Product, Category, UserPreference, UserFeedback
# from ..db.session import get_db

# router = APIRouter()

# # ---- Pydantic models for request/response ----

# class UserBase(BaseModel):
#     username: str
#     email: str
#     is_active: bool = True

# class UserCreate(UserBase):
#     password: str

# class UserResponse(UserBase):
#     id: int
#     created_at: Optional[str] = None

#     class Config:
#         orm_mode = True

# class CategoryBase(BaseModel):
#     name: str

# class CategoryResponse(CategoryBase):
#     id: int
    
#     class Config:
#         orm_mode = True

# class ProductBase(BaseModel):
#     name: str
#     description: str
#     price: float
#     category_id: int
#     image_url: Optional[str] = None
#     embedding: Optional[str] = None

# class ProductResponse(ProductBase):
#     id: int
    
#     class Config:
#         orm_mode = True

# # ---- User CRUD Operations ----

# @router.post("/users/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
# def create_user_endpoint(user: UserCreate, db: Session = Depends(get_db)):
#     db_user = db.query(User).filter(User.username == user.username).first()
#     if db_user:
#         raise HTTPException(status_code=400, detail="Username already registered")
    
#     # Hash password in a real app
#     import hashlib
#     hashed_password = hashlib.sha256(user.password.encode()).hexdigest()
    
#     db_user = User(
#         username=user.username,
#         email=user.email,
#         hashed_password=hashed_password,
#         is_active=user.is_active
#     )
#     db.add(db_user)
#     db.commit()
#     db.refresh(db_user)
#     return db_user

# @router.get("/users/", response_model=List[UserResponse])
# def get_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
#     users = db.query(User).offset(skip).limit(limit).all()
#     return users

# @router.get("/users/{user_id}", response_model=UserResponse)
# def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
#     db_user = db.query(User).filter(User.id == user_id).first()
#     if db_user is None:
#         raise HTTPException(status_code=404, detail="User not found")
#     return db_user

# @router.get("/users/by-username/{username}", response_model=UserResponse)
# def get_user_by_username(username: str, db: Session = Depends(get_db)):
#     db_user = db.query(User).filter(User.username == username).first()
#     if db_user is None:
#         raise HTTPException(status_code=404, detail="User not found")
#     return db_user

# @router.put("/users/{user_id}", response_model=UserResponse)
# def update_user(user_id: int, user: UserBase, db: Session = Depends(get_db)):
#     db_user = db.query(User).filter(User.id == user_id).first()
#     if db_user is None:
#         raise HTTPException(status_code=404, detail="User not found")
    
#     # Update user attributes
#     for var, value in vars(user).items():
#         if value is not None:
#             setattr(db_user, var, value)
    
#     db.commit()
#     db.refresh(db_user)
#     return db_user

# @router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
# def delete_user(user_id: int, db: Session = Depends(get_db)):
#     db_user = db.query(User).filter(User.id == user_id).first()
#     if db_user is None:
#         raise HTTPException(status_code=404, detail="User not found")
    
#     db.delete(db_user)
#     db.commit()
#     return None

# # ---- Category CRUD Operations ----

# @router.post("/categories/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
# def create_category(category: CategoryBase, db: Session = Depends(get_db)):
#     db_category = db.query(Category).filter(Category.name == category.name).first()
#     if db_category:
#         raise HTTPException(status_code=400, detail="Category already exists")
    
#     db_category = Category(**category.dict())
#     db.add(db_category)
#     db.commit()
#     db.refresh(db_category)
#     return db_category

# @router.get("/categories/", response_model=List[CategoryResponse])
# def get_categories(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
#     categories = db.query(Category).offset(skip).limit(limit).all()
#     return categories

# @router.get("/categories/{category_id}", response_model=CategoryResponse)
# def get_category(category_id: int, db: Session = Depends(get_db)):
#     db_category = db.query(Category).filter(Category.id == category_id).first()
#     if db_category is None:
#         raise HTTPException(status_code=404, detail="Category not found")
#     return db_category

# # ---- Product CRUD Operations ----

# @router.post("/products/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
# def create_product(product: ProductBase, db: Session = Depends(get_db)):
#     # Check if category exists
#     db_category = db.query(Category).filter(Category.id == product.category_id).first()
#     if db_category is None:
#         raise HTTPException(status_code=404, detail="Category not found")
    
#     db_product = Product(**product.dict())
#     db.add(db_product)
#     db.commit()
#     db.refresh(db_product)
#     return db_product

# @router.get("/products/", response_model=List[ProductResponse])
# def get_products(
#     skip: int = 0, 
#     limit: int = 20, 
#     category_id: Optional[int] = None,
#     min_price: Optional[float] = None,
#     max_price: Optional[float] = None,
#     db: Session = Depends(get_db)
# ):
#     query = db.query(Product)
    
#     # Apply filters if provided
#     if category_id:
#         query = query.filter(Product.category_id == category_id)
#     if min_price:
#         query = query.filter(Product.price >= min_price)
#     if max_price:
#         query = query.filter(Product.price <= max_price)
    
#     products = query.offset(skip).limit(limit).all()
#     return products

# @router.get("/products/{product_id}", response_model=ProductResponse)
# def get_product(product_id: int, db: Session = Depends(get_db)):
#     db_product = db.query(Product).filter(Product.id == product_id).first()
#     if db_product is None:
#         raise HTTPException(status_code=404, detail="Product not found")
#     return db_product

# @router.put("/products/{product_id}", response_model=ProductResponse)
# def update_product(product_id: int, product: ProductBase, db: Session = Depends(get_db)):
#     db_product = db.query(Product).filter(Product.id == product_id).first()
#     if db_product is None:
#         raise HTTPException(status_code=404, detail="Product not found")
    
#     # Check if the category exists (if updating category)
#     if product.category_id != db_product.category_id:
#         db_category = db.query(Category).filter(Category.id == product.category_id).first()
#         if db_category is None:
#             raise HTTPException(status_code=404, detail="Category not found")
    
#     # Update product attributes
#     for var, value in vars(product).items():
#         if value is not None:
#             setattr(db_product, var, value)
    
#     db.commit()
#     db.refresh(db_product)
#     return db_product

# @router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
# def delete_product(product_id: int, db: Session = Depends(get_db)):
#     db_product = db.query(Product).filter(Product.id == product_id).first()
#     if db_product is None:
#         raise HTTPException(status_code=404, detail="Product not found")
    
#     db.delete(db_product)
#     db.commit()
#     return None

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from ..db.models import User, Product, Category, UserPreference, UserFeedback
from ..db.session import get_db

router = APIRouter()

# ---- Pydantic models for request/response ----

class UserBase(BaseModel):
    username: str
    email: str
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    created_at: Optional[str] = None

    class Config:
        orm_mode = True
        # Add this configuration to ensure None values are properly handled
        from_attributes = True

class CategoryBase(BaseModel):
    name: str

class CategoryResponse(CategoryBase):
    id: int
    
    class Config:
        orm_mode = True
        from_attributes = True

class ProductBase(BaseModel):
    name: str
    description: str
    price: float
    category_id: int
    image_url: Optional[str] = None
    embedding: Optional[str] = None

class ProductResponse(ProductBase):
    id: int
    
    class Config:
        orm_mode = True
        from_attributes = True

# ---- User CRUD Operations ----

# @router.post("/users/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
# def create_user_endpoint(user: UserCreate, db: Session = Depends(get_db)):
#     db_user = db.query(User).filter(User.username == user.username).first()
#     if db_user:
#         raise HTTPException(status_code=400, detail="Username already registered")
    
#     # Hash password in a real app
#     import hashlib
#     hashed_password = hashlib.sha256(user.password.encode()).hexdigest()
    
#     db_user = User(
#         username=user.username,
#         email=user.email,
#         hashed_password=hashed_password,
#         is_active=user.is_active if user.is_active is not None else True
#     )
#     db.add(db_user)
#     db.commit()
#     db.refresh(db_user)
#     return db_user

# @router.get("/users/", response_model=List[UserResponse])
# def get_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
#     users = db.query(User).offset(skip).limit(limit).all()
#     return users

# @router.get("/users/{user_id}", response_model=UserResponse)
# def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
#     db_user = db.query(User).filter(User.id == user_id).first()
#     if db_user is None:
#         raise HTTPException(status_code=404, detail="User not found")
#     # Ensure is_active is a boolean
#     if db_user.is_active is None:
#         db_user.is_active = True
#         db.commit()
#     return db_user

# @router.get("/users/by-username/{username}", response_model=UserResponse)
# def get_user_by_username(username: str, db: Session = Depends(get_db)):
#     db_user = db.query(User).filter(User.username == username).first()
#     if db_user is None:
#         raise HTTPException(status_code=404, detail="User not found")
#     # Ensure is_active is a boolean
#     if db_user.is_active is None:
#         db_user.is_active = True
#         db.commit()
#     return db_user

# @router.put("/users/{user_id}", response_model=UserResponse)
# def update_user(user_id: int, user: UserBase, db: Session = Depends(get_db)):
#     db_user = db.query(User).filter(User.id == user_id).first()
#     if db_user is None:
#         raise HTTPException(status_code=404, detail="User not found")
    
#     # Update user attributes
#     for var, value in vars(user).items():
#         if var == 'is_active' and value is None:
#             value = True  # Provide a default value if None
#         setattr(db_user, var, value)
    
#     db.commit()
#     db.refresh(db_user)
#     return db_user

# @router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
# def delete_user(user_id: int, db: Session = Depends(get_db)):
#     db_user = db.query(User).filter(User.id == user_id).first()
#     if db_user is None:
#         raise HTTPException(status_code=404, detail="User not found")
    
#     db.delete(db_user)
#     db.commit()
#     return None

# ---- Category CRUD Operations ----

@router.post("/categories/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(category: CategoryBase, db: Session = Depends(get_db)):
    db_category = db.query(Category).filter(Category.name == category.name).first()
    if db_category:
        raise HTTPException(status_code=400, detail="Category already exists")
    
    db_category = Category(**category.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

@router.get("/categories/", response_model=List[CategoryResponse])
def get_categories(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    categories = db.query(Category).offset(skip).limit(limit).all()
    return categories

@router.get("/categories/{category_id}", response_model=CategoryResponse)
def get_category(category_id: int, db: Session = Depends(get_db)):
    db_category = db.query(Category).filter(Category.id == category_id).first()
    if db_category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return db_category

# ---- Product CRUD Operations ----

@router.post("/products/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(product: ProductBase, db: Session = Depends(get_db)):
    # Check if category exists
    db_category = db.query(Category).filter(Category.id == product.category_id).first()
    if db_category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    
    db_product = Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@router.get("/products/", response_model=List[ProductResponse])
def get_products(
    skip: int = 0, 
    limit: int = 20, 
    category_id: Optional[int] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Product)
    
    # Apply filters if provided
    if category_id:
        query = query.filter(Product.category_id == category_id)
    if min_price:
        query = query.filter(Product.price >= min_price)
    if max_price:
        query = query.filter(Product.price <= max_price)
    
    products = query.offset(skip).limit(limit).all()
    return products

@router.get("/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return db_product

@router.put("/products/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, product: ProductBase, db: Session = Depends(get_db)):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Check if the category exists (if updating category)
    if product.category_id != db_product.category_id:
        db_category = db.query(Category).filter(Category.id == product.category_id).first()
        if db_category is None:
            raise HTTPException(status_code=404, detail="Category not found")
    
    # Update product attributes
    for var, value in vars(product).items():
        setattr(db_product, var, value)
    
    db.commit()
    db.refresh(db_product)
    return db_product

@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    
    db.delete(db_product)
    db.commit()
    return None