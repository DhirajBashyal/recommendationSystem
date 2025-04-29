import os
from typing import Dict, List, Any, Optional
import aiohttp
import logging
import json

from app.core.config import settings

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.api_url = "https://api.openai.com/v1/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def generate_recommendations(
        self, 
        user_preferences: str,
        product_descriptions: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Generate product recommendations using LLM"""
        
        prompt = self._create_recommendation_prompt(user_preferences, product_descriptions)
        
        try:
            logger.info(f"Generating LLM recommendations based on: {user_preferences[:100]}...")
            response = await self._call_llm_api(prompt)
            
            recommended_products = self._parse_recommendations(response, product_descriptions)
            
            logger.info(f"Generated {len(recommended_products)} LLM recommendations")
            return recommended_products[:top_k]
        except Exception as e:
            logger.error(f"Error generating LLM recommendations: {str(e)}")
            
            logger.info("Using fallback recommendations")
            return product_descriptions[:min(top_k, len(product_descriptions))]
    
    async def _call_llm_api(self, prompt: str) -> str:
        """Make API call to OpenAI"""
        payload = {
            "model": "gpt-3.5-turbo-instruct",
            "prompt": prompt,
            "max_tokens": 500,
            "temperature": 0.7
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, headers=self.headers, json=payload) as response:
                    response.raise_for_status()
                    result = await response.json()
                    return result["choices"][0]["text"]
        except aiohttp.ClientError as e:
            logger.error(f"API request error: {str(e)}")
            raise
        except KeyError as e:
            logger.error(f"Unexpected API response format: {str(e)}")
            raise
    
    def _create_recommendation_prompt(
        self, 
        user_preferences: str,
        product_descriptions: List[Dict[str, Any]]
    ) -> str:
        """Create a detailed prompt for the LLM"""
        
        # Convert product list to a string with complete details
        products_text = "\n".join([
            f"Product {i+1} (ID: {p['id']}): {p['name']} - {p['description']} - " + 
            f"Category: {p['category']} - Price: {p['price']} - Brand: {p.get('brand', 'Unknown')}"
            for i, p in enumerate(product_descriptions[:50])  # Limit to first 50 to keep prompt size reasonable
        ])
        
        # Build a detailed prompt
        prompt = f"""
You are a personalized product recommendation engine for an e-commerce platform.

Customer preferences: {user_preferences}

Available products:
{products_text}

Based on the customer preferences and available products, recommend the most suitable products.
Consider product categories, descriptions, brands, and any specific needs mentioned by the customer.
Rank products from most to least relevant.

Format your answer as a simple comma-separated list of product IDs (numbers only).
Example: 3, 17, 42, 9, 21
"""
        
        return prompt
    
    def _parse_recommendations(
        self, 
        llm_response: str,
        product_descriptions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Parse LLM response and return recommended products"""
        
        # Create ID to product mapping for faster lookups
        product_map = {p['id']: p for p in product_descriptions}
        
        try:
           
            cleaned_response = llm_response.strip()
            
            if ',' in cleaned_response:
                product_ids = []
                for part in cleaned_response.split(','):
                    try:
                        pid = int(part.strip())
                        product_ids.append(pid)
                    except ValueError:
                        
                        continue
            else:
               
                product_ids = []
                for line in cleaned_response.split('\n'):
                    try:
                      
                        stripped_line = line.strip()
                        if stripped_line.isdigit():
                            pid = int(stripped_line)
                            product_ids.append(pid)
                    except ValueError:
                        continue
            
           
            recommendations = []
            for pid in product_ids:
                if pid in product_map:
                    product = product_map[pid].copy()
                    
                    product['reason'] = "Recommended by AI based on your preferences."
                    
                    product['match_score'] = 95 - (product_ids.index(pid) * 5) 
                    recommendations.append(product)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error parsing LLM recommendations: {str(e)}")
            # Fallback to returning the first few products
            return product_descriptions[:5]
    
    async def generate_product_explanation(
        self,
        product: Dict[str, Any],
        user_preferences: str
    ) -> str:
        """Generate personalized explanation for why a product is recommended"""
        
        prompt = f"""
Product: {product['name']}
Description: {product['description']}
Category: {product['category']}
Brand: {product.get('brand', 'Unknown')}
Price: {product['price']}

Customer preferences: {user_preferences}

In 2-3 sentences, explain why this product would be a good match for this customer. 
Focus on how the product features align with their preferences.
"""
        
        try:
            explanation = await self._call_llm_api(prompt)
            return explanation.strip()
        except Exception as e:
            logger.error(f"Error generating product explanation: {str(e)}")
            return f"This {product['category']} product matches your preferences."