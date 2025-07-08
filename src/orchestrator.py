"""
Multi-Agent Orchestrator - Core orchestration logic for managing multiple Azure AI agents.

This module handles routing, collaboration, and execution coordination between different
specialized agents in the multi-agent system.
"""

import os
import asyncio
import logging
import time
from typing import Dict, List, Optional, Union
from dataclasses import dataclass

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

# Semantic Kernel imports - install with: pip install semantic-kernel
try:
    import semantic_kernel as sk
    SEMANTIC_KERNEL_AVAILABLE = True
except ImportError:
    SEMANTIC_KERNEL_AVAILABLE = False
    sk = None

from agents import (
    AzureAIAgent,
    AgentConfig,
    RoutingAgent,
    RoutingDecision,
    CodeInterpreterAgent,
    BingSearchAgent,
    DetailedAnswerAgent
)

logger = logging.getLogger('multi_agent_orchestrator.orchestrator')

@dataclass
class ConversationMessage:
    """Represents a single message in the conversation."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: float
    agent_used: Optional[str] = None

class MultiAgentOrchestrator:
    """Core orchestrator for managing multiple Azure AI agents."""

    def __init__(self):
        """Initialize the orchestrator with Azure AI project client and agents."""
        # Load environment variables
        load_dotenv()

        # Validate required environment variables
        required_env_vars = ["PROJECT_ENDPOINT", "MODEL_DEPLOYMENT_NAME", "BING_CONNECTION_NAME"]
        for var in required_env_vars:
            if not os.environ.get(var):
                raise ValueError(f"Environment variable {var} is required")

        # Initialize conversation history
        self.conversation_history: List[ConversationMessage] = []

        # Initialize Azure AI Project Client
        self.project_client = AIProjectClient(
            endpoint=os.environ["PROJECT_ENDPOINT"],
            credential=DefaultAzureCredential()
        )

        # Initialize Semantic Kernel if available
        if SEMANTIC_KERNEL_AVAILABLE and sk:
            try:
                self.kernel = sk.Kernel()
                logger.info("Semantic Kernel initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Semantic Kernel: {e}")
                self.kernel = None
        else:
            self.kernel = None
            logger.info("Using simplified orchestration (Semantic Kernel not available)")

        # Configure agent definitions
        self.agent_configs = {
            "routing_agent": RoutingAgent.get_config(),
            "code_interpreter": CodeInterpreterAgent.get_config(),
            "bing_search": BingSearchAgent.get_config(),
            "detailed_answer": DetailedAnswerAgent.get_config()
        }

        self.agents: Dict[str, AzureAIAgent] = {}

    async def initialize_agents(self):
        """Initialize all Azure AI agents."""
        logger.info("Initializing Azure AI agents...")

        # Initialize agents with their specific classes
        # Routing agent
        routing_agent = RoutingAgent(self.project_client, self.agent_configs["routing_agent"])
        await routing_agent.initialize()
        self.agents["routing_agent"] = routing_agent

        # Code interpreter agent
        code_agent = CodeInterpreterAgent(self.project_client, self.agent_configs["code_interpreter"])
        await code_agent.initialize()
        self.agents["code_interpreter"] = code_agent

        # Bing search agent
        bing_agent = BingSearchAgent(self.project_client, self.agent_configs["bing_search"])
        await bing_agent.initialize()
        self.agents["bing_search"] = bing_agent

        # Detailed answer agent
        detailed_agent = DetailedAnswerAgent(self.project_client, self.agent_configs["detailed_answer"])
        await detailed_agent.initialize()
        self.agents["detailed_answer"] = detailed_agent

        logger.info("All agents initialized successfully")

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        try:
            if hasattr(self.project_client, 'close'):
                close_method = self.project_client.close
                if asyncio.iscoroutinefunction(close_method):
                    await close_method()
                else:
                    close_method()
        except Exception as e:
            logger.debug(f"Error closing client: {e}")
            # Ignore close errors to prevent masking the original exception

    async def route_message(self, user_message: str) -> RoutingDecision:
        """
        Route user message using the specialized routing agent.
        Returns a RoutingDecision object with the routing plan.
        """
        routing_agent = self.agents["routing_agent"]
        if isinstance(routing_agent, RoutingAgent):
            return await routing_agent.make_routing_decision(user_message)
        else:
            # Fallback using keyword matching
            return RoutingAgent._fallback_route_message(user_message)

    async def process_request(self, user_message: str, include_history: bool = True) -> str:
        """
        Process a user request using the routing agent to determine execution plan.
        
        Args:
            user_message: The user's input message
            include_history: Whether to include conversation history in the context
        """
        try:
            # Add user message to conversation history
            user_msg = ConversationMessage(
                role="user",
                content=user_message,
                timestamp=time.time()
            )
            self.conversation_history.append(user_msg)

            # Build context with conversation history if requested
            context_message = user_message
            if include_history and len(self.conversation_history) > 1:
                context_message = self._build_context_with_history(user_message)

            # Get routing decision from the routing agent
            routing_decision = await self.route_message(context_message)
            
            # Debug logging
            logger.debug(f"Routing decision received: agents={routing_decision.agents_to_call}, "
                        f"collaborative={routing_decision.collaborative}, reasoning={routing_decision.reasoning}")

            # Validate agents exist and at least one agent is specified
            if not routing_decision.agents_to_call:
                logger.error("Routing decision returned empty agents list")
                return "Error: No agents specified for handling this request"
                
            for agent_name in routing_decision.agents_to_call:
                if agent_name not in self.agents:
                    return f"Error: Agent {agent_name} not available"

            logger.info(f"Executing plan: {routing_decision.agents_to_call} ({routing_decision.execution_order})")

            # Execute based on the routing decision
            if routing_decision.collaborative or len(routing_decision.agents_to_call) > 1:
                response = await self._execute_collaborative(context_message, routing_decision)
            else:
                # Single agent execution
                agent_name = routing_decision.agents_to_call[0]
                agent = self.agents[agent_name]
                agent_response = await agent.process_message(context_message)

                response = f"""**Routing Decision:** {routing_decision.reasoning}
