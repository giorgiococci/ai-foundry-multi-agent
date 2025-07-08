"""
Multi-Agent Orchestrator Chainlit UI

A beautiful web interface for the Multi-Agent Orchestrator system that provides
an interactive chat experience with specialized AI agents.
"""

import asyncio
import logging
import time
from typing import Optional, List, Dict

import chainlit as cl

from orchestrator import MultiAgentOrchestrator, ConversationMessage

# Configure logging
logger = logging.getLogger('multi_agent_orchestrator.ui')

# Custom avatars for different agent types (URLs only in Chainlit 2.x)
AGENT_AVATARS = {
    "routing_agent": "https://cdn-icons-png.flaticon.com/512/3094/3094837.png",
    "code_interpreter": "https://cdn-icons-png.flaticon.com/512/1055/1055687.png", 
    "bing_search": "https://cdn-icons-png.flaticon.com/512/751/751463.png",
    "detailed_answer": "https://cdn-icons-png.flaticon.com/512/3135/3135715.png",
    "user": "https://cdn-icons-png.flaticon.com/512/1077/1077012.png",
    "system": "https://cdn-icons-png.flaticon.com/512/2991/2991148.png"
}

@cl.on_chat_start
async def start():
    """Initialize the chat session when a user starts chatting."""
    # Clean up any previous session data
    previous_orchestrator = cl.user_session.get("orchestrator")
    if previous_orchestrator:
        previous_orchestrator.clear_conversation_history()
        logger.info("Cleared previous orchestrator conversation history")
    
    # Initialize the orchestrator for this session
    try:
        await cl.Message(
            content="🚀 **Initializing Multi-Agent Orchestrator...**",
            author="System"
        ).send()
        
        # Create and initialize orchestrator for this session
        orchestrator = MultiAgentOrchestrator()
        await orchestrator.initialize_agents()
        
        # Success message with agent info
        agent_list = "\n".join([f"• **{name.replace('_', ' ').title()}** - Ready" 
                               for name in orchestrator.agents.keys()])
        
        welcome_msg = f"""
# 🎉 Welcome to Multi-Agent Orchestrator!

## Available Agents:
{agent_list}

## How it works:
- 🧠 **Smart Routing**: Your questions are automatically routed to the most suitable agent
- 📚 **Context Awareness**: The system maintains conversation history for better responses
- 🔄 **Agent Collaboration**: Agents can work together to provide comprehensive answers

## Get Started:
Type your question below and watch the magic happen! The system will automatically:
1. Route your question to the best agent
2. Maintain conversation context
3. Provide detailed, accurate responses

**Try asking about:**
- 🌍 Current events or search queries
- 💻 Code problems or programming questions  
- 📊 Data analysis or calculations
- 📖 Detailed explanations on any topic
"""
        
        await cl.Message(
            content=welcome_msg,
            author="System"
        ).send()
        
        # Store user session data with fresh identifiers
        current_time = time.time()
        cl.user_session.set("orchestrator", orchestrator)
        cl.user_session.set("message_count", 0)
        cl.user_session.set("session_id", str(current_time))  # Unique session identifier
        cl.user_session.set("session_start_time", current_time)
        
        logger.info(f"New chat session initialized with fresh orchestrator (Session: {cl.user_session.get('session_id')})")
        
    except Exception as e:
        error_msg = f"""
# ❌ Initialization Failed

**Error:** {str(e)}

**Please ensure:**
1. All environment variables are set (`PROJECT_ENDPOINT`, `MODEL_DEPLOYMENT_NAME`, `BING_CONNECTION_NAME`)
2. You're authenticated via Azure CLI (`az login`)
3. Bing Search resource is configured in Azure AI Foundry

**Need help?** Check the README.md for setup instructions.
"""
        await cl.Message(
            content=error_msg,
            author="System"
        ).send()
        logger.error(f"Failed to initialize orchestrator: {str(e)}")

