"""
Routing Agent for the Multi-Agent Orchestrator system.

The routing agent analyzes user questions and decides which agents should handle them,
including execution order and collaboration requirements.
"""

import json
import logging
from dataclasses import dataclass
from typing import List

from .base_agent import AzureAIAgent, AgentConfig

logger = logging.getLogger('multi_agent_orchestrator.routing_agent')

@dataclass
class RoutingDecision:
    """Represents a routing decision made by the routing agent."""
    agents_to_call: List[str]
    execution_order: str  # "sequential" or "parallel"
    reasoning: str
    collaborative: bool
    
    @classmethod
    def from_json(cls, json_str: str) -> 'RoutingDecision':
        """Create RoutingDecision from JSON string."""
        try:
            data = json.loads(json_str)
            return cls(
                agents_to_call=data.get('agents_to_call', []),
                execution_order=data.get('execution_order', 'sequential'),
                reasoning=data.get('reasoning', ''),
                collaborative=data.get('collaborative', False)
            )
        except (json.JSONDecodeError, KeyError) as e:
            # Fallback to simple routing if JSON parsing fails
            return cls(
                agents_to_call=['bing_search'],
                execution_order='sequential',
                reasoning=f'JSON parsing failed: {e}. Defaulting to search agent.',
                collaborative=False
            )

class RoutingAgent(AzureAIAgent):
    """Specialized routing agent that determines which agents should handle user requests."""
    
    @staticmethod
    def get_config() -> AgentConfig:
        """Get the routing agent configuration."""
        return AgentConfig(
            name="RoutingAgent",
            instructions="""You are a specialized routing agent that analyzes user questions and decides which agents should handle them.

Available agents:
1. "code_interpreter" - For mathematical calculations, data analysis, programming, code execution, charts, graphs, visualizations
2. "bing_search" - For web search, current information, news, factual data, real-time information

Your task is to analyze the user's question and decide:
- Which agent(s) should handle the request
- Whether they should work sequentially or in parallel
- Whether collaboration between agents is needed

Respond ONLY with a JSON object in this exact format:
{
    "agents_to_call": ["agent_name"],
    "execution_order": "sequential" or "parallel",
    "reasoning": "Brief explanation of your decision",
    "collaborative": true or false
}

Examples:
- For "Calculate 2+2": {"agents_to_call": ["code_interpreter"], "execution_order": "sequential", "reasoning": "Simple mathematical calculation", "collaborative": false}
- For "What's the weather today?": {"agents_to_call": ["bing_search"], "execution_order": "sequential", "reasoning": "Current information lookup", "collaborative": false}
- For "Search for Python trends and create a chart": {"agents_to_call": ["bing_search", "code_interpreter"], "execution_order": "sequential", "reasoning": "Need to search first, then analyze data", "collaborative": true}

IMPORTANT: Always respond with valid JSON only. No additional text.""",
            tools=[]  # Routing agent doesn't need special tools
        )
    
    async def make_routing_decision(self, user_message: str) -> RoutingDecision:
        """
        Analyze user message and return routing decision.
        """
        try:
            logger.info(f"Analyzing routing for message: {user_message[:50]}...")
            
            # Use the routing agent to analyze the message
            routing_response = await self.process_message(user_message)
            
            # Extract JSON from the response (in case there's extra text)
            json_start = routing_response.find('{')
            json_end = routing_response.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = routing_response[json_start:json_end]
                decision = RoutingDecision.from_json(json_str)
                logger.info(f"Routing decision: {decision.agents_to_call} - {decision.reasoning}")
                return decision
            else:
                # Fallback if no JSON found
                logger.warning("No valid JSON found in routing response, using fallback")
                return RoutingAgent._fallback_route_message(user_message)
                
        except Exception as e:
            logger.error(f"Error in routing agent: {str(e)}")
            return RoutingAgent._fallback_route_message(user_message)
    
    @staticmethod
    def _fallback_route_message(user_message: str) -> RoutingDecision:
        """Fallback routing logic using simple keyword matching."""
        message_lower = user_message.lower()
        
        code_keywords = ['calculate', 'compute', 'analyze', 'code', 'python', 'math', 'chart', 'graph', 'data analysis', 'programming', 'visualization']
        search_keywords = ['search', 'find', 'what is', 'who is', 'weather', 'news', 'current', 'latest', 'information', 'when', 'where']
        
        code_score = sum(1 for keyword in code_keywords if keyword in message_lower)
        search_score = sum(1 for keyword in search_keywords if keyword in message_lower)
        
        # Check for collaborative requests
        if ("search" in message_lower or "find" in message_lower) and ("analyze" in message_lower or "chart" in message_lower):
            return RoutingDecision(
                agents_to_call=["bing_search", "code_interpreter"],
                execution_order="sequential",
                reasoning="Request involves both search and analysis - collaborative approach needed",
                collaborative=True
            )
        elif code_score > search_score:
            return RoutingDecision(
                agents_to_call=["code_interpreter"],
                execution_order="sequential",
                reasoning="Code/computation focused request",
                collaborative=False
            )
        else:
            return RoutingDecision(
                agents_to_call=["bing_search"],
                execution_order="sequential",
                reasoning="Information/search focused request",
                collaborative=False
            )
