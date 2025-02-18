from enum import Enum
import re
import json
import requests
from typing import Optional
from dotenv import load_dotenv
import os
from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import ResponseSchema, StructuredOutputParser

load_dotenv()

QUERY_API_URL = os.getenv("QUERY_API_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PRICING_TOKEN = os.getenv("PRICING_TOKEN")


#This is the enum for intent detection
class QueryIntent(Enum):
    PRODUCT_SEARCH = "product_search"
    PRODUCT_PRICE = "product_price"
    PRODUCT_INFO = "product_info"
    STORE_INFO = "store_info"
    UNKNOWN = "unknown"

class QueryFailedError(Exception):
    """Raised when a query fails to return meaningful results"""
    pass

class AgentManager:
    """
    This is the class for the agent manager.
    It is responsible for detecting the intent of the user's query and handling the query.
    """
    def __init__(self):
        self.base_url = QUERY_API_URL
        self.llm = ChatOpenAI(model_name="gpt-4", temperature=0, openai_api_key=OPENAI_API_KEY)

        # Define the output schemas
        self.product_info_schemas = [
            ResponseSchema(
                name="brand",
                description="The brand name of the product (if mentioned)"
            ),
            ResponseSchema(
                name="model",
                description="The model name or type of the product"
            ),
            ResponseSchema(
                name="search_query",
                description="A cleaned up search query combining brand and model"
            )
        ]
        self.product_info_parser = StructuredOutputParser.from_response_schemas(self.product_info_schemas)

    def detect_intent(self, query: str) -> tuple[QueryIntent, dict]:
        # First check for direct patterns
        part_match = re.search(r'[A-Z0-9]{8,}', query.upper())
        if part_match:
            if "price" in query.lower():
                print("🎯 Direct match: Found part number and price request")
                return QueryIntent.PRODUCT_PRICE, {"part_number": part_match.group(), "original_query": query}
            print("🎯 Direct match: Found part number")
            return QueryIntent.PRODUCT_INFO, {"part_number": part_match.group(), "original_query": query}

        # If no direct match, use GPT for planning
        return self._gpt_planning(query)

    def _gpt_planning(self, query: str) -> tuple[QueryIntent, dict]:
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an API planning agent for a pool equipment store. Analyze the user query and determine:
            1. The most appropriate intent
            2. Which API endpoint to use
            3. What parameters to include

            For product searches:
            - If the query mentions specific brands or models (like "Hayward SuperPump"), 
              extract these details and use them in the search.
            - Use vector search (/api/products/search) for better semantic matching.

            Available API endpoints:
            - GET /api/products/search: Vector-enhanced search (params: query, limit)
            - GET /api/search: Basic product search (params: term, page_size, page)
            - GET /api/products/{part_number}: Get product details (only for exact part numbers)
            - POST /api/pricing: Get pricing info
            - GET /api/stores/search: Find stores

            Format your response as JSON with these keys:
            - intent: (PRODUCT_SEARCH, PRODUCT_PRICE, PRODUCT_INFO, STORE_INFO)
            - api_endpoint: (the endpoint to use)
            - parameters: (parameters to send)
            - reasoning: (brief explanation)
            """),
            ("human", "{query}")
        ])
        print(f"🧠 GPT Planning Prompt: {prompt}")
        messages = prompt.format_messages(query=query)
        response = self.llm.invoke(messages)
        print(f"🧠 GPT Planning Response: {response.content}")

        try:
            parsed = json.loads(response.content)
            intent = QueryIntent[parsed["intent"]]
            
            # Default to product search for brand/model queries
            if "brand" in parsed["parameters"] or "model" in parsed["parameters"]:
                search_query = " ".join(filter(None, [
                    parsed["parameters"].get("brand", ""),
                    parsed["parameters"].get("model", "")
                ]))
                return QueryIntent.PRODUCT_SEARCH, {"query": search_query}
            
            # Handle other cases
            if intent == QueryIntent.PRODUCT_SEARCH:
                return intent, {"query": query}
            elif intent in [QueryIntent.PRODUCT_PRICE, QueryIntent.PRODUCT_INFO]:
                if "part_number" in parsed["parameters"]:
                    return intent, {"part_number": parsed["parameters"]["part_number"]}
                return QueryIntent.PRODUCT_SEARCH, {"query": query}
            else:
                return intent, parsed["parameters"]

        except Exception as e:
            print(f"❌ Error parsing GPT response: {str(e)}")
            return QueryIntent.PRODUCT_SEARCH, {"query": query}

    def _extract_product_info(self, query: str) -> dict:
        """Extract brand and model information from query using GPT"""
        system_prompt = """You are a product information extractor for a pool equipment store. 
        Extract brand and model information from customer queries.

        Respond with ONLY a JSON object containing these fields:
        - brand: The brand name (if mentioned)
        - model: The model or product type
        - search_query: Combined brand and model

        Example Input: "Do you have Hayward SuperPumps?"
        Example Output:
        {
            "brand": "Hayward",
            "model": "SuperPump",
            "search_query": "Hayward SuperPump"
        }"""

        print(f"🔍 Extracting product info from: {query}")
        try:
            # Create messages directly without using ChatPromptTemplate
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ]
            
            response = self.llm.invoke(messages)
            print(f"🔍 Raw GPT Response: {response.content}")
            
            # Clean up the response content
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            elif content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            # Parse the JSON response
            parsed_info = json.loads(content)
            
            # Ensure all fields exist
            result = {
                "brand": str(parsed_info.get("brand", "")).strip(),
                "model": str(parsed_info.get("model", "")).strip(),
                "search_query": str(parsed_info.get("search_query", "")).strip()
            }
            
            # If search_query is empty, construct it
            if not result["search_query"]:
                result["search_query"] = " ".join(filter(None, [
                    result["brand"],
                    result["model"]
                ]))
            
            if not result["search_query"]:
                result["search_query"] = query
                
            print(f"📦 Extracted Info: {result}")
            return result
            
        except Exception as e:
            print(f"❌ Error in product info extraction: {str(e)}")
            print(f"❌ Error type: {type(e)}")
            import traceback
            print("❌ Full Traceback:")
            traceback.print_exc()
            return {"brand": "", "model": "", "search_query": query}

    async def _summarize_response(self, raw_response: str, intent: QueryIntent, query: str) -> str:
        """Summarize and format the raw response data using GPT to make it more user-friendly"""
        system_prompt = """You are a helpful pool equipment store assistant. 
        Summarize the product information in a natural, conversational way.
        Focus on the most relevant details based on the user's intent.
        
        Keep these guidelines in mind:
        - Be concise but friendly
        - Highlight the most relevant information first
        - Include all important product details
        - Maintain any links or images from the original response
        - If prices are mentioned, keep them exactly as shown
        """

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", f"""Original query: {query}
            Query intent: {intent.value}
            Raw response: {raw_response}
            
            Please provide a natural, conversational summary.""")
        ])

        try:
            messages = prompt.format_messages()
            response = self.llm.invoke(messages)
            return response.content.strip()
        except Exception as e:
            print(f"❌ Error in response summarization: {str(e)}")
            return raw_response  # Fall back to original response if summarization fails

    async def process_query(self, query: str) -> str:
        print(f"\n🔍 Processing query: '{query}'")
        try:
            intent, params = self.detect_intent(query)
            print(f"🎯 Initial Intent: {intent.value}")
            print(f"📋 Initial Parameters: {params}")
            
            try:
                raw_result = await self._try_direct_query(intent, params, query)
                # Summarize the response before returning
                return await self._summarize_response(raw_result, intent, query)
            except QueryFailedError as e:
                print(f"⚠️ Initial query failed: {str(e)}, falling back to GPT planning")
                try:
                    product_info = self._extract_product_info(query)
                    print(f"📦 Extracted Product Info: {product_info}")
                    
                    if product_info.get("search_query"):
                        raw_result = await self._handle_product_search(product_info["search_query"])
                        return await self._summarize_response(raw_result, QueryIntent.PRODUCT_SEARCH, query)
                    
                    raw_result = await self._handle_product_search(query)
                    return await self._summarize_response(raw_result, QueryIntent.PRODUCT_SEARCH, query)
                except Exception as extract_error:
                    print(f"❌ Error during extraction fallback: {str(extract_error)}")
                    import traceback
                    print("📍 Extraction Error Traceback:")
                    traceback.print_exc()
                    raise

        except Exception as e:
            print(f"❌ Error in process_query: {str(e)}")
            print(f"❌ Error type: {type(e)}")
            import traceback
            print("❌ Full Process Query Traceback:")
            traceback.print_exc()
            return "I apologize, but I couldn't find what you're looking for. Could you please try rephrasing your question?"

    async def _handle_product_search(self, query: str) -> str:
        # Clean and format the search query (remove spaces)
        formatted_query = "".join(query.split())
        print(f"🔎 Searching for products with query: {formatted_query}")
        
        # First try direct model number lookup
        try:
            model_response = requests.get(f"{self.base_url}/api/products/{formatted_query}")
            if model_response.status_code == 200:
                print("✅ Found exact model number match")
                item = model_response.json()
                result = "I found the exact product you're looking for:\n\n"
                result += f"🔹 {item['product_name']}\n"
                result += f"   Brand: {item['brand']}\n"
                result += f"   Part Number: {item['part_number']}\n"
                if item.get('description'):
                    result += f"   Description: {item['description']}\n"
                if item.get('image_url'):
                    result += f"   [View Image]({item['image_url']})\n"
                result += f"   [More Details](https://www.heritagepoolplus.com/{item['heritage_link']})\n\n"
                return result
        except Exception as e:
            print(f"ℹ️ No exact model match found: {str(e)}")
        
        # First try Azure Cognitive Search with formatted query
        response = requests.get(
            f"{self.base_url}/api/products/search",
            params={
                "query": formatted_query,
                "limit": 3
            }
        )
        
        data = response.json()
        if not data.get("items"):
            # If no results, try with original query as fallback
            print(f"ℹ️ No results with formatted query, trying original: {query}")
            response = requests.get(
                f"{self.base_url}/api/products/search",
                params={
                    "query": query,
                    "limit": 3
                }
            )
            data = response.json()
            
            # If still no results, try Klevu search
            if not data.get("items"):
                print("ℹ️ No results from Azure search, falling back to Klevu")
                response = requests.get(
                    f"{self.base_url}/api/search",
                    params={
                        "term": query,
                        "page_size": 5,
                        "page": 1
                    }
                )
                data = response.json()
                if not data.get("items"):
                    raise QueryFailedError(f"No products found matching '{query}'")
        
        result = "Here's what I found:\n\n"
        for item in data["items"]:
            if "product_name" in item:  # Azure search response
                result += f"🔹 {item['product_name']}\n"
                result += f"   Brand: {item['brand']}\n"
                result += f"   Part Number: {item['part_number']}\n"
                if item.get('image_url'):
                    result += f"   [View Image]({item['image_url']})\n"
                result += f"   [More Details](https://www.heritagepoolplus.com/{item['heritage_link']})\n\n"
            else:  # Klevu search response
                result += f"🔹 Part Number: {item['part_number']}\n"
                result += f"   ID: {item['id']}\n\n"
        
        return result

    async def _handle_price_query(self, part_number: str) -> str:
        if not part_number:
            raise QueryFailedError("No part number provided")

        product_response = requests.get(f"{self.base_url}/api/products/{part_number}")
        if product_response.status_code != 200:
            raise QueryFailedError(f"Couldn't find product with part number {part_number}")
        
        product_data = product_response.json()

        # Then get pricing information
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer eyJraWQiOiIxIiwiYWxnIjoiSFMyNTYifQ.eyJ1aWQiOjE0OTU1NywidXR5cGlkIjozLCJpYXQiOjE3Mzk4OTcwNjgsImV4cCI6MTczOTkyNTg2OH0.SlXyEEG9l0oauOiLKg6Kes23uY_VPIsnRQkaN1H_js4'
        }
        payload = {
            "items": [
                {
                    "item_code": part_number,
                    "unit": "EA"
                }
            ]
        }
        
        price_response = requests.post(
            f"{self.base_url}/api/pricing",
            json=payload,
            headers=headers
        )
        
        if price_response.status_code != 200:
            return f"Sorry, I couldn't retrieve pricing information. Error: {price_response.json().get('detail', 'Unknown error')}"
        
        price_data = price_response.json()
        if not price_data.get("items"):
            return "I couldn't find pricing information for that part."

        price_item = price_data["items"][0]
        
        result = f"📊 {product_data['product_name']}\n"
        result += f"• Brand: {product_data['brand']}\n"
        result += f"• Part Number: {part_number}\n"
        result += f"• Price: ${price_item['price']:.2f}\n"
        result += f"• Stock Status: {'In Stock' if price_item['in_stock'] else 'Out of Stock'}"
        if price_item.get('available_quantity'):
            result += f" ({price_item['available_quantity']} available)"
        
        return result

    async def _handle_product_info(self, part_number: str) -> str:
        if not part_number:
            raise QueryFailedError("No part number provided")

        response = requests.get(f"{self.base_url}/api/products/{part_number}")
        if response.status_code != 200:
            raise QueryFailedError(f"Couldn't find information for part number {part_number}")
            
        data = response.json()
        
        result = f"ℹ️ Product Information:\n"
        result += f"• Name: {data['product_name']}\n"
        result += f"• Brand: {data['brand']}\n"
        result += f"• Description: {data['description']}\n"
        result += f"• Manufacturer ID: {data['manufacturer_id']}\n"
        if data.get('image_url'):
            result += f"• [View Image]({data['image_url']})\n"
        result += f"• [More Details](https://www.heritagepoolplus.com/{data['heritage_link']})"    
        
        return result

    async def _handle_store_info(self, query: str) -> str:
        # Using Atlanta coordinates as default
        response = requests.get(
            f"{self.base_url}/api/stores/search",
            params={
                "latitude": 33.7490,
                "longitude": -84.3880,
                "radius": 50,
                "page_size": 5,
                "page": 1
            }
        )
        
        data = response.json()
        
        if not data.get("stores"):
            return "I couldn't find any store information."

        result = "📍 Nearby Stores:\n\n"
        for store in data["stores"]:
            result += f"🏪 {store['name']}\n"
            result += f"📍 {store['address']['street']}, {store['address']['city']}, "
            result += f"{store['address']['state']} {store['address']['zip']}\n"
            result += f"📞 {store['contact']['phone']}\n"
            result += f"📧 {store['contact']['email']}\n"
            if store.get('location', {}).get('distance'):
                result += f"📏 {store['location']['distance']:.1f} miles away\n"
            
            if store.get('hours'):
                result += "⏰ Hours:\n"
                for day, times in store['hours'].items():
                    if times['open'] and times['close']:
                        result += f"   {day.capitalize()}: {times['open']} - {times['close']}\n"
            result += "\n"
        
        return result

    async def _try_direct_query(self, intent: QueryIntent, params: dict, original_query: str) -> str:
        """Helper method to execute queries based on intent"""
        if intent == QueryIntent.PRODUCT_INFO:
            if params.get("part_number"):
                return await self._handle_product_info(params["part_number"])
            raise QueryFailedError("No part number found for product info query")
            
        elif intent == QueryIntent.PRODUCT_SEARCH:
            return await self._handle_product_search(params.get("query", original_query))
            
        elif intent == QueryIntent.PRODUCT_PRICE:
            if params.get("part_number"):
                return await self._handle_price_query(params["part_number"])
            raise QueryFailedError("No part number found for price query")
            
        elif intent == QueryIntent.STORE_INFO:
            return await self._handle_store_info(original_query)
            
        raise QueryFailedError("Unknown query intent") 