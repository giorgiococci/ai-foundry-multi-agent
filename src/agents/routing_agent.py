"""
Routing Agent for the Multi-Agent Orchestrator system.

The routing agent analyzes user questions and decides which agents should handle them,
including execution order and collaboration requirements.
"""

import json
import logging
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum

from .base_agent import AzureAIAgent, AgentConfig

logger = logging.getLogger('multi_agent_orchestrator.routing_agent')

class RoutingStrategy(Enum):
    """Enum for different routing strategies."""
    INITIAL = "initial"  # Initial routing decision
    DYNAMIC = "dynamic"  # Dynamic routing based on agent response
    COMPLETE = "complete"  # No more routing needed

@dataclass
class AgentResponse:
    """Represents a response from an agent."""
    agent_name: str
    response: str
    success: bool
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class DynamicRoutingDecision:
    """Represents a dynamic routing decision after evaluating agent responses."""
    strategy: RoutingStrategy
    next_agents: List[str]
    execution_order: str  # "sequential" or "parallel"
    reasoning: str
    requires_previous_context: bool = True
    is_complete: bool = False
    
    @classmethod
    def from_json(cls, json_str: str) -> 'DynamicRoutingDecision':
        """Create DynamicRoutingDecision from JSON string."""
        try:
            data = json.loads(json_str)
            return cls(
                strategy=RoutingStrategy(data.get('strategy', 'complete')),
                next_agents=data.get('next_agents', []),
                execution_order=data.get('execution_order', 'sequential'),
                reasoning=data.get('reasoning', ''),
                requires_previous_context=data.get('requires_previous_context', True),
                is_complete=data.get('is_complete', len(data.get('next_agents', [])) == 0)
            )
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            # Fallback to complete if parsing fails
            return cls(
                strategy=RoutingStrategy.COMPLETE,
                next_agents=[],
                execution_order='sequential',
                reasoning=f'JSON parsing failed: {e}. Marking as complete.',
                requires_previous_context=False,
                is_complete=True
            )

