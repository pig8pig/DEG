from datetime import datetime
from typing import Dict, Optional, Tuple
import random
import uuid

from simulation.data_generator import DataGenerator
from beckn_models import (
    ComputeNode, BecknCatalog, BecknProvider, BecknItem, 
    BecknDescriptor, BecknPrice, BecknOrder, OrderState, ComputeJob,
    BecknComputeEnergyWindow, BecknGridParameters, BecknTimeWindow,
    BecknOffer, BecknOrderItem
)
from beckn_client import BecknClient

class LocalAgent:
    def __init__(self, name: str, region: str, generator: DataGenerator):
        self.name = name
        self.region = region
        self.generator = generator
        
        self.beckn_client = BecknClient()
        self.active_external_orders = {} # Map job_id -> external_order_id
        
        # We keep 'node' for compatibility with the dashboard, but it represents the "virtual" capacity
        # we have secured from the grid.
        self.node = ComputeNode(
            node_id=str(uuid.uuid4()),
            cluster_id=f"cluster_{name}",
            region_id=region,
            max_power_kw=10.0, 
            idle_power_kw=0.5,
            compute_capacity={"cpu_cores": 64, "gpu_type": "Virtual A100", "memory_gb": 512},
            variable_cost_per_hr=2.5
        )
        
        self.current_jobs: Dict[str, ComputeJob] = {}
        self.energy_data = {}
        self.orders: Dict[str, BecknOrder] = {}

    def update_state(self, timestamp: datetime):
        """
        Updates the local agent's state: energy data, capacity, etc.
        """
        # Get fresh energy data
        self.energy_data = self.generator.get_energy_data(timestamp, self.region)
        
        # Simulate tasks finishing
        finished_job_ids = []
        for job_id, job in self.current_jobs.items():
            # Simple simulation: 10% chance to finish every tick
            if random.random() < 0.1:
                finished_job_ids.append(job_id)
        
        for job_id in finished_job_ids:
            del self.current_jobs[job_id]
            # Update order status if exists
            order = next((o for o in self.orders.values() if o.job_details and o.job_details.job_id == job_id), None)
            if order:
                order.state = OrderState.COMPLETED

        # Poll status for active orders
        for job_id, external_order_id in self.active_external_orders.items():
            # In a real app, we'd know the BPP ID from the order. 
            # For sandbox, we hardcode or store it.
            # Simplified: Just print status check
            pass

        # Update power draw (based on active jobs)
        active_power = len(self.current_jobs) * 1.5
        self.node.current_power_draw_kw = self.node.idle_power_kw + active_power
        self.node.is_available = True # Always try to buy more if needed

    def get_beckn_catalog(self) -> BecknCatalog:
        """
        Generates a Beckn Catalog based on available resources.
        """
        # Calculate dynamic price based on energy cost
        energy_price = self.energy_data.get('price', 0)
        carbon = self.energy_data.get('carbon_intensity', 0)
        
        # Price formula: Base + (Energy Price * Power Factor)
        hourly_price = self.node.variable_cost_per_hr + (energy_price * 0.01) 
        
        # Create detailed attributes
        grid_params = BecknGridParameters(
            grid_area=self.region,
            grid_zone=f"Zone-{self.region}",
            renewable_mix=self.energy_data.get('renewable_mix', 50),
            carbon_intensity=carbon
        )
        
        time_window = BecknTimeWindow(
            start=datetime.now(), # Simplified
            end=datetime.now() # Simplified
        )
        
        compute_window = BecknComputeEnergyWindow(
            slot_id=f"slot_{self.node.node_id}",
            grid_parameters=grid_params,
            time_window=time_window
        )

        item = BecknItem(
            id=f"slot_{self.node.node_id}",
            descriptor=BecknDescriptor(
                name=f"Compute Slot on {self.name}",
                short_desc=f"A100 GPU Node in {self.region}",
                long_desc=f"Carbon Intensity: {carbon} gCO2/kWh"
            ),
            price=BecknPrice(
                currency="USD",
                value=str(round(hourly_price, 2))
            ),
            item_attributes=compute_window,
            matched=True
        )
        
        provider = BecknProvider(
            id=self.name,
            descriptor=BecknDescriptor(name=self.name),
            items=[item] if self.node.is_available else []
        )
        
        return BecknCatalog(
            descriptor=BecknDescriptor(name=f"Catalog for {self.name}"),
            providers=[provider]
        )

    # --- Beckn Order Lifecycle ---

    def execute_order_lifecycle(self, item_id: str, provider_id: str, job: ComputeJob) -> bool:
        """
        Executes the full Beckn order lifecycle (Select -> Init -> Confirm) against the sandbox.
        """
        try:
            transaction_id = str(uuid.uuid4())
            bpp_id = provider_id # Assuming provider_id is the BPP ID
            bpp_uri = f"https://{provider_id}/bpp" # Placeholder URI
            
            # 1. Select
            select_res = self.beckn_client.select(transaction_id, bpp_id, bpp_uri, item_id, provider_id)
            if 'error' in select_res:
                return False
                
            # 2. Init
            # We use the order details from select response
            order_details = select_res.get('message', {}).get('order', {})
            init_res = self.beckn_client.init(transaction_id, bpp_id, bpp_uri, order_details)
            if 'error' in init_res:
                return False

            # 3. Confirm
            order_details = init_res.get('message', {}).get('order', {})
            confirm_res = self.beckn_client.confirm(transaction_id, bpp_id, bpp_uri, order_details)
            
            if 'message' in confirm_res and 'order' in confirm_res['message']:
                confirmed_order = confirm_res['message']['order']
                state = confirmed_order.get('beckn:orderStatus')
                
                if state in ["CONFIRMED", "ACCEPTED", "PENDING"]: # Sandbox might return PENDING
                    # Success
                    self.current_jobs[job.job_id] = job
                    job.status = "ASSIGNED"
                    self.active_external_orders[job.job_id] = confirmed_order.get('beckn:id')
                    return True
            
            return False
            
        except Exception as e:
            print(f"Order lifecycle failed: {e}")
            return False

    def get_report(self):
        """
        Returns a report for the regional agent.
        """
        return {
            "name": self.name,
            "region": self.region,
            "available_capacity": 1 if self.node.is_available else 0, # Simplified
            "energy_data": self.energy_data,
            "active_tasks_count": len(self.current_jobs),
            "catalog": self.get_beckn_catalog().dict()
        }
