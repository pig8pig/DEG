"""
Comprehensive test suite for Beckn Protocol Integration
Tests all API endpoints: discover, select, init, confirm, update, status, rating, support
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from beckn_client import BecknClient
import json
import uuid
from datetime import datetime

def print_section(title):
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")

def print_response(action, response):
    print(f"✓ {action} Response:")
    print(json.dumps(response, indent=2))
    print()

def test_discover():
    """Test the discover API call"""
    print_section("TEST 1: DISCOVER - Search for Grid Flexibility Windows")
    
    client = BecknClient()
    response = client.discover(query="Grid flexibility windows")
    
    print_response("DISCOVER", response)
    
    # Extract provider info for next steps
    catalog = response.get("message", {}).get("catalog", {})
    providers = catalog.get("beckn:providers", [])
    
    if providers:
        provider = providers[0]
        provider_id = provider.get("beckn:id")
        items = provider.get("beckn:items", [])
        if items:
            item_id = items[0].get("beckn:id")
            print(f"Found Provider: {provider_id}")
            print(f"Found Item: {item_id}")
            return provider_id, item_id, response["context"]["transaction_id"]
    
    # Fallback to mock data
    return "provider-gridflex-001", "item-ce-cambridge-morning-001", str(uuid.uuid4())

def test_select(provider_id, item_id, transaction_id):
    """Test the select API call"""
    print_section("TEST 2: SELECT - Request Quote for Specific Item")
    
    client = BecknClient()
    bpp_id = "ev-charging.sandbox1.com"
    bpp_uri = "https://ev-charging.sandbox1.com.com/bpp"
    
    response = client.select(
        transaction_id=transaction_id,
        bpp_id=bpp_id,
        bpp_uri=bpp_uri,
        item_id=item_id,
        provider_id=provider_id
    )
    
    print_response("SELECT", response)
    
    # Extract order details for next steps
    order = response.get("message", {}).get("order", {})
    order_id = order.get("beckn:id")
    
    return order_id, order, bpp_id, bpp_uri

def test_init(transaction_id, order_details, bpp_id, bpp_uri):
    """Test the init API call"""
    print_section("TEST 3: INIT - Initialize Order with Customer Details")
    
    client = BecknClient()
    
    # Add customer invoice details as per documentation
    order_details["beckn:invoice"] = {
        "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/draft/schema/core/v2/context.jsonld",
        "@type": "schema:Invoice",
        "schema:customer": {
            "email": "test.user@computecloud.ai",
            "phone": "+44 7911 123456",
            "legalName": "ComputeCloud.ai",
            "address": {
                "streetAddress": "123 Test St",
                "addressLocality": "Cambridge",
                "addressRegion": "East England",
                "postalCode": "CB1 2AB",
                "addressCountry": "GB"
            }
        }
    }
    
    # Add fulfillment details
    order_details["beckn:fulfillment"] = {
        "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/draft/schema/core/v2/context.jsonld",
        "@type": "beckn:Fulfillment",
        "beckn:id": f"fulfillment-{str(uuid.uuid4())[:8]}",
        "beckn:mode": "GRID-BASED",
        "beckn:status": "PENDING"
    }
    
    response = client.init(
        transaction_id=transaction_id,
        bpp_id=bpp_id,
        bpp_uri=bpp_uri,
        order_details=order_details
    )
    
    print_response("INIT", response)
    
    return response.get("message", {}).get("order", order_details)

def test_confirm(transaction_id, order_details, bpp_id, bpp_uri):
    """Test the confirm API call"""
    print_section("TEST 4: CONFIRM - Confirm the Order")
    
    client = BecknClient()
    
    # Update fulfillment status
    if "beckn:fulfillment" in order_details:
        order_details["beckn:fulfillment"]["beckn:status"] = "CONFIRMED"
    
    # Add payment details as per documentation
    order_details["beckn:payment"] = {
        "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/draft/schema/ComputeEnergy/v1/context.jsonld",
        "@type": "beckn:ComputeEnergyPayment",
        "beckn:settlement": "next-billing-cycle"
    }
    
    response = client.confirm(
        transaction_id=transaction_id,
        bpp_id=bpp_id,
        bpp_uri=bpp_uri,
        order_details=order_details
    )
    
    print_response("CONFIRM", response)
    
    order_id = response.get("message", {}).get("order", {}).get("beckn:id")
    return order_id

def test_status(transaction_id, order_id, bpp_id, bpp_uri):
    """Test the status API call"""
    print_section("TEST 5: STATUS - Check Order Status")
    
    client = BecknClient()
    
    response = client.status(
        transaction_id=transaction_id,
        bpp_id=bpp_id,
        bpp_uri=bpp_uri,
        order_id=order_id
    )
    
    print_response("STATUS", response)

def test_update_workload_shift(transaction_id, order_id, bpp_id, bpp_uri):
    """Test the update API call with workload shift"""
    print_section("TEST 6: UPDATE - Workload Shift (Flexibility Response)")
    
    client = BecknClient()
    
    update_details = {
        "fulfillment": {
            "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/draft/schema/core/v2/context.jsonld",
            "@type": "beckn:Fulfillment",
            "beckn:id": "fulfillment-ce-cambridge-001",
            "beckn:mode": "GRID-BASED",
            "beckn:status": "IN_PROGRESS",
            "beckn:deliveryAttributes": {
                "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/draft/schema/ComputeEnergy/v1/context.jsonld",
                "@type": "beckn:ComputeEnergyFulfillment",
                "beckn:flexibilityAction": {
                    "actionType": "workload_shift",
                    "actionReason": "grid_stress_response",
                    "actionTimestamp": datetime.utcnow().isoformat() + "Z",
                    "shiftDetails": {
                        "shiftedLoad": 0.3,
                        "shiftedLoadUnit": "MW",
                        "sourceLocation": "Cambridge",
                        "targetLocation": "Manchester"
                    }
                }
            }
        }
    }
    
    response = client.update(
        transaction_id=transaction_id,
        bpp_id=bpp_id,
        bpp_uri=bpp_uri,
        order_id=order_id,
        update_type="flexibility_response",
        update_details=update_details
    )
    
    print_response("UPDATE (Workload Shift)", response)

def test_update_carbon_acknowledgement(transaction_id, order_id, bpp_id, bpp_uri):
    """Test the update API call with carbon intensity acknowledgement"""
    print_section("TEST 7: UPDATE - Carbon Intensity Acknowledgement")
    
    client = BecknClient()
    
    update_details = {
        "fulfillment": {
            "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/draft/schema/core/v2/context.jsonld",
            "@type": "beckn:Fulfillment",
            "beckn:id": "fulfillment-ce-cambridge-001",
            "beckn:mode": "GRID-BASED",
            "beckn:status": "IN_PROGRESS",
            "beckn:deliveryAttributes": {
                "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/draft/schema/ComputeEnergy/v1/context.jsonld",
                "@type": "beckn:ComputeEnergyFulfillment",
                "beckn:flexibilityAction": {
                    "actionType": "continue_with_acknowledgement",
                    "actionReason": "acceptable_carbon_cost_tradeoff",
                    "actionTimestamp": datetime.utcnow().isoformat() + "Z",
                    "decision": {
                        "decisionType": "continue_execution",
                        "decisionRationale": "Carbon intensity spike within acceptable threshold",
                        "acceptedCarbonIntensity": 320,
                        "acceptedCarbonIntensityUnit": "gCO2/kWh"
                    }
                }
            }
        }
    }
    
    response = client.update(
        transaction_id=transaction_id,
        bpp_id=bpp_id,
        bpp_uri=bpp_uri,
        order_id=order_id,
        update_type="alert_acknowledgement",
        update_details=update_details
    )
    
    print_response("UPDATE (Carbon Acknowledgement)", response)

def test_rating(transaction_id, order_id, bpp_id, bpp_uri):
    """Test the rating API call"""
    print_section("TEST 8: RATING - Submit Service Rating")
    
    client = BecknClient()
    
    feedback = {
        "comments": "Excellent grid flexibility service! Real-time signals were accurate.",
        "tags": [
            "accurate-signals",
            "seamless-integration",
            "carbon-savings"
        ]
    }
    
    response = client.rating(
        transaction_id=transaction_id,
        bpp_id=bpp_id,
        bpp_uri=bpp_uri,
        order_id=order_id,
        rating_value=5,
        feedback=feedback
    )
    
    print_response("RATING", response)

def test_support(transaction_id, order_id, bpp_id, bpp_uri):
    """Test the support API call"""
    print_section("TEST 9: SUPPORT - Request Support Information")
    
    client = BecknClient()
    
    response = client.support(
        transaction_id=transaction_id,
        bpp_id=bpp_id,
        bpp_uri=bpp_uri,
        order_id=order_id
    )
    
    print_response("SUPPORT", response)

def run_all_tests():
    """Run all Beckn API tests in sequence"""
    print("\n" + "█"*80)
    print("█" + " "*78 + "█")
    print("█" + "  BECKN PROTOCOL INTEGRATION - COMPREHENSIVE TEST SUITE".center(78) + "█")
    print("█" + " "*78 + "█")
    print("█"*80)
    
    try:
        # Test 1: Discover
        provider_id, item_id, transaction_id = test_discover()
        
        # Test 2: Select
        order_id, order_details, bpp_id, bpp_uri = test_select(provider_id, item_id, transaction_id)
        
        # Test 3: Init
        order_details = test_init(transaction_id, order_details, bpp_id, bpp_uri)
        
        # Test 4: Confirm
        order_id = test_confirm(transaction_id, order_details, bpp_id, bpp_uri)
        
        # Test 5: Status
        test_status(transaction_id, order_id, bpp_id, bpp_uri)
        
        # Test 6: Update - Workload Shift
        test_update_workload_shift(transaction_id, order_id, bpp_id, bpp_uri)
        
        # Test 7: Update - Carbon Acknowledgement
        test_update_carbon_acknowledgement(transaction_id, order_id, bpp_id, bpp_uri)
        
        # Test 8: Rating
        test_rating(transaction_id, order_id, bpp_id, bpp_uri)
        
        # Test 9: Support
        test_support(transaction_id, order_id, bpp_id, bpp_uri)
        
        print_section("✅ ALL TESTS COMPLETED SUCCESSFULLY")
        
    except Exception as e:
        print_section(f"❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_all_tests()