@cl.on_message
async def main(message: cl.Message):
    """Handle incoming user messages."""
    orchestrator = cl.user_session.get("orchestrator")
    message_count = cl.user_session.get("message_count", 0)
    session_id = cl.user_session.get("session_id")
    
    # Debug logging to track session state
    logger.info(f"Processing message in session {session_id}, message count: {message_count}")
    
    if not orchestrator:
        await cl.Message(
            content="❌ **System not initialized.** Please refresh the page to restart.",
            author="System"
        ).send()
        return
    
    # Additional check to ensure conversation history is clean for new sessions
    session_start_time = cl.user_session.get("session_start_time")
    current_time = time.time()
    
    # If this is a very fresh session (within 10 seconds of start), ensure history is clean
    if message_count == 0 or (session_start_time and current_time - session_start_time < 10):
        orchestrator.clear_conversation_history()
        logger.info(f"Ensured clean conversation history for session {session_id}")
    
    # Increment message count
    message_count += 1
    cl.user_session.set("message_count", message_count)
    
    # Handle special commands
    user_input = message.content.strip().lower()
    
    if user_input in ['clear', 'reset']:
        orchestrator.clear_conversation_history()
        cl.user_session.set("message_count", 0)
        # Generate new session ID to mark fresh start
        cl.user_session.set("session_id", str(time.time()))
        logger.info(f"Conversation history cleared, new session ID: {cl.user_session.get('session_id')}")
        await cl.Message(
            content="🧹 **Conversation history cleared!** Starting fresh.",
            author="System"
        ).send()
        return
    
    elif user_input in ['history', 'show history']:
        await show_conversation_history(orchestrator)
        return
    
    elif user_input in ['summary', 'show summary']:
        summary = orchestrator.get_conversation_summary()
        await cl.Message(
            content=f"📊 **{summary}**",
            author="System"
        ).send()
        return
    
    elif user_input in ['help', 'commands']:
        help_msg = """
# 🛠️ Available Commands

- **`clear`** or **`reset`** - Clear conversation history
- **`history`** - Show conversation history
- **`summary`** - Show conversation summary
- **`help`** - Show this help message

**Or just ask any question to get started!**
"""
        await cl.Message(
            content=help_msg,
            author="System"
        ).send()
        return
    
    # Show processing message
    processing_msg = cl.Message(
        content=f"🤖 **Processing your request** (Message {message_count})...",
        author="System"
    )
    await processing_msg.send()
    
    try:
        # Process the request with conversation history
        include_history = message_count > 1
        response = await orchestrator.process_request(
            message.content, 
            include_history=include_history
        )
        
        # Get the agent that was used for this response
        history = orchestrator.get_conversation_history()
        agent_used = None
        if history:
            last_assistant_msg = next(
                (msg for msg in reversed(history) if msg.role == "assistant"), 
                None
            )
            if last_assistant_msg:
                agent_used = last_assistant_msg.agent_used
        
        # Determine avatar and author based on agent used
        if agent_used and agent_used in AGENT_AVATARS:
            author = agent_used.replace('_', ' ').title()
        else:
            author = "AI Assistant"
        
        # Remove processing message
        await processing_msg.remove()
        
        # Send the response
        await cl.Message(
            content=response,
            author=author
        ).send()
        
        # Show conversation stats if there's history
        if include_history:
            stats_msg = f"💬 **Conversation:** {len(orchestrator.get_conversation_history())} messages"
            if agent_used:
                stats_msg += f" | **Agent:** {agent_used.replace('_', ' ').title()}"
            
            await cl.Message(
                content=stats_msg,
                author="System"
            ).send()
    
    except Exception as e:
        # Remove processing message
        await processing_msg.remove()
        
        # More detailed error logging
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Error processing request: {str(e)}\nDetails:\n{error_details}")
        
        error_msg = f"""
# ❌ Error Processing Request

**Error:** {str(e)}

**You can:**
- Try rephrasing your question
- Type `clear` to reset the conversation
- Type `help` for available commands
"""
        await cl.Message(
            content=error_msg,
            author="System"
        ).send()

async def show_conversation_history(orchestrator: MultiAgentOrchestrator):
    """Display the conversation history in a formatted way."""
    history = orchestrator.get_conversation_history()
    
    if not history:
        await cl.Message(
            content="📝 **No conversation history yet.** Start by asking a question!",
            author="System"
        ).send()
        return
    
    # Group messages and format them
    history_content = f"# 📝 Conversation History ({len(history)} messages)\n\n"
    
    for i, msg in enumerate(history, 1):
        timestamp = time.strftime("%H:%M:%S", time.localtime(msg.timestamp))
        role_icon = "👤" if msg.role == "user" else "🤖"
        
        # Format agent info
        agent_info = ""
        if msg.agent_used:
            agent_info = f" *({msg.agent_used.replace('_', ' ').title()})*"
        
        # Truncate long messages for history view
        content = msg.content
        if len(content) > 200:
            content = content[:200] + "..."
        
        history_content += f"""
**{i}.** `{timestamp}` {role_icon} **{msg.role.title()}**{agent_info}
> {content}

"""
    
    await cl.Message(
        content=history_content,
        author="System"
    ).send()

@cl.on_chat_end
async def end():
    """Clean up when chat session ends."""
    session_id = cl.user_session.get("session_id")
    orchestrator = cl.user_session.get("orchestrator")
    
    if orchestrator:
        # Clear conversation history
        orchestrator.clear_conversation_history()
        logger.info(f"Chat session {session_id} ended, conversation history cleared")
    
    # Clear session data
    cl.user_session.set("orchestrator", None)
    cl.user_session.set("message_count", 0)
    cl.user_session.set("session_id", None)
    logger.info(f"Session {session_id} data cleared")

if __name__ == "__main__":
    # This allows running the app directly with: python app.py
    import subprocess
    import sys
    
    # Run chainlit command
    subprocess.run([sys.executable, "-m", "chainlit", "run", __file__, "--host", "0.0.0.0", "--port", "8000"])
