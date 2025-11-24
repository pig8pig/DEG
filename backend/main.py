from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
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
    Initializes the agent hierarchy.
    """
    # UK Regions and their major cities with approx lat/lon
    uk_regions = {
        "London": [
            ("London Central", 51.5074, -0.1278),
            ("London West", 51.5074, -0.2278),
            ("London East", 51.5074, -0.0278)
        ],
        "North": [
            ("Manchester", 53.4808, -2.2426),
            ("Leeds", 53.8008, -1.5491),
            ("Liverpool", 53.4084, -2.9916)
        ],
        "Scotland": [
            ("Edinburgh", 55.9533, -3.1883),
            ("Glasgow", 55.8642, -4.2518),
            ("Aberdeen", 57.1497, -2.0943)
        ],
        "South West": [
            ("Bristol", 51.4545, -2.5879),
            ("Cardiff", 51.4816, -3.1791),
            ("Exeter", 50.7184, -3.5339)
        ]
    }
    
    for region_name, cities in uk_regions.items():
        regional_agent = RegionalAgent(name=f"{region_name} Regional", region=region_name)
        
        for city_name, lat, lon in cities:
            local_agent = LocalAgent(
                name=f"{city_name} Node",
                region=region_name,
                generator=data_generator,
                lat=lat,
                lon=lon
            )
            regional_agent.register_local_agent(local_agent)
            
        global_agent.register_regional_agent(regional_agent)

setup_system()

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
        
        # 2. Update Agents (Energy Data, Capacity)
        for region in global_agent.regional_agents:
            region.update_state(sim_time)
            
        # 3. Generate New Tasks
        if random.random() < 0.5: # 50% chance of new tasks
            new_tasks = data_generator.generate_tasks(num_tasks=random.randint(1, 5))
            for task in new_tasks:
                global_agent.add_task_to_queue(task)
                
        # 4. Global Optimization
        global_agent.optimize_and_assign()
        
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

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
