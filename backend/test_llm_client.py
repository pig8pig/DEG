#!/usr/bin/env python3
"""
Test script to verify LLM client integration.
Tests both basic LLM connectivity and agent report synthesis.
"""

import os
import sys
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from llm_client import LLMClient


def test_basic_synthesis():
    """Test basic LLM synthesis functionality."""
    print("=" * 60)
    print("Testing Basic LLM Synthesis")
    print("=" * 60)
    
    client = LLMClient()
    
    if not client.client:
        print("❌ FAILED: ASI_API_KEY not set or client initialization failed")
        print("\nPlease set the ASI_API_KEY environment variable:")
        print("  export ASI_API_KEY='your_api_key_here'")
        return False
    
    print("✓ LLM client initialized successfully")
    
    # Test simple synthesis
    test_prompt = "What is the capital of Japan? Answer in one sentence."
    print(f"\nTest prompt: {test_prompt}")
    
    result = client.synthesize(test_prompt, max_tokens=50)
    
    if result:
        print(f"✓ LLM Response: {result}")
        return True
    else:
        print("❌ FAILED: No response from LLM")
        return False


def test_agent_report_synthesis():
    """Test agent report synthesis functionality."""
    print("\n" + "=" * 60)
    print("Testing Agent Report Synthesis")
    print("=" * 60)
    
    client = LLMClient()
    
    if not client.client:
        print("❌ SKIPPED: ASI_API_KEY not set")
        return False
    
    # Create sample agent data
    sample_data = {
        "name": "Cambridge",
        "region": "South UK",
        "location_data": {
            "locality": "Cambridge",
            "carbon_intensity": 245,
            "renewable_mix": 42,
            "grid_zone": "UK-South-1",
            "available_capacity": 150
        },
        "energy_data": {
            "price": 0.15,
            "carbon_intensity": 250,
            "renewable_mix": 40
        },
        "active_tasks_count": 3,
        "available_capacity": 1
    }
    
    print("\nSample agent data:")
    print(f"  Agent: {sample_data['name']}")
    print(f"  Region: {sample_data['region']}")
    print(f"  Active Tasks: {sample_data['active_tasks_count']}")
    print(f"  Carbon Intensity: {sample_data['location_data']['carbon_intensity']} gCO2/kWh")
    print(f"  Renewable Mix: {sample_data['location_data']['renewable_mix']}%")
    
    print("\nGenerating synthesis...")
    result = client.synthesize_agent_report(sample_data)
    
    if result:
        print(f"\n✓ Synthesized Summary:\n")
        print(f"  {result}")
        return True
    else:
        print("❌ FAILED: No synthesis generated")
        return False


def main():
    """Run all tests."""
    print("\n🧪 LLM Client Integration Tests")
    print(f"Timestamp: {datetime.now().isoformat()}\n")
    
    # Check for API key
    api_key = os.environ.get("ASI_API_KEY")
    if not api_key:
        print("⚠️  WARNING: ASI_API_KEY environment variable not set")
        print("Tests will fail without a valid API key.\n")
    else:
        print(f"✓ ASI_API_KEY found (length: {len(api_key)})\n")
    
    # Run tests
    test1_passed = test_basic_synthesis()
    test2_passed = test_agent_report_synthesis()
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Basic Synthesis: {'✓ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Agent Report Synthesis: {'✓ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
