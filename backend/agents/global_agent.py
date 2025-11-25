from typing import List, Dict, Optional
from agents.regional_agent import RegionalAgent
from typing import List, Dict, Optional
from agents.regional_agent import RegionalAgent
from beckn_models import ComputeJob, BecknCatalog, BecknItem, OrderState, BecknOrder
from beckn_client import BecknClient
from llm_client import LLMClient

class GlobalAgent:
    def __init__(self):
        self.regional_agents: List[RegionalAgent] = []
        self.task_queue: List[ComputeJob] = []
        self.all_jobs: Dict[str, ComputeJob] = {} # Track all jobs centrally
        self.logs = []
        self.beckn_client = BecknClient()
        self.llm_client = LLMClient()
        self.job_history = [] # Track recent assignments for LLM context
        self.cached_discovery_result = None
        self.last_discovery_time = None

    def register_regional_agent(self, agent: RegionalAgent):
        self.regional_agents.append(agent)

    def add_task_to_queue(self, task: Dict):
        # Convert dict to ComputeJob if needed
        if isinstance(task, dict):
            job = ComputeJob(**task)
        else:
            job = task
            
        self.task_queue.append(job)
        self.all_jobs[job.job_id] = job
        self.log_event(f"Job {job.job_id} added to global queue.")

    def log_event(self, message):
        from datetime import datetime
        self.logs.append({
            "message": message,
            "timestamp": datetime.now().isoformat()
        })

    def optimize_and_assign(self):
        """
        Main optimization loop. Assigns tasks from queue to regions using full Beckn Protocol lifecycle:
        1. Discover - Find available grid windows (time slots)
        2. Select - Choose specific time slot and get quote
        3. Init - Initialize order with workload details
        4. Confirm - Finalize reservation for that time slot
        """
        if not self.task_queue:
            print("DEBUG: Task queue empty, skipping optimization.")
            return

        jobs_to_requeue = []

        # STEP 1: DISCOVER - Find available grid windows across all locations
        # Check cache first to avoid spamming discovery (valid for 60 seconds)
        from datetime import datetime, timedelta
        now = datetime.now()
        
        print(f"DEBUG: Starting optimization with {len(self.task_queue)} jobs in queue.")
        
        if (self.cached_discovery_result and self.last_discovery_time and 
            (now - self.last_discovery_time).total_seconds() < 60):
            discovery_result = self.cached_discovery_result
            self.log_event("Using cached discovery results.")
        else:
            self.log_event("Starting Beckn discovery for available grid windows...")
            try:
                discovery_result = self.beckn_client.discover()
                self.cached_discovery_result = discovery_result
                self.last_discovery_time = now
                
                # Distribute discovery results to all regions
                for region in self.regional_agents:
                    # Pass raw discovery data to region to process/filter
                    region.process_discovery_result(discovery_result)
                    # Trigger aggregation to update reports with new catalog data
                    region.aggregate_data()
                
                self.log_event(f"Discovery complete. Found grid windows across {len(self.regional_agents)} regions.")
                            
            except Exception as e:
                self.log_event(f"Discovery failed: {e}")
                # If discovery fails, we can't proceed with job assignment
                return

        # Process each job in queue - SORT BY PRIORITY AND DEADLINE
        # Higher priority (5 > 1) and sooner deadlines first
        self.task_queue.sort(key=lambda j: (
            -j.priority,  # Negative for descending (higher priority first)
            j.must_start_by if j.must_start_by else datetime.max  # Earlier deadlines first
        ))

        while self.task_queue:
            job = self.task_queue.pop(0)
            assigned = False
            
            # Check if deadline has passed
            now = datetime.now()
            if job.must_start_by and now > job.must_start_by:
                self.log_event(
                    f"⚠ Job {job.job_id[:8]} (Priority {job.priority}) MISSED DEADLINE - "
                    f"was due {job.must_start_by.strftime('%H:%M:%S')}, now {now.strftime('%H:%M:%S')}"
                )
                job.status = "FAILED"
                continue
            
            # Calculate time remaining until deadline
            time_remaining_str = ""
            if job.must_start_by:
                time_remaining = (job.must_start_by - now).total_seconds() / 3600  # hours
                time_remaining_str = f", {time_remaining:.1f}h until deadline"
            
            self.log_event(
                f"Processing job {job.job_id[:8]} (Priority {job.priority}{time_remaining_str}, runtime: {job.estimated_runtime_hrs}h)"
            )
            
            # STEP 2: EVALUATE OPTIONS - Review discovered grid windows
            # Collect available time slots from all regional reports
            global_options = []
            
            for region in self.regional_agents:
                report = region.get_report()
                # Get the pre-calculated lowest cost options from the region
                # These represent specific time slots at specific locations
                regional_options = report.get("lowest_cost_options", [])
                
                for option in regional_options:
                    # Add region reference to the option for routing
                    option_with_context = option.copy()
                    option_with_context["region_agent"] = region
                    global_options.append(option_with_context)
            
            # Filter for available slots
            available_options = [opt for opt in global_options if opt.get("available", 0) > 0]
            
            print(f"DEBUG: Job {job.job_id} - Available options: {len(available_options)}")
            
            if not available_options:
                # Defer task if no time slots available
                jobs_to_requeue.append(job)
                self.log_event(f"Job {job.job_id[:8]} deferred - No available time slots found.")
                continue

            # STEP 3: SELECT BEST TIME SLOT
            # Strategy: Consult LLM first, fallback to deterministic scoring
            
            # 1. Collect Agent Summaries
            agent_summaries = []
            for region in self.regional_agents:
                report = region.get_report()
                if "agent_summaries" in report:
                    agent_summaries.extend(report["agent_summaries"])

            # 2. Prepare Job Details
            job_details = {
                "id": job.job_id,
                "priority": job.priority,
                "runtime": job.estimated_runtime_hrs,
                "deadline": job.must_start_by.isoformat() if job.must_start_by else "None"
            }
            
            # 3. Ask LLM for Decision
            self.log_event(f"Consulting LLM for job {job.job_id[:8]} assignment...")
            llm_decision = self.llm_client.decide_job_assignment(
                job_details, 
                agent_summaries, 
                available_options, 
                self.job_history
            )
            
            best_option = None
            
            if llm_decision and "selected_agent" in llm_decision:
                # Find the option selected by LLM
                selected_name = llm_decision["selected_agent"]
                reasoning = llm_decision.get("reasoning", "No reasoning provided.")
                
                # Verify the selected agent is actually available
                matching_options = [opt for opt in available_options if opt.get("agent_name") == selected_name]
                
                if matching_options:
                    best_option = matching_options[0] # Take the first slot for that agent
                    self.log_event(f"🤖 LLM Selected {selected_name}: \"{reasoning}\"")
                else:
                    self.log_event(f"⚠ LLM selected {selected_name} but it's not available. Falling back to scoring.")
            
            # 4. Fallback / Deterministic Scoring
            if not best_option:
                # Score each option based on cost and carbon impact
                for opt in available_options:
                    price = opt.get("cost", float('inf'))
                    carbon = opt.get("carbon", 0)
                    # Weighted score: prioritize carbon reduction
                    opt["score"] = price + (carbon * 0.5)
                
                # Sort by score (lowest is best)
                available_options.sort(key=lambda x: x["score"])
                best_option = available_options[0]
                self.log_event("Selected best option based on Cost/Carbon score.")
            
            # Update History
            self.job_history.append({
                "job_id": job.job_id,
                "assigned_to": best_option.get("agent_name"),
                "timestamp": datetime.now().isoformat()
            })
            if len(self.job_history) > 10: self.job_history.pop(0)
            
            # Log the selected time slot details
            self.log_event(
                f"Selected time slot for job {job.job_id[:8]} (Priority {job.priority}): "
                f"Location={best_option.get('agent_name', 'unknown')}, "
                f"Cost={best_option.get('cost', 0):.3f}, "
                f"Carbon={best_option.get('carbon', 0):.1f} gCO2/kWh"
            )
            
            # STEP 4: EXECUTE BECKN LIFECYCLE (Select → Init → Confirm)
            # This reserves the specific time slot at the specific location
            region = best_option["region_agent"]
            provider_id = best_option["agent_name"]  # Provider managing this time slot
            item_id = best_option.get("item_id", "unknown_item")  # Specific time slot ID
            
            try:
                # Execute full Beckn order lifecycle:
                # - SELECT: Request quote for this specific time slot
                # - INIT: Initialize order with job details (compute load, time window, etc.)
                # - CONFIRM: Finalize reservation for this time slot
                success = region.execute_order_lifecycle(provider_id, item_id, job)
                
                if success:
                    self.log_event(
                        f"✓ Job {job.job_id[:8]} (Priority {job.priority}) successfully assigned to \"{provider_id}\" in {region.region}"
                    )
                    job.status = "ASSIGNED"
                    assigned = True
                else:
                    self.log_event(
                        f"✗ Job {job.job_id[:8]} (Priority {job.priority}) failed to assign to \"{provider_id}\" - Beckn lifecycle failed"
                    )
            except Exception as e:
                self.log_event(f"Error during Beckn flow for job {job.job_id[:8]}: {e}")
            
            if not assigned:
                jobs_to_requeue.append(job)

        # Re-queue jobs that couldn't be assigned
        self.task_queue.extend(jobs_to_requeue)
        
        if jobs_to_requeue:
            self.log_event(f"Re-queued {len(jobs_to_requeue)} jobs for next cycle.")

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

    def get_all_jobs(self):
        """
        Returns all jobs and their statuses.
        """
        return [job.dict() for job in self.all_jobs.values()]
