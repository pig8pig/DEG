from typing import List, Dict, Optional, Tuple
from agents.local_agent import LocalAgent
from beckn_models import BecknCatalog, BecknProvider, BecknDescriptor, ComputeJob, BecknOrder

class RegionalAgent:
    def __init__(self, name: str, region: str):
        self.name = name
        self.region = region
        self.local_agents: List[LocalAgent] = []
        self.aggregated_catalog: Optional[BecknCatalog] = None
        self.aggregated_data = {}

    def register_local_agent(self, agent: LocalAgent):
        """
        Registers a local agent to this region.
        """
        self.local_agents.append(agent)

    def update_state(self, timestamp):
        """
        Updates state of all local agents and aggregates data.
        """
        for agent in self.local_agents:
            agent.update_state(timestamp)
        
        self.aggregate_data()

    def aggregate_data(self):
        """
        Aggregates reports and catalogs from local agents.
        """
        all_providers = []
        total_capacity_available = 0
        
        for agent in self.local_agents:
            # Get local catalog
            catalog = agent.get_beckn_catalog()
            all_providers.extend(catalog.providers)
            
            # Simple stats
            if agent.node.is_available:
                total_capacity_available += 1

        self.aggregated_catalog = BecknCatalog(
            descriptor=BecknDescriptor(name=f"Catalog for {self.region}"),
            providers=all_providers
        )
        
        # Backward compatibility for frontend
        total_capacity = len(self.local_agents)
        total_used = total_capacity - total_capacity_available
        
        lowest_cost_options = []
        for provider in self.aggregated_catalog.providers:
            for item in provider.items:
                # Extract price and carbon
                try:
                    cost = float(item.price.value)
                except:
                    cost = 0.0
                
                carbon = 0.0
                if item.item_attributes and item.item_attributes.grid_parameters:
                    carbon = item.item_attributes.grid_parameters.carbon_intensity
                
                lowest_cost_options.append({
                    "agent_name": provider.id,
                    "cost": cost,
                    "carbon": carbon,
                    "available": 1 # Simplified
                })
        
        # Sort by cost
        lowest_cost_options.sort(key=lambda x: x['cost'])

        self.aggregated_data = {
            "region": self.region,
            "total_capacity_available": total_capacity_available,
            "total_capacity": total_capacity,
            "total_used": total_used,
            "lowest_cost_options": lowest_cost_options[:50],
            "catalog": self.aggregated_catalog.dict()
        }

    def get_report(self):
        return self.aggregated_data

    # --- Beckn Protocol Routing ---

    def handle_beckn_search(self) -> BecknCatalog:
        """
        Returns the aggregated catalog.
        """
        return self.aggregated_catalog

    def handle_beckn_select(self, provider_id: str, item_id: str) -> Optional[BecknOrder]:
        """
        Routes Select to the appropriate local agent.
        """
        agent = next((a for a in self.local_agents if a.name == provider_id), None)
        if agent:
            return agent.handle_beckn_select(item_id)
        return None

    def handle_beckn_init(self, provider_id: str, item_id: str, job_details: ComputeJob) -> Optional[BecknOrder]:
        """
        Routes Init to the appropriate local agent.
        """
        agent = next((a for a in self.local_agents if a.name == provider_id), None)
        if agent:
            return agent.handle_beckn_init(item_id, job_details)
        return None

    def handle_beckn_confirm(self, provider_id: str, order_id: str) -> Optional[BecknOrder]:
        """
        Routes Confirm to the appropriate local agent.
        """
        agent = next((a for a in self.local_agents if a.name == provider_id), None)
        if agent:
            return agent.handle_beckn_confirm(order_id)
        return None
