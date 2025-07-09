"""
Execution Engine - Handles request execution (both streaming and non-streaming).
"""

import asyncio
import logging
from typing import AsyncGenerator
from agents import RoutingDecision
from agent_manager import AgentManager
from response_formatter import ResponseFormatter

logger = logging.getLogger('multi_agent_orchestrator.execution_engine')


class ExecutionEngine:
    """Handles execution of single and collaborative agent requests."""
    
    def __init__(self, agent_manager: AgentManager):
        self.agent_manager = agent_manager
        self.formatter = ResponseFormatter()
    
    async def execute_single_agent(self, message: str, routing_decision: RoutingDecision) -> str:
        """Execute a single agent request."""
        agent_name = routing_decision.agents_to_call[0]
        agent = self.agent_manager.get_agent(agent_name)
        agent_response = await agent.process_message(message)
        
        return self.formatter.format_single_agent_response(
            routing_decision, agent_response, agent.config.name
        )
    
    async def execute_collaborative(self, message: str, routing_decision: RoutingDecision) -> str:
        """Execute a collaborative request using multiple agents."""
        try:
            if routing_decision.execution_order == "sequential":
                responses = await self._execute_sequential(message, routing_decision)
            else:
                responses = await self._execute_parallel(message, routing_decision)
            
            return self.formatter.format_collaborative_response(routing_decision, responses)
            
        except Exception as e:
            error_msg = f"Error in collaborative execution: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    async def _execute_sequential(self, message: str, routing_decision: RoutingDecision) -> list:
        """Execute agents sequentially."""
        context = message
        responses = []
        
        for i, agent_name in enumerate(routing_decision.agents_to_call):
            agent = self.agent_manager.get_agent(agent_name)
            
            if i == 0:
                response = await agent.process_message(context)
            else:
                collaborative_prompt = self._build_collaborative_prompt(message, responses)
                response = await agent.process_message(collaborative_prompt)
            
            responses.append(self.formatter.format_agent_section(agent.config.name, response))
        
        return responses
    
    async def _execute_parallel(self, message: str, routing_decision: RoutingDecision) -> list:
        """Execute agents in parallel."""
        tasks = []
        for agent_name in routing_decision.agents_to_call:
            agent = self.agent_manager.get_agent(agent_name)
            tasks.append(agent.process_message(message))
        
        parallel_responses = await asyncio.gather(*tasks, return_exceptions=True)
        responses = []
        
        for i, response in enumerate(parallel_responses):
            agent_name = routing_decision.agents_to_call[i]
            agent = self.agent_manager.get_agent(agent_name)
            
            if isinstance(response, Exception):
                responses.append(self.formatter.format_error_response(agent.config.name, response))
            else:
                responses.append(self.formatter.format_agent_section(agent.config.name, response))
        
        return responses
    
    def _build_collaborative_prompt(self, original_message: str, previous_responses: list) -> str:
        """Build a collaborative prompt for subsequent agents."""
        return f"""
        Original user request: {original_message}

        Previous agent results:
        {' '.join(previous_responses)}

        Based on the above information, please complete your part of the request.
        """
    
    # Streaming methods
    async def execute_single_agent_stream(self, message: str, routing_decision: RoutingDecision) -> AsyncGenerator[dict, None]:
        """Execute a single agent request with streaming."""
        agent_name = routing_decision.agents_to_call[0]
        agent = self.agent_manager.get_agent(agent_name)
        
        yield {
            'type': 'agent_start',
            'content': f"\n\n**{agent.config.name} Response:**\n",
            'agent': agent_name
        }
        
        async for chunk in agent.process_message_stream(message):
            yield {
                'type': 'content',
                'content': chunk,
                'agent': agent_name
            }
    
    async def execute_collaborative_stream(self, message: str, routing_decision: RoutingDecision) -> AsyncGenerator[dict, None]:
        """Execute a collaborative request with streaming support."""
        try:
            if routing_decision.execution_order == "sequential":
                async for chunk in self._execute_sequential_stream(message, routing_decision):
                    yield chunk
            else:
                async for chunk in self._execute_parallel_stream(message, routing_decision):
                    yield chunk
        except Exception as e:
            error_msg = f"Error in collaborative execution: {str(e)}"
            logger.error(error_msg)
            yield {
                'type': 'error',
                'content': error_msg
            }
    
    async def _execute_sequential_stream(self, message: str, routing_decision: RoutingDecision) -> AsyncGenerator[dict, None]:
        """Execute agents sequentially with streaming."""
        context = message
        responses = []
        
        for i, agent_name in enumerate(routing_decision.agents_to_call):
            agent = self.agent_manager.get_agent(agent_name)
            
            yield {
                'type': 'agent_start',
                'content': f"\n\n**{agent.config.name}:**\n",
                'agent': agent_name
            }
            
            agent_response = ""
            if i == 0:
                async for chunk in agent.process_message_stream(context):
                    agent_response += chunk
                    yield {
                        'type': 'content',
                        'content': chunk,
                        'agent': agent_name
                    }
            else:
                collaborative_prompt = self._build_collaborative_prompt(message, responses)
                async for chunk in agent.process_message_stream(collaborative_prompt):
                    agent_response += chunk
                    yield {
                        'type': 'content',
                        'content': chunk,
                        'agent': agent_name
                    }
            
            responses.append(self.formatter.format_agent_section(agent.config.name, agent_response))
    
    async def _execute_parallel_stream(self, message: str, routing_decision: RoutingDecision) -> AsyncGenerator[dict, None]:
        """Execute agents in parallel with streaming (sequential for streaming purposes)."""
        yield {
            'type': 'info',
            'content': f"\n\n**Executing {len(routing_decision.agents_to_call)} agents in parallel...**\n"
        }
        
        for agent_name in routing_decision.agents_to_call:
            agent = self.agent_manager.get_agent(agent_name)
            
            yield {
                'type': 'agent_start',
                'content': f"\n\n**{agent.config.name}:**\n",
                'agent': agent_name
            }
            
            async for chunk in agent.process_message_stream(message):
                yield {
                    'type': 'content',
                    'content': chunk,
                    'agent': agent_name
                }
