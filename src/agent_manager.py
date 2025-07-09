"""
Agent Manager - Handles agent initialization and management.
"""

import logging
from typing import Dict
from azure.ai.projects import AIProjectClient
from agents import (
    AzureAIAgent,
    RoutingAgent,
    CodeInterpreterAgent,
    BingSearchAgent,
    DetailedAnswerAgent
)

logger = logging.getLogger('multi_agent_orchestrator.agent_manager')


class AgentManager:
    """Manages agent initialization and lifecycle."""
    
    def __init__(self, project_client: AIProjectClient):
        self.project_client = project_client
        self.agents: Dict[str, AzureAIAgent] = {}
        self._agent_configs = {
            "routing_agent": RoutingAgent.get_config(),
            "code_interpreter": CodeInterpreterAgent.get_config(),
            "bing_search": BingSearchAgent.get_config(),
            "detailed_answer": DetailedAnswerAgent.get_config()
        }
    
    async def initialize_all_agents(self):
        """Initialize all Azure AI agents."""
        logger.info("Initializing Azure AI agents...")
        
        # Agent initialization mapping
        agent_classes = {
            "routing_agent": RoutingAgent,
            "code_interpreter": CodeInterpreterAgent,
            "bing_search": BingSearchAgent,
            "detailed_answer": DetailedAnswerAgent
        }
        
        for agent_name, agent_class in agent_classes.items():
            config = self._agent_configs[agent_name]
            agent = agent_class(self.project_client, config)
            await agent.initialize()
            self.agents[agent_name] = agent
            logger.debug(f"Initialized {agent_name}")
        
        logger.info("All agents initialized successfully")
    
    def get_agent(self, agent_name: str) -> AzureAIAgent:
        """Get a specific agent by name."""
        if agent_name not in self.agents:
            raise ValueError(f"Agent {agent_name} not found")
        return self.agents[agent_name]
    
    def validate_agents(self, agent_names: list) -> bool:
        """Validate that all specified agents exist."""
        return all(agent_name in self.agents for agent_name in agent_names)
    
    def get_missing_agents(self, agent_names: list) -> list:
        """Get list of missing agents."""
        return [name for name in agent_names if name not in self.agents]
