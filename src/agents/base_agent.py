"""
Base agent classes and configurations for the Multi-Agent Orchestrator system.
"""

import os
import asyncio
import logging
from typing import Dict, List, Optional, Union
from dataclasses import dataclass

from azure.ai.projects import AIProjectClient

logger = logging.getLogger('multi_agent_orchestrator.base_agent')

@dataclass
class AgentConfig:
    """Configuration class for Azure AI agents."""
    name: str
    instructions: str
    tools: List
    agent_id: Optional[str] = None
    thread_id: Optional[str] = None

class AzureAIAgent:
    """Wrapper class for Azure AI Foundry agents with enhanced functionality."""
    
    def __init__(self, project_client: AIProjectClient, config: AgentConfig):
        self.project_client = project_client
        self.config = config
        self.agent = None
        self.thread = None
        
    async def initialize(self):
        """Initialize the agent and create a communication thread."""
        try:
            # Create the agent
            self.agent = self.project_client.agents.create_agent(
                model=os.environ["MODEL_DEPLOYMENT_NAME"],
                name=self.config.name,
                instructions=self.config.instructions,
                tools=self.config.tools
            )
            self.config.agent_id = self.agent.id
            logger.info(f"Created {self.config.name} agent, ID: {self.agent.id}")
            
            # Create a thread for communication
            self.thread = self.project_client.agents.threads.create()
            self.config.thread_id = self.thread.id
            logger.info(f"Created thread for {self.config.name}, ID: {self.thread.id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize {self.config.name} agent: {str(e)}")
            raise
    
    async def process_message(self, message: str) -> str:
        """Process a message through the agent and return the response."""
        if not self.agent or not self.thread:
            raise RuntimeError(f"Agent {self.config.name} not initialized")
        
        try:
            # Add user message to thread
            user_message = self.project_client.agents.messages.create(
                thread_id=self.thread.id,
                role="user",
                content=message
            )
            logger.debug(f"Created message for {self.config.name}, ID: {user_message['id']}")
            
            # Create and process agent run
            run = self.project_client.agents.runs.create_and_process(
                thread_id=self.thread.id, 
                agent_id=self.agent.id
            )
            logger.debug(f"{self.config.name} run finished with status: {run.status}")
            
            if run.status == "failed":
                logger.error(f"{self.config.name} run failed: {run.last_error}")
                return f"Agent {self.config.name} failed to process the request: {run.last_error}"
            
            # Get the latest assistant message
            messages = self.project_client.agents.messages.list(thread_id=self.thread.id)
            for msg in messages:
                if msg.role == "assistant":
                    # Get the text content from the message
                    if hasattr(msg, 'content') and msg.content:
                        if isinstance(msg.content, list) and len(msg.content) > 0:
                            # Handle multiple content items (text + images)
                            text_content = []
                            for content_item in msg.content:
                                if hasattr(content_item, 'text') and content_item.text:
                                    text_content.append(content_item.text.value)
                                elif hasattr(content_item, 'type') and content_item.type == 'text':
                                    text_content.append(str(content_item))
                            
                            if text_content:
                                return '\n'.join(text_content)
                            else:
                                # Fallback to first content item as string
                                return str(msg.content[0])
                        else:
                            return str(msg.content)
            
            return f"No response received from {self.config.name}"
            
        except Exception as e:
            logger.error(f"Error processing message in {self.config.name}: {str(e)}")
            return f"Error processing request in {self.config.name}: {str(e)}"
