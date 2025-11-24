from fastapi import FastAPI, BackgroundTasks # Trigger reload
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')) # Explicitly look in parent dir

import uvicorn
import asyncio
from datetime import datetime, timedelta
import random

from agents.global_agent import GlobalAgent
from agents.regional_agent import RegionalAgent
from agents.local_agent import LocalAgent
from simulation.data_generator import DataGenerator

app = FastAPI(title="Digital Energy Grid Agent System")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# System State
global_agent = GlobalAgent()
data_generator = DataGenerator()
simulation_running = False

def setup_system():
    """
    Initializes the agent hierarchy with city-based agents.
    Uses all UK cities available in the Beckn API.
    """
    # Define all UK cities available in Beckn API and their regions
    # Define all UK cities available in Beckn API and their regions with coordinates
    cities = [
        # South UK
        ("Cambridge", "South UK", 52.2053, 0.1218),
        ("London", "South UK", 51.5074, -0.1278),
        ("Bristol", "South UK", 51.4545, -2.5879),
        ("Birmingham", "South UK", 52.4862, -1.8904),
        
        # North UK
        ("Manchester", "North UK", 53.4808, -2.2426),
        ("Liverpool", "North UK", 53.4084, -2.9916),
        ("Leeds", "North UK", 53.8008, -1.5491),
        ("Edinburgh", "North UK", 55.9533, -3.1883),
        ("Glasgow", "North UK", 55.8642, -4.2518),
    ]
    
    # Group cities by region
    regions = {}
    for city, region, lat, lon in cities:
        if region not in regions:
            regions[region] = []
        regions[region].append((city, lat, lon))
    
    # Create regional agents and local agents per city
    for region_name, region_cities in regions.items():
        regional_agent = RegionalAgent(name=f"{region_name} Regional", region=region_name)
        
        for city, lat, lon in region_cities:
            local_agent = LocalAgent(
                name=city,  # Agent name is just the city name
                region=region_name,
                generator=data_generator,
                lat=lat,
                lon=lon
            )
            regional_agent.register_local_agent(local_agent)
            
        global_agent.register_regional_agent(regional_agent)

setup_system()

def run_simulation_step(sim_time):
    """
    Synchronous simulation step to be run in a thread.
    """
    # 2. Update Agents (Energy Data, Capacity)
    for region in global_agent.regional_agents:
        region.update_state(sim_time)
        
    # 3. Generate New Tasks
    # if random.random() < 0.5: # 50% chance of new tasks
    #     new_tasks = data_generator.generate_tasks(num_tasks=random.randint(1, 5))
    #     for task in new_tasks:
    #         global_agent.add_task_to_queue(task)
            
    # 4. Global Optimization
    global_agent.optimize_and_assign()

async def simulation_loop():
    """
    Background task to run the simulation.
    """
    global simulation_running
    simulation_running = True
    sim_time = datetime.now()
    
    while simulation_running:
        # 1. Update Time
        sim_time += timedelta(minutes=15) # Fast forward
        
        # Run blocking simulation logic in a separate thread to avoid blocking API
        await asyncio.to_thread(run_simulation_step, sim_time)
        
        # Sleep for a bit to simulate real-time ticking (e.g. 1 sec = 15 mins)
        await asyncio.sleep(2)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(simulation_loop())

@app.get("/")
async def root():
    return {"message": "DEG Agent System Online"}

@app.get("/status")
async def get_status():
    return global_agent.get_system_status()

@app.post("/control/start")
async def start_sim():
    global simulation_running
    if not simulation_running:
        asyncio.create_task(simulation_loop())
    return {"status": "started"}

@app.post("/control/stop")
async def stop_sim():
    global simulation_running
    simulation_running = False
    return {"status": "stopped"}

@app.get("/discovery/status")
async def get_discovery_status():
    """
    Returns discovery data from all local agents across all regions.
    """
    discovery_data = []
    
    for region in global_agent.regional_agents:
        for local_agent in region.local_agents:
            discovery_data.append(local_agent.get_discovery_data())
    
    return {
        "total_agents": len(discovery_data),
        "agents": discovery_data
    }

@app.get("/discovery/agent/{agent_name}")
async def get_agent_discovery(agent_name: str):
    """
    Returns discovery data for a specific agent by name.
    """
    for region in global_agent.regional_agents:
        for local_agent in region.local_agents:
            if local_agent.name == agent_name:
                return local_agent.get_discovery_data()
    
    return {"error": "Agent not found"}

@app.post("/jobs")
async def submit_job(job: dict):
    """
    Submit a new compute job.
    """
    # Ensure job_id exists
    if "job_id" not in job:
        import uuid
        job["job_id"] = str(uuid.uuid4())
    
    # Set defaults if missing
    if "num_computations" not in job: job["num_computations"] = 100.0
    if "estimated_runtime_hrs" not in job: job["estimated_runtime_hrs"] = 1.0
    if "status" not in job: job["status"] = "PENDING"
    
    global_agent.add_task_to_queue(job)
    return {"status": "submitted", "job_id": job["job_id"]}

@app.get("/jobs")
async def get_jobs():
    """
    Get all jobs and their status.
    """
    return {"jobs": global_agent.get_all_jobs()}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
