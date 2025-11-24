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
    # Define location assignments for each agent (agent name -> Beckn API location)
    # All 9 UK cities available in the Beckn API
    LOCATION_ASSIGNMENTS = {
        "Cambridge": "Cambridge",
        "London": "London",
        "Manchester": "Manchester",
        "Birmingham": "Birmingham",
        "Edinburgh": "Edinburgh",
        "Bristol": "Bristol",
        "Liverpool": "Liverpool",
        "Glasgow": "Glasgow",
        "Leeds": "Leeds",
    }
    
    def __init__(self, name: str, region: str, generator: DataGenerator, lat: float = 0.0, lon: float = 0.0):
        self.name = name
        self.region = region
        self.generator = generator
        self.lat = lat
        self.lon = lon
        
        self.beckn_client = BecknClient()
        self.active_external_orders = {} # Map job_id -> external_order_id
        
        # Discovery tracking
        self.discovery_history = []  # List of discovery results with timestamps
        self.last_discovery_time = None
        self.discovery_count = 0
        self.update_tick = 0  # Track update cycles
        self.discovered_locations = []  # Store discovered UK locations from Beckn API
        
        # Assign this agent to a specific UK location
        self.assigned_location = self.LOCATION_ASSIGNMENTS.get(name, "Cambridge")
        self.location_data = None  # Will store data for assigned location only
        
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
        self.update_tick += 1
        
        # Get fresh energy data
        self.energy_data = self.generator.get_energy_data(timestamp, self.region)
        
        # Perform discovery every 5 ticks (~10 seconds in simulation)
        if self.update_tick % 5 == 0:
            self.discover_energy_slots()
        
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

    def discover_energy_slots(self) -> Dict:
        """
        Uses Beckn discover API to search for energy slots and extract UK location data.
        Filters results to show only data for this agent's assigned location.
        """
        query = "Grid flexibility windows"
        
        try:
            result = self.beckn_client.discover(query=query)
            
            # Extract locations from Beckn response
            locations = self._extract_locations_from_discovery(result)
            if locations:
                self.discovered_locations = locations
                
                # Filter to find this agent's assigned location
                assigned_loc = next(
                    (loc for loc in locations if loc["locality"] == self.assigned_location),
                    None
                )
                
                if assigned_loc:
                    self.location_data = assigned_loc
            
            # Track discovery with assigned location
            discovery_record = {
                "timestamp": datetime.now().isoformat(),
                "city": self.assigned_location,
                "query": query,
                "result": result,
                "agent_name": self.name,
                "region": self.region,
                "discovered_locations": locations,
                "assigned_location": self.assigned_location,
                "location_data": self.location_data  # Only this location's data
            }
            
            # Keep last 10 discoveries
            self.discovery_history.append(discovery_record)
            if len(self.discovery_history) > 10:
                self.discovery_history.pop(0)
            
            self.last_discovery_time = datetime.now()
            self.discovery_count += 1
            
            return result
            
        except Exception as e:
            print(f"Discovery failed for {self.name}: {e}")
            return {"error": str(e)}
    
    def _extract_locations_from_discovery(self, result: Dict) -> list:
        """
        Extract location data from Beckn discovery response.
        Returns list of location dictionaries with grid parameters.
        """
        locations = []
        
        try:
            catalogs = result.get("message", {}).get("catalogs", [])
            
            for catalog in catalogs:
                items = catalog.get("beckn:items", [])
                
                for item in items:
                    # Extract location from beckn:availableAt
                    available_at = item.get("beckn:availableAt", [])
                    if available_at and len(available_at) > 0:
                        location_data = available_at[0]
                        address = location_data.get("address", {})
                        
                        # Extract grid parameters
                        item_attrs = item.get("beckn:itemAttributes", {})
                        grid_params = item_attrs.get("beckn:gridParameters", {})
                        
                        location_info = {
                            "item_id": item.get("beckn:id", ""),
                            "name": item.get("beckn:descriptor", {}).get("schema:name", ""),
                            "locality": address.get("addressLocality", "Unknown"),
                            "region": address.get("addressRegion", "Unknown"),
                            "country": address.get("addressCountry", "GB"),
                            "grid_area": grid_params.get("gridArea", ""),
                            "grid_zone": grid_params.get("gridZone", ""),
                            "renewable_mix": grid_params.get("renewableMix", 0),
                            "carbon_intensity": grid_params.get("carbonIntensity", 0),
                            "available_capacity": item_attrs.get("beckn:capacityParameters", {}).get("availableCapacity", 0)
                        }
                        
                        locations.append(location_info)
            
            return locations
            
        except Exception as e:
            print(f"Error extracting locations: {e}")
            return []

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
            "location": {"lat": self.lat, "lon": self.lon},
            "available_capacity": 1 if self.node.is_available else 0, # Simplified
            "energy_data": self.energy_data,
            "active_tasks_count": len(self.current_jobs),
            "catalog": self.get_beckn_catalog().dict()
        }
    
    def get_discovery_data(self):
        """
        Returns discovery data for frontend display.
        Includes assigned location and location-specific data.
        """
        return {
            "agent_name": self.name,
            "region": self.region,
            "discovery_count": self.discovery_count,
            "last_discovery_time": self.last_discovery_time.isoformat() if self.last_discovery_time else None,
            "discovery_history": self.discovery_history[-5:],  # Last 5 discoveries
            "discovered_locations": self.discovered_locations,  # All UK locations
            "assigned_location": self.assigned_location,  # This agent's assigned location
            "location_data": self.location_data  # Data for assigned location only
        }
