"""
Multi-Agent Orchestrator - Core orchestration logic.

This module provides a focused orchestrator that delegates
specific concerns to specialized components.
"""

import os
import asyncio
import logging
from typing import AsyncGenerator

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

from agents import RoutingAgent, RoutingDecision
from conversation_manager import ConversationManager
from agent_manager import AgentManager
from execution_engine import ExecutionEngine
from response_formatter import ResponseFormatter

logger = logging.getLogger('multi_agent_orchestrator.orchestrator')


class MultiAgentOrchestrator:
    """Orchestrator focusing on coordination between specialized components."""

    def __init__(self):
        """Initialize the orchestrator with required components."""
        # Load environment and validate
        load_dotenv()
        self._validate_environment()
        
        # Initialize Azure AI Project Client
        self.project_client = AIProjectClient(
            endpoint=os.environ["PROJECT_ENDPOINT"],
            credential=DefaultAzureCredential()
        )
        
        # Initialize Semantic Kernel if available
        self.kernel = self._initialize_semantic_kernel()
        
        # Initialize components
        self.conversation_manager = ConversationManager()
        self.agent_manager = AgentManager(self.project_client)
        self.execution_engine = ExecutionEngine(self.agent_manager)
        self.formatter = ResponseFormatter()
    
    def _validate_environment(self):
        """Validate required environment variables."""
        required_vars = ["PROJECT_ENDPOINT", "MODEL_DEPLOYMENT_NAME", "BING_CONNECTION_NAME"]
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        if missing_vars:
            raise ValueError(f"Missing environment variables: {', '.join(missing_vars)}")
    
    def _initialize_semantic_kernel(self):
        """Initialize Semantic Kernel if available."""
        if not SEMANTIC_KERNEL_AVAILABLE or not sk:
            logger.info("Using orchestration (Semantic Kernel not available)")
            return None
        
        try:
            kernel = sk.Kernel()
            logger.info("Semantic Kernel initialized")
            return kernel
        except Exception as e:
            logger.warning(f"Failed to initialize Semantic Kernel: {e}")
            return None
    
    async def initialize_agents(self):
        """Initialize all Azure AI agents."""
        await self.agent_manager.initialize_all_agents()
    
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
    
    async def route_message(self, user_message: str) -> RoutingDecision:
        """Route user message using the specialized routing agent."""
        routing_agent = self.agent_manager.get_agent("routing_agent")
        if isinstance(routing_agent, RoutingAgent):
            return await routing_agent.make_routing_decision(user_message)
        else:
            return RoutingAgent._fallback_route_message(user_message)
    
    async def process_request(self, user_message: str, include_history: bool = True) -> str:
        """Process a user request using the routing agent to determine execution plan."""
        try:
            # Add user message to conversation history
            self.conversation_manager.add_user_message(user_message)
            
            # Build context with history if requested
            context_message = user_message
            if include_history:
                context_message = self.conversation_manager.build_context_with_history(user_message)
            
            # Get routing decision
            routing_decision = await self.route_message(context_message)
            logger.debug(f"Routing decision: agents={routing_decision.agents_to_call}, "
                        f"collaborative={routing_decision.collaborative}")
            
            # Validate routing decision
            if not routing_decision.agents_to_call:
                return "Error: No agents specified for handling this request"
            
            if not self.agent_manager.validate_agents(routing_decision.agents_to_call):
                missing = self.agent_manager.get_missing_agents(routing_decision.agents_to_call)
                return f"Error: Agents not available: {', '.join(missing)}"
            
            # Execute based on routing decision
            if routing_decision.collaborative or len(routing_decision.agents_to_call) > 1:
                response = await self.execution_engine.execute_collaborative(context_message, routing_decision)
            else:
                response = await self.execution_engine.execute_single_agent(context_message, routing_decision)
            
            # Add response to conversation history
            agent_used = routing_decision.agents_to_call[0] if routing_decision.agents_to_call else "unknown"
            self.conversation_manager.add_assistant_message(response, agent_used)
            
            return response
            
        except Exception as e:
            error_msg = f"Error processing request: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    async def process_request_stream(self, user_message: str, include_history: bool = True) -> AsyncGenerator[dict, None]:
        """Process a user request with streaming responses."""
        try:
            # Add user message to conversation history
            self.conversation_manager.add_user_message(user_message)
            
            # Build context with history if requested
            context_message = user_message
            if include_history:
                context_message = self.conversation_manager.build_context_with_history(user_message)
            
            # Get routing decision
            routing_decision = await self.route_message(context_message)
            
            # Send routing information
            yield {
                'type': 'routing',
                'content': self.formatter.format_routing_info(routing_decision),
                'agent': 'routing_agent'
            }
            
            # Validate routing decision
            if not routing_decision.agents_to_call:
                yield {'type': 'error', 'content': "Error: No agents specified for handling this request"}
                return
            
            if not self.agent_manager.validate_agents(routing_decision.agents_to_call):
                missing = self.agent_manager.get_missing_agents(routing_decision.agents_to_call)
                yield {'type': 'error', 'content': f"Error: Agents not available: {', '.join(missing)}"}
                return
            
            # Track response for conversation history
            full_response = ""
            
            # Execute with streaming
            if routing_decision.collaborative or len(routing_decision.agents_to_call) > 1:
                async for chunk in self.execution_engine.execute_collaborative_stream(context_message, routing_decision):
                    full_response += chunk.get('content', '')
                    yield chunk
            else:
                async for chunk in self.execution_engine.execute_single_agent_stream(context_message, routing_decision):
                    full_response += chunk.get('content', '')
                    yield chunk
            
            # Send completion signal
            yield {
                'type': 'complete',
                'content': '',
                'agent': routing_decision.agents_to_call[0] if routing_decision.agents_to_call else "unknown"
            }
            
            # Add response to conversation history
            agent_used = routing_decision.agents_to_call[0] if routing_decision.agents_to_call else "unknown"
            self.conversation_manager.add_assistant_message(full_response, agent_used)
            
        except Exception as e:
            error_msg = f"Error processing request: {str(e)}"
            logger.error(error_msg)
            yield {'type': 'error', 'content': error_msg}
    
    # Convenience methods for backward compatibility and easier access
    async def collaborative_request(self, user_message: str) -> str:
        """Process a collaborative request (backward compatibility)."""
        return await self.process_request(user_message)
    
    def get_conversation_history(self):
        """Get the current conversation history."""
        return self.conversation_manager.get_history()
    
    def clear_conversation_history(self):
        """Clear the conversation history."""
        self.conversation_manager.clear_history()
        logger.info("Conversation history cleared")
    
    def get_conversation_summary(self) -> str:
        """Get a formatted summary of the conversation."""
        return self.conversation_manager.get_summary()
