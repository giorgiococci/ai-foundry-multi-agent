"""
Conversation Manager - Handles conversation history and context building.
"""

import time
from typing import List
from dataclasses import dataclass


@dataclass
class ConversationMessage:
    """Represents a single message in the conversation."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: float
    agent_used: str = None


class ConversationManager:
    """Manages conversation history and context building."""
    
    def __init__(self):
        self.conversation_history: List[ConversationMessage] = []
    
    def add_user_message(self, content: str) -> ConversationMessage:
        """Add a user message to conversation history."""
        msg = ConversationMessage(
            role="user",
            content=content,
            timestamp=time.time()
        )
        self.conversation_history.append(msg)
        return msg
    
    def add_assistant_message(self, content: str, agent_used: str = "unknown") -> ConversationMessage:
        """Add an assistant message to conversation history."""
        msg = ConversationMessage(
            role="assistant",
            content=content,
            timestamp=time.time(),
            agent_used=agent_used
        )
        self.conversation_history.append(msg)
        return msg
    
    def build_context_with_history(self, current_message: str, max_messages: int = 10) -> str:
        """Build a context message that includes conversation history."""
        if len(self.conversation_history) <= 1:
            return current_message
            
        context_parts = ["=== CONVERSATION HISTORY ==="]
        
        # Include recent messages to avoid token limits
        recent_history = self.conversation_history[-max_messages:]
        
        for msg in recent_history[:-1]:  # Exclude the current message we just added
            if msg.role == "user":
                context_parts.append(f"User: {msg.content}")
            else:
                # Extract core content without formatting
                content = self._extract_core_content(msg.content)
                context_parts.append(f"Assistant: {content}")
        
        context_parts.extend([
            "=== CURRENT REQUEST ===",
            current_message
        ])
        
        return '\n'.join(context_parts)
    
    def _extract_core_content(self, content: str) -> str:
        """Extract core content from formatted assistant messages."""
        if "**Agent Used:**" not in content:
            return content
            
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
                
        return '\n'.join(response_lines).strip()
    
    def get_history(self) -> List[ConversationMessage]:
        """Get a copy of the conversation history."""
        return self.conversation_history.copy()
    
    def clear_history(self):
        """Clear the conversation history."""
        self.conversation_history.clear()
    
    def get_summary(self) -> str:
        """Get a formatted summary of the conversation."""
        if not self.conversation_history:
            return "No conversation history available."
        
        summary_parts = [
            f"Conversation History ({len(self.conversation_history)} messages):",
            "-" * 50
        ]
        
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
