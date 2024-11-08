import os
import time
from typing import List, Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from scrapegraphai.graphs import SmartScraperGraph
from scrapegraphai.utils import prettify_exec_info

# Load environment variables if needed
load_dotenv()

# Define the schema to match your CSV structure
class InventoryItem(BaseModel):
    item_type: str = Field(description="Type of item (Phone/Tablet/Computer)")
    manufacturer: str = Field(description="Manufacturer/Brand name")
    name: str = Field(description="Product name")
    sku: str = Field(description="Product SKU/ID")
    instock_qty: Optional[int] = Field(description="Available quantity in stock")
    cost: Optional[float] = Field(description="Product cost")
    price: Optional[float] = Field(description="Product price")
    status: Optional[str] = Field(description="Product status")
    condition: Optional[str] = Field(description="Product condition")
    supplier: str = Field(default="MobileSentrix", description="Supplier name")

class Inventory(BaseModel):
    items: List[InventoryItem]

# Configure the scraping graph with enhanced features
graph_config = {
    "llm": {
        "model": "openai/gpt-4",
        "api_key": os.getenv("OPENAI_API_KEY"),
        "temperature": 0.2,
        # Add rate limiting for the LLM
        "rate_limit": {
            "requests_per_second": 1
        }
    },
    "verbose": True,
    "headless": False,
    # Add proxy configuration
    "loader_kwargs": {
        "proxy": {
            "server": os.getenv("PROXY_SERVER"),
            "username": os.getenv("josiahbv99@gmail.com"),
            "password": os.getenv("Battle2Field!"),
        },
        # Add authentication headers and cookies
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
        },
        # Add authentication cookies if needed
        "cookies": {
            "session_id": os.getenv("SESSION_ID"),
            "auth_token": os.getenv("AUTH_TOKEN")
        }
    },
    # Enable caching to avoid redundant requests
    "caching": True,
    # Add retry mechanism
    "reattempt": True,
    # Use undetected Chrome to bypass anti-bot measures
    "backend": "undetected_chromedriver"
}

# List of categories to scrape
categories = ["Cell Phones",
            "Tablets",
            "Computers"
]

def scrape_with_retry(url, max_retries=3, delay=5):
    """Scrape with retry mechanism"""
    for attempt in range(max_retries):
        try:
            scraper = SmartScraperGraph(
                prompt="""Extract all product information including:
                - Item type (Phone/Tablet/Computer)
                - Manufacturer
                - Product name
                - SKU
                - Stock quantity
                - Cost/Price
                - Status
                - Condition
                
                Important: Make sure to extract all available information from the product listings.
                If pagination is present, analyze all pages.
                If a product has multiple variants, list each separately.
                Format the data according to the provided schema.""",
                source=url,
                config=graph_config,
                schema=Inventory
            )
            
            result = scraper.run()
            
            # Get execution info for monitoring
            exec_info = scraper.get_execution_info()
            print(prettify_exec_info(exec_info))
            
            return result
            
        except Exception as e:
            print(f"Attempt {attempt + 1} failed for {url}: {str(e)}")
            if attempt < max_retries - 1:
                print(f"Waiting {delay} seconds before retry...")
                time.sleep(delay)
                # Increase delay for next retry
                delay *= 2
            else:
                print(f"Failed to scrape {url} after {max_retries} attempts")
                raise

# Main scraping loop
for category_url in categories:
    try:
        print(f"\nScraping category: {category_url}")
        result = scrape_with_retry(category_url)
        
        # Save results to file
        category_name = category_url.split('/')[-1]
        filename = f"mobilesentrix_{category_name}_{time.strftime('%Y%m%d')}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(str(result))
            
        print(f"Results saved to {filename}")
        
        # Add delay between categories to avoid rate limiting
        time.sleep(5)
        
    except Exception as e:
        print(f"Error scraping {category_url}: {str(e)}")
        continue
