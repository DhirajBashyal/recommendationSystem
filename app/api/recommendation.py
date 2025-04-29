from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import asyncio

from app.db.session import get_db
from app.db.models import Product
from app.api.auth import get_current_user, oauth2_scheme
from app.cache.redis import MemcachedClient
from app.llm.client import LLMClient

router = APIRouter()
redis_client = MemcachedClient()
llm_client = LLMClient()
logger = logging.getLogger(__name__)

# Function to extract token
async def extract_token(authorization: Optional[str], token_param: Optional[str]) -> str:
    if authorization and authorization.startswith("Bearer "):
        return authorization.replace("Bearer ", "")
    elif token_param:
        return token_param
    else:
        logger.error("No authentication token provided")
        raise HTTPException(status_code=401, detail="Authentication required")

class ProductRecommender:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.product_vectors = None
        self.products = None
    
    def fit(self, products):
        """Create vector representations of products"""
        self.products = products
        
        texts = [f"{p['name']} {p['description']} {p['category']}" for p in products]

        try:
            self.product_vectors = self.vectorizer.fit_transform(texts)
            logger.info(f"Created vectors for {len(products)} products")
        except Exception as e:
            logger.error(f"Error creating product vectors: {str(e)}")
            raise
    
    def recommend_similar_products(self, query, top_k=5):
        if not self.products or self.product_vectors is None:
            logger.error("Recommender not fitted with product data")
            raise ValueError("Recommender not fitted with product data")

        query_vector = self.vectorizer.transform([query])
    
        similarities = cosine_similarity(query_vector, self.product_vectors).flatten()
        
        top_indices = similarities.argsort()[-top_k:][::-1]

        recommendations = []
        for idx in top_indices:
            product = self.products[idx]
            match_score = int(similarities[idx] * 100)  # Convert to 0-100 scale
            
            price_formatted = f"{product['price']:.2f} USD"
            
            recommendation = {
                "id": product["id"],
                "name": product["name"],
                "description": product.get("description", ""),
                "price": price_formatted,
                "category": product["category"],
                "brand": product.get("brand", "Unknown"),
                "reviews_count": product.get("reviews_count", 0),
                "match_score": match_score,
                "reason": self._generate_reason(product, query, match_score)
            }
            recommendations.append(recommendation)
        
        return recommendations
    
    def _generate_reason(self, product, query, match_score):
        """Generate human-readable reason for recommendation"""
        reason = f"This product matches your search for '{query}'."

        if product.get("brand"):
            reason += f" Brand: {product['brand']}."

        if product.get("reviews_count", 0) > 0:
            reason += f" Has {product['reviews_count']} reviews."
        

        reason += f" Match Score: {match_score}/100"
        
        return reason

recommender = ProductRecommender()

# Fixed: Return a list instead of a dictionary to match response_model
# @router.get("/recommendations/similar/", response_model=List[Dict[str, Any]])
# async def get_similar_products(
#     query: str,
#     limit: int = Query(5, gt=0, le=20),
#     authorization: Optional[str] = Header(None),
#     token_param: Optional[str] = Depends(oauth2_scheme),
#     db: Session = Depends(get_db)
# ):
#     """Endpoint to get products similar to a search query"""
#     token = await extract_token(authorization, token_param)
#     current_user = await get_current_user(token=token, db=db)
    
#     # Check cache first
#     cache_key = f"similar:{query}:{limit}"
#     cached_data = await redis_client.get(cache_key)
#     if cached_data:
#         logger.info(f"Returning cached similar products for query '{query}'")
#         return cached_data
    
#     try:
#         # Get products from database
#         products = db.query(Product).all()
        
#         if not products:
#             # Return empty list instead of dictionary with message
#             return []
        
