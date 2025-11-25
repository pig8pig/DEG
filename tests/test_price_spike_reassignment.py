import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime
import sys
import os

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from agents.local_agent import LocalAgent
from agents.regional_agent import RegionalAgent
from simulation.data_generator import DataGenerator
from beckn_models import ComputeJob

class TestPriceSpikeReassignment(unittest.TestCase):
    def setUp(self):
        self.generator = DataGenerator()
        self.agent_a = LocalAgent("Agent_A", "UK-South", self.generator)
        self.agent_b = LocalAgent("Agent_B", "UK-South", self.generator)
        self.regional_agent = RegionalAgent("Regional_South", "UK-South")
        
        self.regional_agent.register_local_agent(self.agent_a)
        self.regional_agent.register_local_agent(self.agent_b)
        
        # Mock BecknClient for both agents
        self.agent_a.beckn_client = MagicMock()
        self.agent_b.beckn_client = MagicMock()
        
        # Setup successful responses
        self.agent_a.beckn_client.select.return_value = {"message": {"order": {}}}
        self.agent_a.beckn_client.init.return_value = {"message": {"order": {"beckn:fulfillment": {}}}}
        self.agent_a.beckn_client.confirm.return_value = {"message": {"order": {"beckn:orderStatus": "CONFIRMED", "beckn:id": "order_123"}}}
        self.agent_a.beckn_client.status.return_value = {"message": {"order": {"beckn:orderStatus": "CONFIRMED"}}}
        self.agent_a.beckn_client.update.return_value = {}

        self.agent_b.beckn_client.select.return_value = {"message": {"order": {}}}
        self.agent_b.beckn_client.init.return_value = {"message": {"order": {"beckn:fulfillment": {}}}}
        self.agent_b.beckn_client.confirm.return_value = {"message": {"order": {"beckn:orderStatus": "CONFIRMED", "beckn:id": "order_456"}}}
        
        # Initialize capacity
        self.agent_a.total_capacity = 10
        self.agent_a.available_capacity = 10
        self.agent_b.total_capacity = 10
        self.agent_b.available_capacity = 10
        
    def test_reassignment_on_price_spike(self):
        # 1. Assign job to Agent A
        job = ComputeJob(
            job_id="job_spike_test",
            priority=1,
            estimated_runtime_hrs=1.0,
            num_computations=100, # Added required field
            submitted_at=datetime.now()
        )
        
        # Manually assign to A first
        print("\n[Test] Assigning job to Agent A...")
        success = self.agent_a.assign_job(job)
        self.assertTrue(success)
        self.assertIn("job_spike_test", self.agent_a.current_jobs)
        
        # 2. Simulate Price Spike on Agent A
        print("[Test] Simulating price spike on Agent A...")
        # Set location_data to ensure prices persist and aren't overwritten by generator
        self.agent_a.location_data = {
            'price': 0.50, 
            'carbon_intensity': 100, 
            'renewable_mix': 50,
            'available_capacity': 10
        }
        self.agent_b.location_data = {
            'price': 0.10, 
            'carbon_intensity': 100, 
            'renewable_mix': 50,
            'available_capacity': 10
        }
        
        # Ensure Agent B has capacity
        self.agent_b.available_capacity = 10
        
        # 3. Trigger Regional Update
        print("[Test] Triggering Regional Agent update...")
        self.regional_agent.update_state(datetime.now())
        
        # 4. Verify Reassignment
        print("[Test] Verifying reassignment...")
        
        # Check Agent A sent status check
        self.agent_a.beckn_client.status.assert_called()
        print(" - Agent A checked job status (Beckn Status API called)")
        
        # Check Agent A sent update
        self.agent_a.beckn_client.update.assert_called()
        call_args = self.agent_a.beckn_client.update.call_args
        self.assertEqual(call_args[1]['update_type'], "flexibility_response")
        print(" - Agent A sent workload shift update (Beckn Update API called)")
        
        # Check Job moved to Agent B
        self.assertIn("job_spike_test", self.agent_b.current_jobs)
        self.assertNotIn("job_spike_test", self.agent_a.current_jobs)
        print(" - Job successfully moved from Agent A to Agent B")

if __name__ == '__main__':
    unittest.main()
