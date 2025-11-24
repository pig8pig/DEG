import sys
import os
import json
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from beckn_client import BecknClient

def test_discovery():
    client = BecknClient()
    print("Calling discover()...")
    try:
        # Force the client to NOT use mock if possible, or just see what it returns.
        result = client.discover()
        with open('debug_output.json', 'w') as f:
            json.dump(result, f, indent=2)
        print("Wrote response to debug_output.json")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_discovery()