#         # Prepare product data
#         product_data = [
#             {
#                 "id": p.id,
#                 "name": p.name,
#                 "description": p.description,
#                 "price": p.price,
#                 "category": p.category.name,
#                 "image_url": p.image_url,
#                 "brand": getattr(p, 'brand', 'Unknown'),
#                 "reviews_count": getattr(p, 'reviews_count', 0)
#             }
#             for p in products
#         ]
        
#         # Fit recommender with all products
#         recommender.fit(product_data)
        
#         # Get recommendations - directly return the list
#         recommendations = recommender.recommend_similar_products(
#             query=query,
#             top_k=limit
#         )
        
#         logger.info(f"Found {len(recommendations)} similar products for query '{query}'")
        
#     except Exception as e:
#         logger.error(f"Error finding similar products: {str(e)}")
#         raise HTTPException(status_code=500, detail="Error finding similar products")
    
#     # Cache results
#     try:
#         await redis_client.set(cache_key, recommendations, expire=600)  # 10 minutes
#     except Exception as e:
#         logger.warning(f"Failed to cache similar products: {str(e)}")
    
#     return recommendations

# Fixed: Return a list instead of a dictionary
@router.get("/search/", response_model=List[Dict[str, Any]])
async def search_products(
    query: str,
    limit: int = Query(20, gt=0, le=100),
    authorization: Optional[str] = Header(None),
    token_param: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Search for products and provide similar products recommendations"""
    token = await extract_token(authorization, token_param)
    current_user = await get_current_user(token=token, db=db)

    cache_key = f"search:{query}:{limit}"
    cached_data = await redis_client.get(cache_key)
    if cached_data:
        logger.info(f"Returning cached search results for query '{query}'")
        return cached_data

    try:
        exact_matches = db.query(Product).filter(
            Product.name.ilike(f"%{query}%") |
            Product.description.ilike(f"%{query}%")
        ).limit(limit).all()
        
        all_products = db.query(Product).all()
        
        product_data = [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "price": p.price,
                "category": p.category.name,
                "image_url": p.image_url,
                "brand": getattr(p, 'brand', 'Unknown'),
                "reviews_count": getattr(p, 'reviews_count', 0)
            }
            for p in all_products
        ]
        
        if product_data:
            recommender.fit(product_data)
            results = recommender.recommend_similar_products(
                query=query,
                top_k=limit
            )
        else:
            results = []
            
    except Exception as e:
        logger.error(f"Error searching products: {str(e)}")
        raise HTTPException(status_code=500, detail="Error searching products")

    try:
        await redis_client.set(cache_key, results, expire=600)  # 10 min
    except Exception as e:
        logger.warning(f"Failed to cache search results: {str(e)}")
    
    return results
@router.get("/recommendations/", response_model=List[Dict[str, Any]])
async def get_hybrid_recommendations(
    query: str = Query(..., description="Search query/title to find recommendations for"),
    limit: int = Query(10, gt=0, le=100),
    tfidf_weight: float = Query(0.5, ge=0.0, le=1.0, description="Weight for TF-IDF recommendations"),
    min_score: int = Query(20, ge=0, le=100, description="Minimum match score threshold"),
    authorization: Optional[str] = Header(None),
    token_param: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    token = await extract_token(authorization, token_param)
    current_user = await get_current_user(token=token, db=db)

    cache_key = f"hybrid_recommendations:query:{query}:{tfidf_weight}:{limit}:{min_score}"
    cached_data = await redis_client.get(cache_key)
    if cached_data:
        logger.info(f"Returning cached hybrid recommendations for query '{query}'")
        return cached_data

    try:
        logger.info(f"Getting recommendations for query: '{query}' with min score: {min_score}")

        all_products = db.query(Product).all()

        product_data = [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "price": p.price,
                "category": p.category.name,
                "image_url": p.image_url,
                "brand": getattr(p, 'brand', 'Unknown'),
                "reviews_count": getattr(p, 'reviews_count', 0)
            }
            for p in all_products
        ]

        recommender.fit(product_data)
        tfidf_recommendations = recommender.recommend_similar_products(
            query=query,  
            top_k=limit*2 
        )
        
        filtered_tfidf_recs = [rec for rec in tfidf_recommendations if rec.get('match_score', 0) > min_score]
        
        query_prompt = f"Find products similar to '{query}'. The customer is looking for products like: {query}"
        
        llm_recommendations = await llm_client.generate_recommendations(
            user_preferences=query_prompt,
            product_descriptions=product_data,
            top_k=limit*2  
        )
        filtered_llm_recs = []
        for prod in llm_recommendations:
            score = prod.get('match_score', 0)
            
            if isinstance(score, (int, float)) and score <= min_score:
                continue
                
            if isinstance(prod.get('price'), (int, float)):
                prod['price'] = f"{prod['price']:.2f} USD"
            
            if isinstance(score, (int, float)):
                if score >= 80:
                    prod['match_score'] = 'Excellent'
                elif score >= 60:
                    prod['match_score'] = 'Good'
                elif score >= 40:
                    prod['match_score'] = 'Fair'
                else:
                    prod['match_score'] = 'Low'
            
            if 'reason' not in prod:
                prod['reason'] = f"Recommended based on your search for '{query}'. Brand: {prod.get('brand', 'Unknown')}."
                
            filtered_llm_recs.append(prod)
    
        included_ids = set()
        hybrid_recommendations = []
        
        tfidf_count = int(limit * tfidf_weight)
        llm_count = limit - tfidf_count

        for rec in filtered_tfidf_recs:
            if len(hybrid_recommendations) >= tfidf_count:
                break
                
            if rec['id'] not in included_ids:
                included_ids.add(rec['id'])
                score = rec.get('match_score', 0)
                if isinstance(score, int) or isinstance(score, float):
                    if score >= 80:
                        rec['match_score'] = 'Excellent'
                    elif score >= 60:
                        rec['match_score'] = 'Good'
                    elif score >= 40:
                        rec['match_score'] = 'Fair'
                    else:
                        rec['match_score'] = 'Low'
                rec['source'] = 'Content-Based'
                hybrid_recommendations.append(rec)
        
        for rec in filtered_llm_recs:
            if len(hybrid_recommendations) >= limit:
                break
                
            if rec['id'] not in included_ids:
                included_ids.add(rec['id'])
                rec['source'] = 'Title-Based'
                hybrid_recommendations.append(rec)
        
        remaining_tfidf = [r for r in filtered_tfidf_recs if r['id'] not in included_ids]
        remaining_llm = [r for r in filtered_llm_recs if r['id'] not in included_ids]
        remaining_recs = []
        for i in range(max(len(remaining_tfidf), len(remaining_llm))):
            if i < len(remaining_tfidf):
                remaining_recs.append(remaining_tfidf[i])
            if i < len(remaining_llm):
                remaining_recs.append(remaining_llm[i])
        
        for rec in remaining_recs:
            if len(hybrid_recommendations) >= limit:
                break
                
            if rec['id'] not in included_ids:
                included_ids.add(rec['id'])
                score = rec.get('match_score', 0)
                if isinstance(score, int) or isinstance(score, float):
                    if score >= 80:
                        rec['match_score'] = 'Excellent'
                    elif score >= 60:
                        rec['match_score'] = 'Good'
                    elif score >= 40:
                        rec['match_score'] = 'Fair'
                    else:
                        rec['match_score'] = 'Low'
                rec['source'] = 'Additional'
                hybrid_recommendations.append(rec)
                
        logger.info(f"Generated {len(hybrid_recommendations)} hybrid recommendations for query '{query}' (requested {limit}, min score {min_score})")
    except Exception as e:
        logger.error(f"Error generating hybrid recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail="Error generating hybrid recommendations")

    try:
        await redis_client.set(cache_key, hybrid_recommendations, expire=1800)  # 30 min
    except Exception as e:
        logger.warning(f"Failed to cache hybrid recommendations: {str(e)}")

    return hybrid_recommendations