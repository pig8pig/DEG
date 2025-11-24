from typing import List, Dict, Optional
from agents.regional_agent import RegionalAgent
from typing import List, Dict, Optional
from agents.regional_agent import RegionalAgent
from beckn_models import ComputeJob, BecknCatalog, BecknItem, OrderState, BecknOrder
from beckn_client import BecknClient

class GlobalAgent:
    def __init__(self):
        self.regional_agents: List[RegionalAgent] = []
        self.task_queue: List[ComputeJob] = []
        self.logs = []
        self.beckn_client = BecknClient()

    def register_regional_agent(self, agent: RegionalAgent):
        self.regional_agents.append(agent)

    def add_task_to_queue(self, task: Dict):
        # Convert dict to ComputeJob if needed
        if isinstance(task, dict):
            job = ComputeJob(**task)
        else:
            job = task
            
        self.task_queue.append(job)
        self.log_event(f"Job {job.job_id} added to global queue.")

    def log_event(self, message):
        self.logs.append(f"{message}")

    def optimize_and_assign(self):
        """
        Main optimization loop. Assigns tasks from queue to regions using Beckn Protocol.
        """
        if not self.task_queue:
            return

        jobs_to_requeue = []

        while self.task_queue:
            job = self.task_queue.pop(0)
            assigned = False
            
            # 1. Search (Broadcast to all regions)
            all_items: List[tuple[BecknItem, RegionalAgent, str]] = [] # (Item, Region, ProviderID)
            
            # Use Beckn Client to discover
            try:
                discovery_result = self.beckn_client.discover()
                # Parse discovery result into BecknCatalog
                # Note: Sandbox returns raw JSON, we need to map it if we want to use our models
                # For now, let's assume we can extract items directly or pass raw data
                
                # Simplified: We'll let the Regional Agents process the raw discovery data
                # In a real BAP, the Global Agent might route based on location.
                # Here, we'll give the same discovery result to all regions to filter.
                
                for region in self.regional_agents:
                    # Pass raw discovery data to region to process/filter
                    region.process_discovery_result(discovery_result)
                    
                    # Then get the catalog as before (now populated from external data)
                    catalog = region.get_beckn_catalog()
                    if catalog:
                        for provider in catalog.providers:
                            for item in provider.items:
                                # We assume matched=True for now
                                all_items.append((item, region, provider.id))
                                
            except Exception as e:
                self.log_event(f"Discovery failed: {e}")
            
            # 2. Selection Logic (Find best slot)
            best_match = None
            best_score = float('inf')
            
            for item, region, provider_id in all_items:
                # Parse price
                try:
                    price = float(item.price.value)
                except:
                    price = float('inf')
                    
                # Parse carbon from item attributes
                carbon = 0.0
                if item.item_attributes and item.item_attributes.grid_parameters:
                    carbon = item.item_attributes.grid_parameters.carbon_intensity
                
                # Score = Price + (Carbon * 0.5)
                score = price + (carbon * 0.5)
                
                if score < best_score:
                    best_score = score
                    best_match = (item, region, provider_id)
            
            if best_match:
                item, region, provider_id = best_match
                
                # 3. Order Lifecycle (Delegated to Region/Local Agent)
                try:
                    success = region.execute_order_lifecycle(provider_id, item.id, job)
                    if success:
                        self.log_event(f"Job {job.job_id} assigned to {provider_id} in {region.region} via Beckn Sandbox.")
                        assigned = True
                    else:
                        self.log_event(f"Job {job.job_id} failed during Beckn lifecycle.")
                except Exception as e:
                    self.log_event(f"Error during Beckn flow for {job.job_id}: {e}")
            
            if not assigned:
                # Defer task
                jobs_to_requeue.append(job)
                self.log_event(f"Job {job.job_id} deferred (No suitable slot found).")

        self.task_queue.extend(jobs_to_requeue)

    def get_system_status(self):
        """
        Returns the global view of the system.
        """
        status = {
            "queue_length": len(self.task_queue),
            "regions": [r.get_report() for r in self.regional_agents],
            "logs": self.logs[-20:] # Last 20 logs
        }
        return status
