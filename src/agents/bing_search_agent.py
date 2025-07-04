"""
Bing Search Agent for the Multi-Agent Orchestrator system.

Specialized agent for web search, current information, news, factual data, 
and real-time information retrieval.
"""

import os
from azure.ai.agents.models import BingGroundingTool
from .base_agent import AzureAIAgent, AgentConfig

class BingSearchAgent(AzureAIAgent):
    """Specialized agent for web search and information retrieval."""
    
    @staticmethod
    def get_config() -> AgentConfig:
        """Get the Bing search agent configuration."""
        return AgentConfig(
            name="BingSearchAgent", 
            instructions="""You are a specialized web search and information retrieval agent.
Your role is to:
- Search the web for current information and news
- Find factual information about events, people, places
- Gather real-time data and statistics
- Provide citations and sources for information
- Answer questions that require up-to-date knowledge

Always provide accurate, well-sourced information with proper citations.""",
            tools=BingGroundingTool(connection_id=os.environ["BING_CONNECTION_NAME"]).definitions
        )
