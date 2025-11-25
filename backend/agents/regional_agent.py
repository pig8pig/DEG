from typing import List, Dict, Optional, Tuple
from agents.local_agent import LocalAgent
from beckn_models import (
    BecknCatalog, BecknProvider, BecknDescriptor, ComputeJob, BecknOrder,
    BecknItem, BecknPrice, BecknComputeEnergyWindow, BecknGridParameters,
    BecknTimeWindow
)
from llm_client import LLMClient

class RegionalAgent:
    def __init__(self, name: str, region: str):
        self.name = name
        self.region = region
        self.local_agents: List[LocalAgent] = []
        self.aggregated_catalog: Optional[BecknCatalog] = None
        self.aggregated_data = {}
        self.llm_client = LLMClient()
        self.regional_ranking = None

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
        Includes synthesized summaries from each agent's LLM.
        """
        all_providers = []
        total_capacity_available = 0
        agent_summaries = []  # Collect LLM-synthesized summaries
        
        for agent in self.local_agents:
            # Get local catalog
            catalog = agent.get_beckn_catalog()
            all_providers.extend(catalog.providers)
            
            # Get report (this triggers synthesis)
            report = agent.get_report()
            
            # Collect synthesized summary from the report
            if report.get("synthesized_summary"):
                agent_summaries.append({
                    "agent_name": agent.name,
                    "location": agent.assigned_location,
                    "summary": report["synthesized_summary"]
                })
            
            # Simple stats
            if agent.node.is_available:
                total_capacity_available += 1

        # In BAP mode, we aggregate from the external discovery result
        # If no discovery result yet, we might have an empty catalog
        if not self.aggregated_catalog:
             self.aggregated_catalog = BecknCatalog(
                descriptor=BecknDescriptor(name=f"Catalog for {self.region}"),
                providers=[]
            )
        
        # Backward compatibility for frontend
        total_capacity = len(self.local_agents)
        total_used = total_capacity - total_capacity_available
        
        # Combine local and external providers
        combined_providers = all_providers + (self.aggregated_catalog.providers if self.aggregated_catalog else [])
        
        lowest_cost_options = []
        for agent in self.local_agents:
            # Get energy data and location data from each agent
            report = agent.get_report()
            energy_data = report.get('energy_data', {})
            
            # Extract energy price, carbon intensity, and cost score
            energy_price = energy_data.get('price', 0.0)
            carbon = energy_data.get('carbon_intensity', 0.0)
            cost_score = report.get('cost_score', 0.0)
            
            lowest_cost_options.append({
                "agent_name": agent.name,
                "energy_price": energy_price,  # Energy price in GBP/kWh
                "carbon": carbon,
                "cost_score": cost_score,  # Include the computed score
                "available": 1 if agent.node.is_available else 0
            })
        
        # Sort by cost_score (lower is better)
        lowest_cost_options.sort(key=lambda x: x.get('cost_score', 999))
        
        # Calculate average score across all local agents
        total_score = sum(opt.get('cost_score', 0) for opt in lowest_cost_options)
        average_score = total_score / len(lowest_cost_options) if lowest_cost_options else 0.0

        self.aggregated_data = {
            "region": self.region,
            "total_capacity_available": total_capacity_available,
            "total_capacity": total_capacity,
            "total_used": total_used,
            "lowest_cost_options": lowest_cost_options[:50],
            "local_agents": [agent.get_report() for agent in self.local_agents],
            "catalog": self.aggregated_catalog.dict(),
            "agent_summaries": agent_summaries,  # Include LLM-synthesized summaries
            "average_score": average_score  # Include average score
        }
        
        # Synthesize regional ranking
        # We only do this if we have summaries to rank
        if agent_summaries:
            ranking = self.llm_client.synthesize_regional_ranking(self.aggregated_data)
            if ranking:
                self.regional_ranking = ranking
                self.aggregated_data["regional_ranking"] = ranking

    def get_report(self):
        return self.aggregated_data

    def assign_job(self, job: ComputeJob) -> bool:
        """
        Assigns a job to the local agent with the lowest score.
        
        Args:
            job: ComputeJob object to assign
            
        Returns:
            bool: True if assignment successful, False otherwise
        """
        print(f"[{self.region}] Regional agent received job {job.job_id[:8]} (Priority {job.priority})")
        
        # Get scores from all local agents
        agent_scores = []
        excluded_agents = []
        for agent in self.local_agents:
            report = agent.get_report()
            score = report.get('cost_score', float('inf'))
            available = report.get('available_capacity', 0)
            
            # Only consider agents with available capacity
            if available > 0:
                agent_scores.append({
                    'agent': agent,
                    'score': score,
                    'available': available
                })
            else:
                excluded_agents.append(f"{agent.name} (full)")
        
        if excluded_agents:
            print(f"[{self.region}] Excluded {len(excluded_agents)} full agents: {', '.join(excluded_agents)}")
        
        if not agent_scores:
            print(f"[{self.region}] No available agents for job {job.job_id[:8]}")
            return False
        
        # Sort by score (lowest is best)
        agent_scores.sort(key=lambda x: x['score'])
        best_agent = agent_scores[0]['agent']
        
        print(
            f"[{self.region}] Assigning job {job.job_id[:8]} to {best_agent.name} "
            f"(score: {agent_scores[0]['score']:.1f}, capacity: {agent_scores[0]['available']})"
        )
        
        # Assign to local agent
        return best_agent.assign_job(job)

    # --- Beckn Protocol Routing ---

    def process_discovery_result(self, discovery_data: Dict):
        """
        Processes raw discovery data from Beckn Client and updates the internal catalog.
        """
        print(f"DEBUG: Discovery Data: {discovery_data}")
        
        providers = []
        if 'message' in discovery_data and 'catalog' in discovery_data['message']:
            catalog = discovery_data['message']['catalog']
            raw_providers = catalog.get('beckn:providers', [])
            
            for raw_provider in raw_providers:
                # Map Provider
                provider_id = raw_provider.get('beckn:id', 'unknown')
                provider_desc = raw_provider.get('beckn:descriptor', {})
                
                items = []
                for raw_item in raw_provider.get('beckn:items', []):
                    # Map Item
                    item_id = raw_item.get('beckn:id', 'unknown')
                    item_desc = raw_item.get('beckn:descriptor', {})
                    price_info = raw_item.get('beckn:price', {})
                    
                    # Extract Carbon
                    carbon = 0
                    attrs = raw_item.get('beckn:itemAttributes', {})
                    grid_params = attrs.get('beckn:gridParameters', {})
                    carbon = grid_params.get('carbonIntensity', 0)
                    
                    # Create BecknItem
                    # Note: We are using our internal models which might expect slightly different structure
                    # so we map carefully.
                    
                    # Create Item Attributes
                    # We need to populate BecknComputeEnergyWindow structure if possible
                    # For now, we just ensure we can extract carbon in aggregate_data
                    
                    # Construct Item
                    item = BecknItem(
                        id=item_id,
                        descriptor=BecknDescriptor(name=item_desc.get('name', 'Unknown Item')),
                        price=BecknPrice(currency=price_info.get('currency', 'USD'), value=str(price_info.get('value', '0'))),
                        category_id="compute",
                        matched=True,
                        item_attributes=BecknComputeEnergyWindow(
                            slot_id=f"slot-{item_id}",
                            time_window=BecknTimeWindow(
                                start="2025-11-24T12:00:00Z",
                                end="2025-11-24T16:00:00Z"
                            ),
                            grid_parameters=BecknGridParameters(
                                carbon_intensity=carbon,
                                grid_area="UK-South", # Placeholder
                                grid_zone="UK-South-1", # Placeholder
                                renewable_mix=50 # Placeholder
                            )
                        )
                    )
                    items.append(item)
                
                if items:
                    provider = BecknProvider(
                        id=provider_id,
                        descriptor=BecknDescriptor(name=provider_desc.get('name', 'Unknown Provider')),
                        items=items
                    )
                    providers.append(provider)
        
        # Update aggregated catalog
        self.aggregated_catalog = BecknCatalog(
            descriptor=BecknDescriptor(name=f"Catalog for {self.region}"),
            providers=providers
        )

    def get_beckn_catalog(self) -> BecknCatalog:
        """
        Returns the aggregated catalog.
        """
        return self.aggregated_catalog

    def execute_order_lifecycle(self, provider_id: str, item_id: str, job: ComputeJob) -> bool:
        """
        Routes the order execution to the correct local agent based on provider_id.
        The provider_id should match the local agent's name.
        """
        if not self.local_agents:
            return False
            
        # Find the specific local agent that matches the provider_id
        agent = next((a for a in self.local_agents if a.name == provider_id), None)
        
        if not agent:
            print(f"Warning: No local agent found with name '{provider_id}' in region {self.region}")
            return False
            
        return agent.execute_order_lifecycle(item_id, provider_id, job)

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
