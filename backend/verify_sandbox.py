import sys
import os
# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__)))

from agents.global_agent import GlobalAgent
from agents.regional_agent import RegionalAgent
from agents.local_agent import LocalAgent
from simulation.data_generator import DataGenerator
from beckn_models import ComputeJob
import time

def verify_sandbox_flow():
    print("Starting Beckn Sandbox Verification...")
    
    # 1. Setup Agents
    global_agent = GlobalAgent()
    data_generator = DataGenerator()
    
    # Create one region and one local agent for testing
    region = RegionalAgent("UK-South", "UK-South")
    local = LocalAgent("Local-1", "UK-South", data_generator)
    region.register_local_agent(local)
    global_agent.register_regional_agent(region)
    
    print("Agents initialized.")
    
    # 2. Add a Task
    job = ComputeJob(
        job_id="job-sandbox-test-001",
        requirements={"cpu_cores": 8, "memory_gb": 32},
        duration_hours=2,
        max_carbon_intensity=200,
        num_computations=1000,
        estimated_runtime_hrs=2.0
    )
    global_agent.add_task_to_queue(job)
    print(f"Job {job.job_id} added to queue.")
    
    # 3. Run Optimization (Trigger Beckn Flow)
    print("Running optimization loop (calling Sandbox)...")
    global_agent.optimize_and_assign()
    
    # 4. Verify Assignment
    # Check logs
    for log in global_agent.logs:
        print(f"Log: {log}")
        
    if job.status == "ASSIGNED":
        print("SUCCESS: Job assigned via Beckn Sandbox.")
    else:
        print("FAILURE: Job not assigned. Check logs and Sandbox connectivity.")

if __name__ == "__main__":
    verify_sandbox_flow()
