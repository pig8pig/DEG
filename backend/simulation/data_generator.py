import random
import math
from datetime import datetime, timedelta

class DataGenerator:
    def __init__(self):
        self.base_price = 100.0  # Base energy price
        self.base_carbon = 200.0  # Base carbon intensity (gCO2/kWh)

    def get_energy_data(self, timestamp: datetime, region: str):
        """
        Generates synthetic energy price and carbon intensity based on time of day and region.
        """
        hour = timestamp.hour
        
        # Simple daily cycle simulation
        # Peak hours: 9am - 8pm
        is_peak = 9 <= hour <= 20
        
        # Random fluctuation
        price_noise = random.uniform(-10, 10)
        carbon_noise = random.uniform(-20, 20)
        
        # Regional modifiers (simplified)
        region_modifier = 1.0
        if "EU" in region:
            region_modifier = 1.2
        elif "NA" in region:
            region_modifier = 1.0
        elif "MENA" in region:
            region_modifier = 0.8
            
        # Calculate Price
        price_multiplier = 1.5 if is_peak else 0.8
        price = (self.base_price * price_multiplier * region_modifier) + price_noise
        
        # Calculate Carbon
        # Assume solar dips carbon during day, wind random, etc. 
        # Simplified: Lower carbon during day (solar) if sunny region, else higher during peak
        carbon_multiplier = 1.2 if is_peak else 0.9
        if "MENA" in region or "WEST" in region: # Sunny
             if 10 <= hour <= 16:
                 carbon_multiplier = 0.6 # Solar impact
        
        carbon = (self.base_carbon * carbon_multiplier * region_modifier) + carbon_noise
        
        return {
            "price": round(max(0, price), 2),
            "carbon_intensity": round(max(0, carbon), 2),
            "timestamp": timestamp.isoformat()
        }

    def generate_tasks(self, num_tasks=5):
        """
        Generates a list of random compute tasks compatible with ComputeJob model.
        """
        tasks = []
        for _ in range(num_tasks):
            task_type = random.choice(["training", "inference", "data_processing"])
            duration = random.randint(1, 24) # hours
            # Simplified FLOPs estimation
            flops = duration * 1000 * 1000 * 1000 * 10 # Arbitrary number
            
            tasks.append({
                "job_id": f"job_{random.randint(1000, 9999)}",
                "num_computations": flops,
                "estimated_runtime_hrs": duration,
                "gpu_cluster_preference": [random.choice(["A100", "H100", "V100"])] if random.random() > 0.7 else None,
                "priority": random.randint(1, 3),
                "status": "PENDING"
            })
        return tasks
