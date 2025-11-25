from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import random
import uuid

from simulation.data_generator import DataGenerator
import math
from beckn_models import (
    ComputeNode, BecknCatalog, BecknProvider, BecknItem, 
    BecknDescriptor, BecknPrice, BecknOrder, OrderState, ComputeJob,
    BecknComputeEnergyWindow, BecknGridParameters, BecknTimeWindow,
    BecknOffer, BecknOrderItem
)
from beckn_client import BecknClient
from llm_client import LLMClient

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

    # Hard‑coded workload forecast (hour -> weight) – values from user request
    WORKLOAD_FORECAST = {
        0: 0.15,
        1: 0.10,
        2: 0.08,
        3: 0.05,
        4: 0.05,
        5: 0.07,
        6: 0.14,
        7: 0.28,
        8: 0.45,
        9: 0.65,
        10: 0.80,
        11: 0.90,
        12: 0.70,
        13: 0.88,
        14: 0.98,
        15: 1.00,
        16: 0.92,
        17: 0.75,
        18: 0.50,
        19: 0.40,
        20: 0.30,
        21: 0.25,
        22: 0.20,
        23: 0.18,
    }

    
    def __init__(self, name: str, region: str, generator: DataGenerator, lat: float = 0.0, lon: float = 0.0):
        self.name = name
        self.region = region
        self.generator = generator
        self.lat = lat
        self.lon = lon
        
        self.beckn_client = BecknClient()
        self.llm_client = LLMClient()  # Each agent gets its own LLM instance
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
        self.job_schedule: Dict[str, Dict] = {}  # Track job start times and durations
        self.energy_data = {}
        self.orders: Dict[str, BecknOrder] = {}
        self.synthesized_summary = None  # Store latest LLM-synthesized summary
        
        # Capacity tracking - will be set from location_data
        self.total_capacity = 0  # Will be set from location_data.available_capacity
        self.available_capacity = 0  # Dynamic: decreases with active jobs

    def update_state(self, timestamp: datetime):
        """
        Updates the local agent's state: energy data, capacity, etc.
        """
        self.update_tick += 1
        
        # Get fresh energy data from DataGenerator (fallback/default)
        self.energy_data = self.generator.get_energy_data(timestamp, self.region)
        
        # Perform discovery on first tick and then every 5 ticks (~10 seconds in simulation)
        if self.update_tick == 1 or self.update_tick % 5 == 0:
            self.discover_energy_slots()
        
        # Use location_data prices if available (from Beckn API or estimation)
        # This ensures consistency with the Discovery page
        if self.location_data and 'price' in self.location_data:
            self.energy_data = {
                'price': self.location_data.get('price', 0),
                'carbon_intensity': self.location_data.get('carbon_intensity', 0),
                'renewable_mix': self.location_data.get('renewable_mix', 0),
                'timestamp': timestamp.isoformat()
            }
            
            # Set total_capacity from location_data (constant)
            # Convert MW to compute slots (1 MW = 1 compute slot)
            if self.total_capacity == 0:  # Only set once
                grid_capacity_mw = self.location_data.get('available_capacity', 100)
                self.total_capacity = int(grid_capacity_mw)  # Convert MW to slots
                self.available_capacity = self.total_capacity
        
        # Update available capacity based on active jobs
        if self.total_capacity > 0:
            self.available_capacity = self.total_capacity - len(self.current_jobs)
        
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

        # Compute and store cost score for this timestamp
        self.cost_score = self.compute_cost_score(timestamp)


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
                    
                    # Try to get price from Beckn offers
                    beckn_price = self._extract_price_from_offers(result, assigned_loc.get("item_id"))
                    
                    # If no Beckn price, estimate using DataGenerator
                    if beckn_price is not None:
                        self.location_data["price"] = beckn_price
                        self.location_data["price_source"] = "beckn_api"
                    else:
                        # Estimate price using DataGenerator
                        estimated_price = self.generator.estimate_price(
                            timestamp=datetime.now(),
                            location=self.assigned_location,
                            carbon_intensity=assigned_loc.get("carbon_intensity"),
                            renewable_mix=assigned_loc.get("renewable_mix")
                        )
                        self.location_data["price"] = estimated_price
                        self.location_data["price_source"] = "estimated"
            
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
    
    def _extract_price_from_offers(self, result: Dict, item_id: str) -> Optional[float]:
        """
        Extract price from Beckn offers for a specific item ID.
        
        Args:
            result: Beckn discovery result
            item_id: Item ID to find price for
            
        Returns:
            Price in GBP/kWh or None if not found
        """
        try:
            catalogs = result.get("message", {}).get("catalogs", [])
            
            for catalog in catalogs:
                offers = catalog.get("beckn:offers", [])
                
                for offer in offers:
                    offer_items = offer.get("beckn:items", [])
                    if item_id in offer_items:
                        price_obj = offer.get("beckn:price", {})
                        if price_obj and "value" in price_obj:
                            return float(price_obj["value"])
            
            return None
            
        except Exception as e:
            print(f"Error extracting price from offers: {e}")
            return None

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

    def assign_job(self, job: ComputeJob) -> bool:
        """
        Assigns a job to this local agent and executes Beckn lifecycle.
        
        Args:
            job: ComputeJob object to assign
            
        Returns:
            bool: True if assignment successful, False otherwise
        """
        print(f"[{self.name}] Local agent received job {job.job_id[:8]} (Priority {job.priority})")
        
        # Check capacity
        if self.available_capacity <= 0:
            print(f"[{self.name}] No capacity available for job {job.job_id[:8]}")
            return False
        
        # Execute Beckn lifecycle
        item_id = f"slot_{self.node.node_id}"
        provider_id = self.name
        
        success = self.execute_order_lifecycle(item_id, provider_id, job)
        
        if not success:
            print(f"[{self.name}] Beckn lifecycle failed for job {job.job_id[:8]}")
            return False
        
        # Add to current jobs
        self.current_jobs[job.job_id] = job
        
        # Update capacity
        self.available_capacity = self.total_capacity - len(self.current_jobs)
        
        # Create job schedule entry
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=job.estimated_runtime_hrs)
        
        self.job_schedule[job.job_id] = {
            "job_id": job.job_id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_hrs": job.estimated_runtime_hrs,
            "priority": job.priority,
            "status": "RUNNING",
            "submitted_at": job.submitted_at.isoformat() if job.submitted_at else None,
            "must_start_by": job.must_start_by.isoformat() if job.must_start_by else None
        }
        
        # Update job status
        job.status = "RUNNING"
        
        print(
            f"[{self.name}] Job {job.job_id[:8]} is now RUNNING "
            f"(capacity: {self.available_capacity}/{self.total_capacity})"
        )
        
        return True

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
                
            # 2. Init - Pass job for Compute-Energy enrichment
            order_details = select_res.get('message', {}).get('order', {})
            init_res = self.beckn_client.init(transaction_id, bpp_id, bpp_uri, order_details, job=job)
            
            # Enrich location data with actual agent coordinates
            if 'message' in init_res and 'order' in init_res['message']:
                order = init_res['message']['order']
                if 'beckn:fulfillment' in order:
                    fulfillment = order['beckn:fulfillment']
                    if 'beckn:deliveryAttributes' in fulfillment:
                        delivery = fulfillment['beckn:deliveryAttributes']
                        if 'beckn:location' in delivery:
                            # Update with actual agent location
                            delivery['beckn:location']['geo']['coordinates'] = [self.lon, self.lat]
                            delivery['beckn:location']['address']['addressLocality'] = self.assigned_location
                            delivery['beckn:location']['address']['addressRegion'] = self.region
            
            if 'error' in init_res:
                return False

            # 3. Confirm
            order_details = init_res.get('message', {}).get('order', {})
            confirm_res = self.beckn_client.confirm(transaction_id, bpp_id, bpp_uri, order_details)
            
            if 'message' in confirm_res and 'order' in confirm_res['message']:
                confirmed_order = confirm_res['message']['order']
                state = confirmed_order.get('beckn:orderStatus')
                
                if state in ["CONFIRMED", "ACCEPTED", "PENDING"]: # Sandbox might return PENDING
                    # Success - record job assignment
                    self.current_jobs[job.job_id] = job
                    job.status = "ASSIGNED"
                    self.active_external_orders[job.job_id] = confirmed_order.get('beckn:id')
                    
                    # Record job schedule for timeline visualization
                    # Use actual current time as start time (job starts now when assigned)
                    start_time = datetime.now()
                    end_time = start_time + timedelta(hours=job.estimated_runtime_hrs)
                    
                    self.job_schedule[job.job_id] = {
                        "job_id": job.job_id,
                        "start_time": start_time.isoformat(),
                        "duration_hrs": job.estimated_runtime_hrs,
                        "end_time": end_time.isoformat(),
                        "priority": job.priority,
                        "status": "SCHEDULED",
                        "submitted_at": job.submitted_at.isoformat() if job.submitted_at else None,
                        "must_start_by": job.must_start_by.isoformat() if job.must_start_by else None
                    }
                    
                    return True
            
            return False
            
        except Exception as e:
            print(f"Order lifecycle failed: {e}")
            return False

    def synthesize_report(self) -> Optional[str]:
        """
        Uses the LLM to synthesize agent data into a natural language summary.
        This summary is ready for the regional agent to consume.
        """
        agent_data = {
            "name": self.name,
            "region": self.region,
            "location_data": self.location_data or {},
            "energy_data": self.energy_data,
            "active_tasks_count": len(self.current_jobs),
            "available_capacity": 1 if self.node.is_available else 0
        }
        
        summary = self.llm_client.synthesize_agent_report(agent_data)
        if summary:
            self.synthesized_summary = summary
        return summary
    
    def get_report(self):
        """
        Returns a report for the regional agent.
        Includes both raw data and LLM-synthesized summary.
        """
        # Generate fresh synthesis
        synthesis = self.synthesize_report()
        
        return {
            "name": self.name,
            "region": self.region,
            "location": {"lat": self.lat, "lon": self.lon},
            "available_capacity": 1 if self.node.is_available else 0, # Simplified
            "energy_data": self.energy_data,
            "active_tasks_count": len(self.current_jobs),
            "catalog": self.get_beckn_catalog().dict(),
            "synthesized_summary": synthesis,  # LLM-generated summary
            "location_data": self.location_data,  # Include location data for context
            "cost_score": getattr(self, 'cost_score', None),  # Expose computed cost score
        }

    
    def get_discovery_data(self):
        """
        Returns discovery data for frontend display.
        Includes assigned location and location-specific data.
        """
        # Create lightweight version of discovery history without full Beckn responses
        lightweight_history = []
        for record in self.discovery_history[-5:]:  # Last 5 discoveries
            lightweight_history.append({
                "timestamp": record["timestamp"],
                "city": record["city"],
                "query": record["query"],
                "agent_name": record["agent_name"],
                "region": record["region"],
                "assigned_location": record["assigned_location"],
                "location_data": record["location_data"],
                "cost_score": getattr(self, 'cost_score', None)  # Include current cost score
                # Exclude 'result' and 'discovered_locations' to reduce payload size
            })
        
        return {
            "agent_name": self.name,
            "region": self.region,
            "discovery_count": self.discovery_count,
            "last_discovery_time": self.last_discovery_time.isoformat() if self.last_discovery_time else None,
            "discovery_history": lightweight_history,
            "assigned_location": self.assigned_location,  # This agent's assigned location
            "location_data": self.location_data,  # Data for assigned location only
            "job_schedule": list(self.job_schedule.values()),  # Scheduled jobs for timeline
            "cost_score": getattr(self, 'cost_score', None),  # Expose computed cost score
            "available_capacity": self.available_capacity,  # Current available capacity
            "total_capacity": self.total_capacity  # Total capacity from location data
        }

    def compute_cost_score(self, timestamp: datetime) -> float:
        """Calculate the cost score for this agent.

        f = a*energy_price + b*carbon + c*workload_forecast
        a = 10, b = 0.01, c = 2 (as per user request)
        The raw f is passed through a sigmoid to bound it between 0 and 1.
        The final score is sigmoid(f) * 100 to normalize from 0 - 100.
        """
        # Coefficients
        a = 5.0
        b = 0.005
        c = 2.0
        d = 1.0
        
        # Pull values
        energy_price = self.energy_data.get('price', 0.0)
        carbon = self.energy_data.get('carbon_intensity', 0.0)
        hour = timestamp.hour
        workload = self.WORKLOAD_FORECAST.get(hour, 0.0)
        
        # Linear combination
        raw_f = a * energy_price + b * carbon + c * workload - 2
        
        # Sigmoid normalization
        sigmoid = 1.0 / (1.0 + math.exp(-1.5*raw_f))
        
        # Normalize to 0-100
        return sigmoid * 100.0

    def check_for_price_spike(self) -> bool:
        """
        Checks if the current energy price exceeds a threshold.
        Threshold: Price > 0.30 GBP/kWh (approx 3x normal)
        """
        current_price = self.energy_data.get('price', 0.0)
        # Threshold could be dynamic, but fixed for now as per plan
        PRICE_THRESHOLD = 0.30 
        
        if current_price > PRICE_THRESHOLD:
            print(f"[{self.name}] PRICE SPIKE DETECTED: {current_price:.3f} > {PRICE_THRESHOLD}")
            return True
        return False

    def trigger_workload_shift(self, job_id: str, target_agent_name: str) -> bool:
        """
        Sends a Beckn Update request to signal a workload shift.
        """
        if job_id not in self.active_external_orders:
            return False
            
        external_order_id = self.active_external_orders[job_id]
        transaction_id = str(uuid.uuid4())
        
        # Construct flexibility action payload
        update_details = {
            "beckn:flexibilityAction": {
                "actionType": "workload_shift",
                "actionReason": "grid_stress_response",
                "actionTimestamp": datetime.now().isoformat(),
                "shiftDetails": {
                    "sourceLocation": self.assigned_location,
                    "targetLocation": target_agent_name, # Simplified: using agent name as location proxy
                    "estimatedShiftTime": "PT5M"
                }
            }
        }
        
        # Call Beckn Update
        # In a real scenario, we'd use the stored BPP URI. Here we assume a standard one or use the client's default.
        bpp_id = self.name # Self is the provider
        bpp_uri = f"https://{self.name}/bpp"
        
        print(f"[{self.name}] Sending Beckn Update (Workload Shift) for Order {external_order_id}")
        response = self.beckn_client.update(
            transaction_id=transaction_id,
            bpp_id=bpp_id,
            bpp_uri=bpp_uri,
            order_id=external_order_id,
            update_type="flexibility_response",
            update_details=update_details
        )
        
        if 'error' not in response:
            return True
        return False