**Agent Used:** {agent.config.name}

{agent_response}"""

            # Add assistant response to conversation history
            assistant_msg = ConversationMessage(
                role="assistant",
                content=response,
                timestamp=time.time(),
                agent_used=routing_decision.agents_to_call[0] if routing_decision.agents_to_call else "unknown"
            )
            self.conversation_history.append(assistant_msg)

            return response

        except Exception as e:
            error_msg = f"Error processing request: {str(e)}"
            logger.error(error_msg)
            return error_msg

    async def _execute_collaborative(self, user_message: str, routing_decision: RoutingDecision) -> str:
        """Execute a collaborative request using multiple agents."""
        try:
            responses = []

            if routing_decision.execution_order == "sequential":
                # Execute agents sequentially
                context = user_message

                for i, agent_name in enumerate(routing_decision.agents_to_call):
                    agent = self.agents[agent_name]

                    if i == 0:
                        # First agent gets the original message
                        response = await agent.process_message(context)
                    else:
                        # Subsequent agents get context from previous agents
                        collaborative_prompt = f"""
                        Original user request: {user_message}

                        Previous agent results:
                        {' '.join(responses)}

                        Based on the above information, please complete your part of the request.
                        """
                        response = await agent.process_message(collaborative_prompt)

                    responses.append(f"**{agent.config.name}:**\n{response}")

            else:  # parallel execution
                # Execute agents in parallel
                tasks = []
                for agent_name in routing_decision.agents_to_call:
                    agent = self.agents[agent_name]
                    tasks.append(agent.process_message(user_message))

                parallel_responses = await asyncio.gather(*tasks, return_exceptions=True)

                for i, response in enumerate(parallel_responses):
                    agent_name = routing_decision.agents_to_call[i]
                    agent = self.agents[agent_name]

                    if isinstance(response, Exception):
                        responses.append(f"**{agent.config.name}:** Error - {str(response)}")
                    else:
                        responses.append(f"**{agent.config.name}:**\n{response}")

            # Combine all responses
            final_response = f"""**Routing Decision:** {routing_decision.reasoning}
**Execution Plan:** {routing_decision.execution_order} execution of {len(routing_decision.agents_to_call)} agents

{"="*60}
{chr(10).join(responses)}
{"="*60}

**Summary:** This response was generated through {routing_decision.execution_order} collaboration between multiple specialized agents."""

            return final_response

        except Exception as e:
            error_msg = f"Error in collaborative execution: {str(e)}"
            logger.error(error_msg)
            return error_msg

    async def collaborative_request(self, user_message: str) -> str:
        """
        Process a request that might require collaboration between multiple agents.
        Note: The routing agent now determines collaboration automatically in process_request.
        This method is kept for backward compatibility.
        """
        logger.info("Using routing agent to determine collaboration strategy")
        return await self.process_request(user_message)

    def _build_context_with_history(self, current_message: str) -> str:
        """Build a context message that includes conversation history."""
        context_parts = ["=== CONVERSATION HISTORY ==="]
        
        # Include the last 10 messages (or fewer if not available) to avoid token limits
        recent_history = self.conversation_history[-10:]
        
        for msg in recent_history[:-1]:  # Exclude the current message we just added
            if msg.role == "user":
                context_parts.append(f"User: {msg.content}")
            else:
                # For assistant messages, include just the core content without formatting
                content = msg.content
                if "**Agent Used:**" in content:
                    # Extract just the response part, skip the routing decision
                    lines = content.split('\n')
                    response_lines = []
                    skip_next = False
                    for line in lines:
                        if line.startswith("**") and ":**" in line:
                            skip_next = True
                            continue
                        if skip_next and line.strip() == "":
                            skip_next = False
                            continue
                        if not skip_next:
                            response_lines.append(line)
                    content = '\n'.join(response_lines).strip()
                
                context_parts.append(f"Assistant: {content}")
        
        context_parts.append("=== CURRENT REQUEST ===")
        context_parts.append(current_message)
        
        return '\n'.join(context_parts)

    def get_conversation_history(self) -> List[ConversationMessage]:
        """Get the current conversation history."""
        return self.conversation_history.copy()

    def clear_conversation_history(self):
        """Clear the conversation history."""
        self.conversation_history.clear()
        logger.info("Conversation history cleared")

    def get_conversation_summary(self) -> str:
        """Get a formatted summary of the conversation."""
        if not self.conversation_history:
            return "No conversation history available."
        
        summary_parts = [f"Conversation History ({len(self.conversation_history)} messages):"]
        summary_parts.append("-" * 50)
        
        for i, msg in enumerate(self.conversation_history, 1):
            timestamp = time.strftime("%H:%M:%S", time.localtime(msg.timestamp))
            if msg.role == "user":
                summary_parts.append(f"{i}. [{timestamp}] User: {msg.content}")
            else:
                agent_info = f" ({msg.agent_used})" if msg.agent_used else ""
                # Truncate long responses for summary
                content = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
                summary_parts.append(f"{i}. [{timestamp}] Assistant{agent_info}: {content}")
        
        return '\n'.join(summary_parts)
