import sys
import os
import json
import logging

# Add backend directory to path so we can import modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.beckn_client import BecknClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_discover():
    logger.info("Initializing BecknClient...")
    client = BecknClient()
    
    logger.info(f"Target URL: {client.base_url}")
    
    logger.info("Sending 'discover' request...")
    # We can pass a specific query if needed, but default is fine
    response = client.discover(query="Grid flexibility windows")
    
    logger.info("Response received.")
    print(json.dumps(response, indent=2))
    
    # Check if it's a mock response
    is_mock = False
    try:
        if response.get("message", {}).get("catalog", {}).get("beckn:descriptor", {}).get("name") == "Mock Catalog":
            is_mock = True
    except:
        pass
        
    if is_mock:
        logger.warning("WARNING: Received MOCK response. The API call to the sandbox likely failed.")
    else:
        logger.info("SUCCESS: Received response from the sandbox (or at least not the hardcoded mock).")

if __name__ == "__main__":
    test_discover()
