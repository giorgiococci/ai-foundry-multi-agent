"""
Response Formatter - Handles response formatting and presentation.
"""

from agents import RoutingDecision


class ResponseFormatter:
    """Handles formatting of responses from agents and routing decisions."""
    
    @staticmethod
    def format_single_agent_response(routing_decision: RoutingDecision, agent_response: str, agent_name: str) -> str:
        """Format response from a single agent."""
        return f"""**Routing Decision:** {routing_decision.reasoning}
**Agent Used:** {agent_name}

{agent_response}"""
    
    @staticmethod
    def format_collaborative_response(routing_decision: RoutingDecision, responses: list) -> str:
        """Format response from collaborative execution."""
        return f"""**Routing Decision:** {routing_decision.reasoning}
**Execution Plan:** {routing_decision.execution_order} execution of {len(routing_decision.agents_to_call)} agents

{"="*60}
{chr(10).join(responses)}
{"="*60}

**Summary:** This response was generated through {routing_decision.execution_order} collaboration between multiple specialized agents."""
    
    @staticmethod
    def format_agent_section(agent_name: str, response: str) -> str:
        """Format a section for an agent's response."""
        return f"**{agent_name}:**\n{response}"
    
    @staticmethod
    def format_error_response(agent_name: str, error: Exception) -> str:
        """Format an error response from an agent."""
        return f"**{agent_name}:** Error - {str(error)}"
    
    @staticmethod
    def format_routing_info(routing_decision: RoutingDecision) -> str:
        """Format routing information for streaming."""
        agent = routing_decision.agents_to_call[0] if routing_decision.agents_to_call else 'unknown'
        return f"**Routing Decision:** {routing_decision.reasoning}\n**Agent:** {agent}"
