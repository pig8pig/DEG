import os
from typing import Optional, Dict, Any
import openai


class LLMClient:
    """
    LLM client wrapper for ASI Cloud inference endpoint.
    Uses OpenAI-compatible API for easy integration.
    """
    
    def __init__(self, model: str = "mistralai/mistral-nemo", api_key: Optional[str] = None):
        """
        Initialize LLM client.
        
        Args:
            model: Model identifier (default: mistralai/mistral-nemo)
            api_key: API key for ASI Cloud (defaults to ASI_API_KEY env var)
        """
        self.model = model
        self.api_key = api_key or os.environ.get("ASI_API_KEY")
        
        if not self.api_key:
            print("⚠️  WARNING: ASI_API_KEY not set. LLM synthesis will be disabled.")
            self.client = None
        else:
            print(f"✓ LLM Client initialized with API key (model: {self.model})")
            self.client = openai.OpenAI(
                api_key=self.api_key,
                base_url="https://inference.asicloud.cudos.org/v1"
            )
    
    def synthesize(self, prompt: str, max_tokens: int = 500, temperature: float = 0.7) -> Optional[str]:
        """
        Synthesize data using the LLM.
        
        Args:
            prompt: The prompt to send to the LLM
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0.0 = deterministic, 1.0 = creative)
            
        Returns:
            Synthesized text or None if API call fails
        """
        if not self.client:
            return None
        
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return resp.choices[0].message.content
            
        except Exception as e:
            print(f"LLM synthesis error: {e}")
            return None
    
    def synthesize_agent_report(self, agent_data: Dict[str, Any]) -> Optional[str]:
        """
        Synthesize a local agent's report into a natural language summary.
        
        Args:
            agent_data: Dictionary containing agent state data
            
        Returns:
            Natural language summary or None if synthesis fails
        """
        # Extract key metrics
        name = agent_data.get("name", "Unknown")
        region = agent_data.get("region", "Unknown")
        location_data = agent_data.get("location_data", {})
        energy_data = agent_data.get("energy_data", {})
        active_tasks = agent_data.get("active_tasks_count", 0)
        available_capacity = agent_data.get("available_capacity", 0)
        
        # Build prompt
        prompt = f"""You are a data synthesis agent for a Digital Energy Grid system. 
Synthesize the following local agent data into a concise, informative summary for the regional coordinator.

Agent: {name}
Region: {region}
Active Tasks: {active_tasks}
Available Capacity: {available_capacity}

Location Data:
- City: {location_data.get('locality', 'N/A')}
- Carbon Intensity: {location_data.get('carbon_intensity', 'N/A')} gCO2/kWh
- Renewable Mix: {location_data.get('renewable_mix', 'N/A')}%
- Grid Zone: {location_data.get('grid_zone', 'N/A')}
- Available Capacity: {location_data.get('available_capacity', 'N/A')} MW

Energy Data:
- Price: ${energy_data.get('price', 'N/A')}/kWh
- Carbon Intensity: {energy_data.get('carbon_intensity', 'N/A')} gCO2/kWh
- Renewable Mix: {energy_data.get('renewable_mix', 'N/A')}%

Provide a 2-3 sentence summary highlighting:
1. Current operational status (workload and capacity)
2. Energy profile (carbon intensity and renewable mix)
3. Any notable conditions or recommendations

Keep it concise and actionable for the regional agent."""

        return self.synthesize(prompt, max_tokens=200, temperature=0.5)

    def decide_job_assignment(self, job_details: Dict, agent_summaries: list, available_options: list, history: list) -> Optional[Dict]:
        """
        Ask LLM to decide which agent should handle the job based on summaries and quantitative data.
        
        Args:
            job_details: Dict with job info (id, priority, etc)
            agent_summaries: List of text summaries from agents
            available_options: List of available slots with cost/carbon
            history: List of recent assignments
            
        Returns:
            Dict with 'selected_agent' and 'reasoning' or None
        """
        import json
        
        # Format options for prompt
        options_text = ""
        for opt in available_options:
            options_text += f"- Agent: {opt.get('agent_name')}, Cost: ${opt.get('cost', 0):.3f}, Carbon: {opt.get('carbon', 0):.1f} gCO2/kWh\n"
            
        # Format summaries
        summaries_text = ""
        for summary in agent_summaries:
            summaries_text += f"- {summary.get('agent_name')} ({summary.get('location')}): {summary.get('summary')}\n"
            
        prompt = f"""You are the Global Orchestrator for a Digital Energy Grid.
Your task is to assign a compute job to the best available agent.

JOB DETAILS:
- Priority: {job_details.get('priority')} (1-5, 5 is highest)
- Runtime: {job_details.get('runtime')} hours
- Deadline: {job_details.get('deadline', 'None')}

AVAILABLE AGENTS (Quantitative Data):
{options_text}

AGENT STATUS REPORTS (Qualitative Data):
{summaries_text}

RECENT ASSIGNMENTS:
{str(history[-5:]) if history else "None"}

INSTRUCTIONS:
1. Analyze the trade-offs between Cost, Carbon, and Agent Status.
2. For High Priority jobs, favor reliability and speed (check status reports).
3. For Low Priority jobs, favor low cost and low carbon.
4. Avoid overloading agents that report being busy or having issues.
5. Select the best agent name from the Available Agents list.

RESPONSE FORMAT:
You must respond with ONLY a valid JSON object in this format:
{{
  "selected_agent": "Exact Agent Name",
  "reasoning": "One sentence explaining why."
}}
"""
        response = self.synthesize(prompt, max_tokens=150, temperature=0.3)
        if not response:
            return None
            
        try:
            # Clean response to ensure valid JSON
            cleaned = response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned.split("```json")[1].split("```")[0].strip()
            elif cleaned.startswith("```"):
                cleaned = cleaned.split("```")[1].split("```")[0].strip()
                
            return json.loads(cleaned)
        except Exception as e:
            print(f"LLM decision parsing error: {e}")
            return None
