"""
Code Interpreter Agent for the Multi-Agent Orchestrator system.

Specialized agent for mathematical calculations, data analysis, programming, 
code execution, charts, graphs, and visualizations.
"""

import os
import sys
import logging
from typing import List, Optional

from azure.ai.agents.models import CodeInterpreterTool
from .base_agent import AzureAIAgent, AgentConfig

# Add parent directory to path for image_manager import
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from image_manager import ImageManager

logger = logging.getLogger('multi_agent_orchestrator.code_interpreter_agent')

class CodeInterpreterAgent(AzureAIAgent):
    """Specialized agent for data analysis and computation tasks with image handling."""
    
    def __init__(self, project_client, config: AgentConfig):
        """Initialize the code interpreter agent with image manager."""
        super().__init__(project_client, config)
        self.image_manager = ImageManager(project_client=project_client)
        
    @staticmethod
    def get_config() -> AgentConfig:
        """Get the code interpreter agent configuration."""
        return AgentConfig(
            name="CodeInterpreterAgent",
            instructions="""You are a specialized data analysis and computation agent. 
Your role is to:
- Perform mathematical calculations and data analysis
- Write and execute Python code for complex computations
- Generate charts, graphs, and visualizations
- Process and analyze datasets
- Solve programming problems and debugging tasks

When creating visualizations or charts:
- Use matplotlib, seaborn, or plotly for creating graphs
- Always save plots with plt.savefig() or equivalent
- Create clear, well-labeled visualizations
- Use appropriate chart types for the data

Always provide clear explanations of your code and results.""",
            tools=CodeInterpreterTool().definitions
        )
    
    async def process_message(self, message: str) -> str:
        """Process a message and handle any images generated."""
        try:
            # Call the parent process_message method
            response = await super().process_message(message)
            
            # Check for images in the latest messages
            if self.thread:
                # Get the latest messages to check for images
                messages = self.project_client.agents.messages.list(thread_id=self.thread.id)
                
                saved_images = []
                for msg in messages:
                    if msg.role == "assistant":
                        # Extract and save any images from the message
                        images = self.image_manager.extract_and_save_images_from_message(msg)
                        saved_images.extend(images)
                        break  # Only check the latest assistant message
            
            return response
            
        except Exception as e:
            logger.error(f"Error in CodeInterpreterAgent.process_message: {str(e)}")
            # Fall back to the original response if image handling fails
            return await super().process_message(message)