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

class LocalAgent:
    def __init__(self, name: str, region: str, generator: DataGenerator):
        self.name = name
        self.region = region
        self.generator = generator
        
        # Initialize ComputeNode state
        self.node = ComputeNode(
            node_id=str(uuid.uuid4()),
            cluster_id=f"cluster_{name}",
            region_id=region,
            max_power_kw=10.0, # 10 kW node
            idle_power_kw=0.5,
            compute_capacity={"cpu_cores": 64, "gpu_type": "A100", "memory_gb": 512},
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

        # Update power draw (simplified)
        # Base idle + (active jobs * 1.5 kW)
        active_power = len(self.current_jobs) * 1.5
        self.node.current_power_draw_kw = self.node.idle_power_kw + active_power
        self.node.is_available = self.node.current_power_draw_kw < self.node.max_power_kw

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

    def handle_beckn_select(self, item_id: str) -> Optional[BecknOrder]:
        """
        Step 1: Select - Check availability and return quote (Order with Quote).
        """
        if not self.node.is_available:
            return None
            
        # Re-calculate price (should match catalog logic)
        energy_price = self.energy_data.get('price', 0)
        hourly_price = self.node.variable_cost_per_hr + (energy_price * 0.01)
        
        offer = BecknOffer(
            id=f"offer_{uuid.uuid4()}",
            descriptor=BecknDescriptor(name=f"Offer for {item_id}"),
            provider_id=self.name,
            item_ids=[item_id],
            price=BecknPrice(currency="USD", value=str(round(hourly_price, 2)))
        )
        
        order_item = BecknOrderItem(
            line_id=f"line_{uuid.uuid4()}",
            ordered_item_id=item_id,
            accepted_offer=offer
        )
        
        # Return Order in QUOTE_REQUESTED state (or similar, acting as the quote response)
        # In Beckn 'on_select', we return the order with the quote.
        return BecknOrder(
            id=f"order_{uuid.uuid4()}",
            state=OrderState.QUOTE_REQUESTED,
            seller_id=self.name,
            buyer_id="global_agent", # Placeholder
            items=[order_item]
        )

    def handle_beckn_init(self, item_id: str, job_details: ComputeJob) -> BecknOrder:
        """
        Step 2: Init - Initialize order with job details.
        """
        # In a real flow, we would validate the quote from 'select' here.
        # For now, we create a new order or update existing if we had state.
        
        # Re-create offer/item for the order (simplified)
        # Ideally we pass the 'select' result to 'init'
        
        # ... reusing select logic for offer creation ...
        energy_price = self.energy_data.get('price', 0)
        hourly_price = self.node.variable_cost_per_hr + (energy_price * 0.01)
        
        offer = BecknOffer(
            id=f"offer_{uuid.uuid4()}",
            descriptor=BecknDescriptor(name=f"Offer for {item_id}"),
            provider_id=self.name,
            item_ids=[item_id],
            price=BecknPrice(currency="USD", value=str(round(hourly_price, 2)))
        )
        
        order_item = BecknOrderItem(
            line_id=f"line_{uuid.uuid4()}",
            ordered_item_id=item_id,
            accepted_offer=offer
        )
        
        order_id = str(uuid.uuid4())
        order = BecknOrder(
            id=order_id,
            state=OrderState.INITIALIZED,
            seller_id=self.name,
            buyer_id="global_agent",
            items=[order_item],
            job_details=job_details
        )
        self.orders[order_id] = order
        return order

    def handle_beckn_confirm(self, order_id: str) -> BecknOrder:
        """
        Step 3: Confirm - Finalize agreement and schedule job.
        """
        if order_id not in self.orders:
            raise ValueError("Order not found")
            
        order = self.orders[order_id]
        
        if self.node.is_available:
            order.state = OrderState.CONFIRMED
            # Start the job
            if order.job_details:
                self.current_jobs[order.job_details.job_id] = order.job_details
                order.job_details.status = "ASSIGNED"
        else:
            order.state = OrderState.CANCELLED
            
        return order

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
