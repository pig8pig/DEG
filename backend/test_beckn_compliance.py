"""
Test Beckn Protocol Compliance for Compute-Energy Integration
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from beckn_client import BecknClient
from beckn_models import ComputeJob
from datetime import datetime, timedelta
import uuid

def test_init_with_compute_job():
    """Test that init method properly enriches order with ComputeJob data"""
    
    # Create a test ComputeJob
    job = ComputeJob(
        job_id=str(uuid.uuid4()),
        num_computations=1000.0,
        estimated_runtime_hrs=2.5,
        priority=4,
        status="PENDING",
        start_time_earliest=datetime.utcnow(),
        deadline_latest=datetime.utcnow() + timedelta(hours=24)
    )
    
    # Create BecknClient
    client = BecknClient()
    
    # Mock order details from select
    order_details = {
        "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/draft/schema/core/v2/context.jsonld",
        "@type": "beckn:Order",
        "beckn:id": str(uuid.uuid4()),
        "beckn:seller": "test-provider",
        "beckn:buyer": "test-buyer",
        "beckn:orderItems": []
    }
    
    # Call init with job
    result = client.init(
        transaction_id=str(uuid.uuid4()),
        bpp_id="test-bpp",
        bpp_uri="https://test-bpp.com",
        order_details=order_details,
        job=job
    )
    
    # Verify structure
    assert "message" in result, "Result should have 'message' field"
    assert "order" in result["message"], "Message should have 'order' field"
    
    order = result["message"]["order"]
    
    # Check order status
    assert order["beckn:orderStatus"] == "INITIALIZED", "Order status should be INITIALIZED"
    
    # Check fulfillment details
    assert "beckn:fulfillment" in order, "Order should have fulfillment details"
    fulfillment = order["beckn:fulfillment"]
    
    assert fulfillment["beckn:mode"] == "GRID-BASED", "Fulfillment mode should be GRID-BASED"
    assert fulfillment["beckn:status"] == "PENDING", "Fulfillment status should be PENDING"
    
    # Check delivery attributes
    assert "beckn:deliveryAttributes" in fulfillment, "Fulfillment should have delivery attributes"
    delivery = fulfillment["beckn:deliveryAttributes"]
    
    assert "@type" in delivery, "Delivery attributes should have @type"
    assert delivery["@type"] == "beckn:ComputeEnergyFulfillment", "Should be ComputeEnergyFulfillment type"
    
    # Check compute load
    assert "beckn:computeLoad" in delivery, "Should have compute load"
    assert delivery["beckn:computeLoad"] == job.estimated_runtime_hrs * 1.2, "Compute load should match calculation"
    assert delivery["beckn:computeLoadUnit"] == "MW", "Compute load unit should be MW"
    
    # Check time window
    assert "beckn:timeWindow" in delivery, "Should have time window"
    time_window = delivery["beckn:timeWindow"]
    assert "start" in time_window, "Time window should have start"
    assert "end" in time_window, "Time window should have end"
    
    # Check workload metadata
    assert "beckn:workloadMetadata" in delivery, "Should have workload metadata"
    metadata = delivery["beckn:workloadMetadata"]
    assert metadata["workloadId"] == job.job_id, "Workload ID should match job ID"
    assert metadata["workloadType"] == "BATCH_COMPUTE", "Should have workload type"
    assert "gpuHours" in metadata, "Should have GPU hours estimate"
    assert "carbonBudget" in metadata, "Should have carbon budget"
    
    # Check order attributes
    assert "beckn:orderAttributes" in order, "Order should have order attributes"
    order_attrs = order["beckn:orderAttributes"]
    
    assert order_attrs["@type"] == "beckn:ComputeEnergyOrder", "Should be ComputeEnergyOrder type"
    assert order_attrs["beckn:requestType"] == "compute_slot_reservation", "Request type should be compute_slot_reservation"
    assert order_attrs["beckn:priority"] in ["low", "medium", "high"], "Priority should be valid"
    assert order_attrs["beckn:flexibilityLevel"] == "high", "Flexibility level should be high"
    
    # Check invoice
    assert "beckn:invoice" in order, "Order should have invoice"
    invoice = order["beckn:invoice"]
    assert "@type" in invoice, "Invoice should have @type"
    assert "schema:customer" in invoice, "Invoice should have customer"
    
    print("✅ All Beckn Compute-Energy compliance tests passed!")
    print(f"   - Order status: {order['beckn:orderStatus']}")
    print(f"   - Compute load: {delivery['beckn:computeLoad']} {delivery['beckn:computeLoadUnit']}")
    print(f"   - Workload ID: {metadata['workloadId']}")
    print(f"   - Priority: {order_attrs['beckn:priority']}")
    print(f"   - Carbon budget: {metadata['carbonBudget']} {metadata['carbonBudgetUnit']}")
    
    return True

def test_init_without_job():
    """Test that init works without ComputeJob (backward compatibility)"""
    
    client = BecknClient()
    
    order_details = {
        "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/draft/schema/core/v2/context.jsonld",
        "@type": "beckn:Order",
        "beckn:id": str(uuid.uuid4()),
        "beckn:seller": "test-provider",
        "beckn:buyer": "test-buyer",
        "beckn:orderItems": []
    }
    
    result = client.init(
        transaction_id=str(uuid.uuid4()),
        bpp_id="test-bpp",
        bpp_uri="https://test-bpp.com",
        order_details=order_details
        # Note: job parameter omitted (defaults to None)
    )
    
    assert "message" in result
    assert "order" in result["message"]
    assert result["message"]["order"]["beckn:orderStatus"] == "INITIALIZED"
    
    print("✅ Backward compatibility test passed!")
    print("   - Init works without job parameter")
    print("   - Order status correctly set to INITIALIZED")
    
    return True

if __name__ == "__main__":
    print("Testing Beckn Protocol Compute-Energy Compliance\n")
    print("=" * 60)
    
    try:
        test_init_with_compute_job()
        print()
        test_init_without_job()
        print()
        print("=" * 60)
        print("🎉 All tests passed! Beckn integration is compliant.")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
