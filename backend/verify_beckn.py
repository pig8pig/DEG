import sys
import os
# Add backend to path so we can import as 'agents.local_agent' etc
sys.path.append(os.path.join(os.path.dirname(__file__)))

from datetime import datetime
from agents.local_agent import LocalAgent
from agents.regional_agent import RegionalAgent
from agents.global_agent import GlobalAgent
from simulation.data_generator import DataGenerator
from beckn_models import ComputeJob

def verify_beckn_flow():
    print("Starting Beckn Protocol Verification...")
    
    # 1. Setup
    generator = DataGenerator()
    
    # Create Agents
    local_agent = LocalAgent("provider-1", "UK-South", generator)
    regional_agent = RegionalAgent("region-1", "UK-South")
    regional_agent.register_local_agent(local_agent)
    
    global_agent = GlobalAgent()
    global_agent.register_regional_agent(regional_agent)
    
    # Update state to generate catalog
    print("Updating agent states...")
    local_agent.update_state(datetime.now())
    regional_agent.update_state(datetime.now())
    
    # 2. Create Job
    job = ComputeJob(
        job_id="job-test-001",
        num_computations=100,
        estimated_runtime_hrs=1,
        priority=1
    )
    
    print(f"Adding job {job.job_id} to global queue...")
    global_agent.add_task_to_queue(job)
    
    # 3. Run Optimization (Beckn Flow)
    print("Running optimization loop...")
    global_agent.optimize_and_assign()
    
    # 4. Check Logs
    print("\nGlobal Agent Logs:")
    for log in global_agent.logs:
        print(f" - {log}")
        
    # 5. Verify Outcome
    if any("assigned to provider-1" in log for log in global_agent.logs):
        print("\nSUCCESS: Job assigned via Beckn protocol.")
    else:
        print("\nFAILURE: Job not assigned.")
        # Debug info
        print(f"Local Agent Available: {local_agent.node.is_available}")
        print(f"Catalog: {local_agent.get_beckn_catalog()}")

if __name__ == "__main__":
    verify_beckn_flow()
