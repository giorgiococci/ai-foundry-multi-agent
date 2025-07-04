"""
Code Interpreter Agent for the Multi-Agent Orchestrator system.

Specialized agent for mathematical calculations, data analysis, programming, 
code execution, charts, graphs, and visualizations.
"""

from azure.ai.agents.models import CodeInterpreterTool
from .base_agent import AzureAIAgent, AgentConfig

class CodeInterpreterAgent(AzureAIAgent):
    """Specialized agent for data analysis and computation tasks."""
    
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

Always provide clear explanations of your code and results.""",
            tools=CodeInterpreterTool().definitions
        )
