from typing import List, Dict, Optional
from agents.regional_agent import RegionalAgent
from typing import List, Dict, Optional
from agents.regional_agent import RegionalAgent
from beckn_models import ComputeJob, BecknCatalog, BecknItem, OrderState, BecknOrder

class GlobalAgent:
    def __init__(self):
        self.regional_agents: List[RegionalAgent] = []
        self.task_queue: List[ComputeJob] = []
        self.logs = []

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
            
            for region in self.regional_agents:
                catalog = region.handle_beckn_search()
                if catalog:
                    for provider in catalog.providers:
                        for item in provider.items:
                            if item.matched:
                                all_items.append((item, region, provider.id))
            
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
                
                # 3. Order Lifecycle
                # 3. Order Lifecycle
                try:
                    # Select (Get Quote)
                    quote_order = region.handle_beckn_select(provider_id, item.id)
                    if quote_order and quote_order.state == OrderState.QUOTE_REQUESTED:
                        # Init
                        # In real Beckn, we'd pass the quote details.
                        init_order = region.handle_beckn_init(provider_id, item.id, job)
                        if init_order:
                            # Confirm
                            confirmed_order = region.handle_beckn_confirm(provider_id, init_order.id)
                            if confirmed_order and confirmed_order.state == OrderState.CONFIRMED:
                                self.log_event(f"Job {job.job_id} assigned to {provider_id} in {region.region} via Beckn.")
                                assigned = True
                            else:
                                self.log_event(f"Job {job.job_id} confirmation failed.")
                        else:
                            self.log_event(f"Job {job.job_id} init failed.")
                    else:
                        self.log_event(f"Job {job.job_id} select failed (Quote not received).")
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
