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
- Price: £{energy_data.get('price', 'N/A')}/kWh
- Carbon Intensity: {energy_data.get('carbon_intensity', 'N/A')} gCO2/kWh
- Renewable Mix: {energy_data.get('renewable_mix', 'N/A')}%

Provide a 2-3 sentence summary highlighting:
1. Current operational status (workload and capacity)
2. Energy profile (carbon intensity and renewable mix)
3. Any notable conditions or recommendations

Keep it concise and actionable for the regional agent."""

        return self.synthesize(prompt, max_tokens=200, temperature=0.5)

    def synthesize_regional_ranking(self, regional_data: Dict[str, Any]) -> Optional[str]:
        """
        Synthesize a regional ranking based on local agent reports.
        
        Args:
            regional_data: Dictionary containing regional aggregation data
            
        Returns:
            Natural language ranking and summary or None if synthesis fails
        """
        region_name = regional_data.get("region", "Unknown")
        agent_summaries = regional_data.get("agent_summaries", [])
        
        # Format summaries for the prompt
        summaries_text = ""
        for summary in agent_summaries:
            summaries_text += f"\n- Agent {summary['agent_name']} ({summary['location']}): {summary['summary']}"
            
        # Build prompt
        prompt = f"""You are a Regional Energy Coordinator for {region_name}.
Your goal is to analyze reports from local agents and rank them based on the cheapest and cleanest energy available.

Local Agent Reports:
{summaries_text}

Based on these reports, please:
1. Rank the locations from best to worst for compute tasks, prioritizing low carbon intensity and cost.
2. Provide a brief justification for the top pick.
3. Summarize the overall energy status of the region.

Format the output clearly with a numbered list for the ranking."""

        return self.synthesize(prompt, max_tokens=400, temperature=0.5)