@dataclass
class RoutingDecision:
    """Represents a routing decision made by the routing agent."""
    agents_to_call: List[str]
    execution_order: str  # "sequential" or "parallel"
    reasoning: str
    collaborative: bool
    is_dynamic: bool = False  # Whether this requires dynamic evaluation
    
    @classmethod
    def from_json(cls, json_str: str) -> 'RoutingDecision':
        """Create RoutingDecision from JSON string."""
        try:
            data = json.loads(json_str)
            agents_to_call = data.get('agents_to_call', [])
            
            # Ensure we always have at least one agent
            if not agents_to_call:
                agents_to_call = ['detailed_answer']  # Default fallback agent
                
            return cls(
                agents_to_call=agents_to_call,
                execution_order=data.get('execution_order', 'sequential'),
                reasoning=data.get('reasoning', ''),
                collaborative=data.get('collaborative', False),
                is_dynamic=data.get('is_dynamic', False)
            )
        except (json.JSONDecodeError, KeyError) as e:
            # Fallback to simple routing if JSON parsing fails
            return cls(
                agents_to_call=['detailed_answer'],
                execution_order='sequential',
                reasoning=f'JSON parsing failed: {e}. Defaulting to detailed answer agent.',
                collaborative=False,
                is_dynamic=False
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
    3. "detailed_answer" - For comprehensive, well-structured explanations, educational content, tutorials, and detailed answers that require excellent formatting and thorough coverage

    Your task is to analyze the user's question and decide:
    - Which agent(s) should handle the request
    - Whether they should work sequentially or in parallel
    - Whether collaboration between agents is needed
    - Whether dynamic routing is needed (when you can't determine all agents upfront)

    Respond ONLY with a JSON object in this exact format:
    {
        "agents_to_call": ["agent_name"],
        "execution_order": "sequential" or "parallel",
        "reasoning": "Brief explanation of your decision",
        "collaborative": true or false,
        "is_dynamic": true or false
    }

    Set "is_dynamic": true when:
    - You need to see results from one agent before deciding on the next
    - The user's request is ambiguous and may require follow-up agents
    - The outcome depends on what the first agent finds or produces

    Examples:
    - For "Calculate 2+2": {"agents_to_call": ["code_interpreter"], "execution_order": "sequential", "reasoning": "Simple mathematical calculation", "collaborative": false, "is_dynamic": false}
    - For "What's the weather today?": {"agents_to_call": ["bing_search"], "execution_order": "sequential", "reasoning": "Current information lookup", "collaborative": false, "is_dynamic": false}
    - For "What is GraphRAG?": {"agents_to_call": ["detailed_answer"], "execution_order": "sequential", "reasoning": "Needs comprehensive explanation with good formatting", "collaborative": false, "is_dynamic": false}
    - For "Explain machine learning": {"agents_to_call": ["detailed_answer"], "execution_order": "sequential", "reasoning": "Educational content requiring detailed explanation", "collaborative": false, "is_dynamic": false}
    - For "Search for Python trends and create a chart": {"agents_to_call": ["bing_search", "code_interpreter"], "execution_order": "sequential", "reasoning": "Need to search first, then analyze data", "collaborative": true, "is_dynamic": false}
    - For "Find information about a topic and analyze if needed": {"agents_to_call": ["bing_search"], "execution_order": "sequential", "reasoning": "Start with search, then decide if analysis is needed", "collaborative": false, "is_dynamic": true}

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
                logger.info(f"Routing decision: {decision.agents_to_call} - {decision.reasoning} (Dynamic: {decision.is_dynamic})")
                return decision
            else:
                # Fallback if no JSON found
                logger.warning("No valid JSON found in routing response, using fallback")
                return RoutingAgent._fallback_route_message(user_message)
                
        except Exception as e:
            logger.error(f"Error in routing agent: {str(e)}")
            return RoutingAgent._fallback_route_message(user_message)
    
    async def evaluate_agent_response(
        self, 
        original_request: str, 
        agent_responses: List[AgentResponse],
        remaining_context: str = ""
    ) -> DynamicRoutingDecision:
        """
        Evaluate agent responses and decide if additional agents are needed.
        
        Args:
            original_request: The original user request
            agent_responses: List of responses from agents that have been called
            remaining_context: Any additional context about what still needs to be done
            
        Returns:
            DynamicRoutingDecision indicating next steps
        """
        try:
            logger.info(f"Evaluating {len(agent_responses)} agent responses for dynamic routing")
            
            # Prepare the evaluation context
            evaluation_context = self._prepare_evaluation_context(
                original_request, agent_responses, remaining_context
            )
            
            # Create a specialized prompt for dynamic routing evaluation
            evaluation_prompt = f"""You are evaluating agent responses to determine if additional agents are needed.

Original user request: "{original_request}"

Agent responses so far:
{evaluation_context}

Available agents for next steps:
1. "code_interpreter" - For mathematical calculations, data analysis, programming, code execution, charts, graphs, visualizations
2. "bing_search" - For web search, current information, news, factual data, real-time information
3. "detailed_answer" - For comprehensive, well-structured explanations, educational content, tutorials, and detailed answers that require excellent formatting and thorough coverage

Your task: Determine if the user's request has been fully satisfied or if additional agents are needed.

Respond ONLY with a JSON object in this exact format:
{{
    "strategy": "complete" or "dynamic",
    "next_agents": ["agent_name"] or [],
    "execution_order": "sequential" or "parallel",
    "reasoning": "Brief explanation of your decision",
    "requires_previous_context": true or false,
    "is_complete": true or false
}}

Set "strategy": "complete" and "is_complete": true if:
- The user's request has been fully satisfied
- No additional processing is needed
- The responses adequately answer the original question

Set "strategy": "dynamic" and specify "next_agents" if:
- Additional processing or agents are needed
- The responses reveal new requirements
- Follow-up analysis or search is required

IMPORTANT: Always respond with valid JSON only. No additional text."""

            # Get the dynamic routing decision
            routing_response = await self.process_message(evaluation_prompt)
            
            # Extract JSON from the response
            json_start = routing_response.find('{')
            json_end = routing_response.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = routing_response[json_start:json_end]
                decision = DynamicRoutingDecision.from_json(json_str)
                logger.info(f"Dynamic routing decision: {decision.strategy.value} - {decision.reasoning}")
                return decision
            else:
                # Fallback to complete if no JSON found
                logger.warning("No valid JSON found in dynamic routing response, marking as complete")
                return DynamicRoutingDecision(
                    strategy=RoutingStrategy.COMPLETE,
                    next_agents=[],
                    execution_order='sequential',
                    reasoning='No valid JSON response, assuming request is complete',
                    is_complete=True
                )
                
        except Exception as e:
            logger.error(f"Error in dynamic routing evaluation: {str(e)}")
            return DynamicRoutingDecision(
                strategy=RoutingStrategy.COMPLETE,
                next_agents=[],
                execution_order='sequential',
                reasoning=f'Error in evaluation: {str(e)}. Marking as complete.',
                is_complete=True
            )
    
    def _prepare_evaluation_context(
        self, 
        original_request: str, 
        agent_responses: List[AgentResponse],
        remaining_context: str
    ) -> str:
        """Prepare context string for dynamic routing evaluation."""
        context_parts = []
        
        for i, response in enumerate(agent_responses, 1):
            status = "✓ Success" if response.success else "✗ Failed"
            context_parts.append(f"""
Agent {i}: {response.agent_name} ({status})
Response: {response.response[:500]}{'...' if len(response.response) > 500 else ''}
""")
        
        if remaining_context:
            context_parts.append(f"\nRemaining context: {remaining_context}")
            
        return "\n".join(context_parts)
    
    async def should_continue_routing(
        self, 
        original_request: str, 
        agent_responses: List[AgentResponse]
    ) -> bool:
        """
        Quick check to determine if dynamic routing evaluation is needed.
        
        Args:
            original_request: The original user request
            agent_responses: List of responses from agents that have been called
            
        Returns:
            True if dynamic routing evaluation should be performed
        """
        # Always evaluate if any agent failed
        if any(not response.success for response in agent_responses):
            return True
            
        # Check for indicators that more work might be needed
        last_response = agent_responses[-1] if agent_responses else None
        if last_response:
            response_lower = last_response.response.lower()
            
            # Keywords that might indicate incomplete work
            incomplete_indicators = [
                'more information needed',
                'additional data required',
                'cannot determine',
                'insufficient information',
                'would need to',
                'requires further',
                'unable to complete'
            ]
            
            if any(indicator in response_lower for indicator in incomplete_indicators):
                return True
        
        # For simple single-agent requests, usually no dynamic routing needed
        if len(agent_responses) == 1 and agent_responses[0].success:
            simple_keywords = ['calculate', 'compute', 'what is', 'define']
            if any(keyword in original_request.lower() for keyword in simple_keywords):
                return False
                
        # Default to checking for complex requests
        return len(agent_responses) > 0
    
    @staticmethod
    def _fallback_route_message(user_message: str) -> RoutingDecision:
        """Fallback routing logic using simple keyword matching."""
        message_lower = user_message.lower()
        
        code_keywords = ['calculate', 'compute', 'analyze', 'code', 'python', 'math', 'chart', 'graph', 'data analysis', 'programming', 'visualization']
        search_keywords = ['search', 'find', 'what is', 'who is', 'weather', 'news', 'current', 'latest', 'information', 'when', 'where']
        
        code_score = sum(1 for keyword in code_keywords if keyword in message_lower)
        search_score = sum(1 for keyword in search_keywords if keyword in message_lower)
        
        # Check for dynamic routing indicators
        dynamic_indicators = ['if needed', 'analyze if', 'check if', 'determine whether', 'see if', 'might need']
        is_dynamic = any(indicator in message_lower for indicator in dynamic_indicators)
        
        # Check for collaborative requests
        if ("search" in message_lower or "find" in message_lower) and ("analyze" in message_lower or "chart" in message_lower):
            return RoutingDecision(
                agents_to_call=["bing_search", "code_interpreter"],
                execution_order="sequential",
                reasoning="Request involves both search and analysis - collaborative approach needed",
                collaborative=True,
                is_dynamic=is_dynamic
            )
        elif code_score > search_score:
            return RoutingDecision(
                agents_to_call=["code_interpreter"],
                execution_order="sequential",
                reasoning="Code/computation focused request",
                collaborative=False,
                is_dynamic=is_dynamic
            )
        else:
            return RoutingDecision(
                agents_to_call=["bing_search"],
                execution_order="sequential",
                reasoning="Information/search focused request",
                collaborative=False,
                is_dynamic=is_dynamic
            )
