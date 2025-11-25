import sys
import os
from datetime import datetime, timedelta
import uuid

# Add current directory to path
sys.path.append(os.getcwd())

from agents.local_agent import LocalAgent
from agents.regional_agent import RegionalAgent
from simulation.data_generator import DataGenerator
from beckn_models import ComputeJob

def verify_reassignment():
    print("=== Starting Job Reassignment Verification ===")
    
    # 1. Setup
    generator = DataGenerator()
    regional_agent = RegionalAgent("UK-Region", "UK")
    
    # Create two local agents
    agent_a = LocalAgent("Agent-Cambridge", "UK", generator)
    agent_b = LocalAgent("Agent-Manchester", "UK", generator)
    
    # Register them
    regional_agent.register_local_agent(agent_a)
    regional_agent.register_local_agent(agent_b)
    
    # Initialize state
    now = datetime.now()
    regional_agent.update_state(now)
    
    print(f"Agent A Capacity: {agent_a.available_capacity}")
    print(f"Agent B Capacity: {agent_b.available_capacity}")
    
    # 2. Assign Job to Agent A
    job = ComputeJob(
        job_id=str(uuid.uuid4()),
        num_computations=100,
        estimated_runtime_hrs=2.0,
        priority=1,
        submitted_at=now
    )
    
    print(f"\nAssigning Job {job.job_id[:8]} to Agent A...")
    success = agent_a.assign_job(job)
    
    if not success:
        print("Failed to assign initial job. Aborting.")
        return
        
    print(f"Agent A Jobs: {len(agent_a.current_jobs)}")
    print(f"Agent B Jobs: {len(agent_b.current_jobs)}")
    
    # 3. Simulate Price Spike on Agent A
    print("\nSimulating Price Spike on Agent A...")
    # Force high price
    agent_a.energy_data['price'] = 0.50 # > 0.30 threshold
    
    # Ensure Agent B has low price
    agent_b.energy_data['price'] = 0.10
    
    # Update scores manually since we modified data directly
    agent_a.cost_score = agent_a.compute_cost_score(now)
    agent_b.cost_score = agent_b.compute_cost_score(now)
    
    print(f"Agent A Price: {agent_a.energy_data['price']}, Score: {agent_a.cost_score:.2f}")
    print(f"Agent B Price: {agent_b.energy_data['price']}, Score: {agent_b.cost_score:.2f}")
    
    # 4. Trigger Reassignment Logic
    print("\nTriggering Regional Agent Update (Spike Detection)...")
    regional_agent.handle_energy_spikes()
    
    # 5. Verify Results
    print("\n=== Verification Results ===")
    print(f"Agent A Jobs: {len(agent_a.current_jobs)}")
    print(f"Agent B Jobs: {len(agent_b.current_jobs)}")
    
    if len(agent_a.current_jobs) == 0 and len(agent_b.current_jobs) == 1:
        # Check if it's the same job ID
        job_on_b = list(agent_b.current_jobs.values())[0]
        if job_on_b.job_id == job.job_id:
            print("SUCCESS: Job successfully reassigned from Agent A to Agent B.")
        else:
            print("PARTIAL SUCCESS: Job moved, but ID mismatch (might be expected if object copied).")
    else:
        print("FAILURE: Job reassignment did not occur as expected.")

if __name__ == "__main__":
    verify_reassignment()
