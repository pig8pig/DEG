from typing import List, Dict, Optional
from agents.regional_agent import RegionalAgent
from beckn_models import ComputeJob, BecknCatalog, BecknItem, OrderState, BecknOrder
from beckn_client import BecknClient
from datetime import datetime

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
        Main optimization loop. Assigns tasks from queue to regions based on score.
        """
        if not self.task_queue:
            print("DEBUG: Task queue empty, skipping optimization.")
            return
        
        print(f"\n[GLOBAL] Processing {len(self.task_queue)} jobs in queue")

        jobs_to_requeue = []

        # STEP 1: DISCOVER - Find available grid windows across all locations
        self.log_event("Starting Beckn discovery for available grid windows...")
        try:
            discovery_result = self.beckn_client.discover()
            
            # Distribute discovery results to all regions
            for region in self.regional_agents:
                # Pass raw discovery data to region to process/filter
                region.process_discovery_result(discovery_result)
                # Trigger aggregation to update reports with new catalog data
                region.aggregate_data()
            
            self.log_event(f"Discovery complete. Found grid windows across {len(self.regional_agents)} regions.")
                        
        except Exception as e:
            self.log_event(f"Discovery failed: {e}")
            print(f"[GLOBAL] Discovery failed: {e}")
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
            
            
            # STEP 2: SELECT REGION BY SCORE
            # Find region with lowest average score
            region_scores = []
            for region in self.regional_agents:
                report = region.get_report()
                avg_score = report.get('average_score', float('inf'))
                region_scores.append({
                    'region': region,
                    'average_score': avg_score
                })
            
            # Sort by average score (lowest is best)
            region_scores.sort(key=lambda x: x['average_score'])
            
            if not region_scores:
                jobs_to_requeue.append(job)
                self.log_event(f"Job {job.job_id[:8]} deferred - No regions available.")
                continue
            
            best_region = region_scores[0]['region']
            
            self.log_event(
                f"Assigning job {job.job_id[:8]} (Priority {job.priority}) to region {best_region.region} "
                f"(avg score: {region_scores[0]['average_score']:.1f})"
            )
            
            # STEP 3: ASSIGN TO REGIONAL AGENT
            try:
                success = best_region.assign_job(job)
                
                if success:
                    self.log_event(
                        f"✓ Job {job.job_id[:8]} (Priority {job.priority}) successfully assigned to region {best_region.region}"
                    )
                    job.status = "ASSIGNED"
                    assigned = True
                else:
                    self.log_event(
                        f"✗ Job {job.job_id[:8]} (Priority {job.priority}) failed to assign to region {best_region.region}"
                    )
            except Exception as e:
                self.log_event(f"Error assigning job {job.job_id[:8]} to region: {e}")
            
            
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
