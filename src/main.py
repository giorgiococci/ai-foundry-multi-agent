"""
Multi-Agent Orchestrator Demo - Entry point for demonstrating the multi-agent system.

This module provides a demo of the Multi-Agent Orchestrator system that coordinates
between specialized AI agents for different types of tasks.

Prerequisites:
- Set environment variables: PROJECT_ENDPOINT, MODEL_DEPLOYMENT_NAME, BING_CONNECTION_NAME
- Authenticate via Azure CLI: az login
- Configure Bing Search resource in Azure AI Foundry
"""

import asyncio
import logging
import time

from orchestrator import MultiAgentOrchestrator

# Configure clean logging (suppresses verbose Azure SDK HTTP logs)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

# Suppress verbose Azure SDK logs
logging.getLogger('azure.core.pipeline.policies.http_logging_policy').setLevel(logging.WARNING)
logging.getLogger('azure.ai.projects').setLevel(logging.WARNING)
logging.getLogger('azure.ai.agents').setLevel(logging.WARNING)
logging.getLogger('azure.identity').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

logger = logging.getLogger('multi_agent_orchestrator.main')

async def run_demo():
    """Run the multi-agent orchestrator demo with predefined test scenarios."""
    # Example interactions showcasing different routing scenarios and conversation flow
    test_messages = [
        "What is the current weather in Seattle?",
        "Based on that weather, what activities would you recommend for today?",
        "What is GraphRAG and how does it work?",
        "Calculate the compound interest on $10,000 invested at 5% annual rate for 10 years",
        "Now create a chart showing the growth over time for that calculation",
        "Find the latest news about artificial intelligence developments",
        "Can you summarize the key points from that AI news in a bulleted list?",
        "Explain how machine learning algorithms work in detail",
    ]

    print("🚀 Multi-Agent Orchestrator Demo - Conversation Flow")
    print("=" * 60)
    print("This demo shows how the system maintains conversation context across messages.")

    try:
        # Initialize orchestrator and use it as a context manager
        async with MultiAgentOrchestrator() as orchestrator:
            await orchestrator.initialize_agents()

            # Process each test message with conversation history
            for i, message in enumerate(test_messages, 1):
                print(f"\n📝 Test {i}: {message}")
                print("-" * 50)

                try:
                    # Enable conversation history for all messages after the first
                    include_history = i > 1
                    response = await orchestrator.process_request(message, include_history=include_history)
                    print(response)

                    if include_history:
                        print(f"\n📊 Conversation so far: {len(orchestrator.get_conversation_history())} messages")

                except Exception as e:
                    print(f"❌ Error processing message: {str(e)}")

                print("-" * 50)

                # Add a small delay between messages for better readability
                if i < len(test_messages):
                    print("⏳ Continuing conversation in 2 seconds...")
                    await asyncio.sleep(2)

            print(f"\n✅ Demo completed successfully! Processed {len(test_messages)} test messages.")

            # Show final conversation summary
            print("\n📋 Final Conversation Summary:")
            print("=" * 60)
            summary = orchestrator.get_conversation_summary()
            print(summary)

    except Exception as e:
        logger.error(f"Demo failed: {str(e)}")
        print(f"\n❌ Demo failed: {str(e)}")
        print("\nPlease ensure:")
        print("1. All environment variables are set (PROJECT_ENDPOINT, MODEL_DEPLOYMENT_NAME, BING_CONNECTION_NAME)")
        print("2. You're authenticated via Azure CLI (az login)")
        print("3. Bing Search resource is configured in Azure AI Foundry")

async def run_interactive():
    """Run the multi-agent orchestrator in interactive mode."""
    print("🚀 Multi-Agent Orchestrator - Interactive Conversation Mode")
    print("=" * 70)
    print("Type your questions and the system will route them to the appropriate agents.")
    print("The system maintains conversation history for context-aware responses.")
    print("\nAvailable commands:")
    print("  - Type your question to get an AI response")
    print("  - 'history' - Show conversation history")
    print("  - 'clear' - Clear conversation history")
    print("  - 'summary' - Show conversation summary")
    print("  - 'quit' or 'exit' - Stop the conversation")
    print("-" * 70)

    try:
        async with MultiAgentOrchestrator() as orchestrator:
            await orchestrator.initialize_agents()

            conversation_count = 0

            while True:
                try:
                    # Show conversation count
                    history_len = len(orchestrator.get_conversation_history())
                    prompt = f"\n💬 Message {conversation_count + 1}"
                    if history_len > 0:
                        prompt += f" (History: {history_len} messages)"
                    prompt += ": "

                    user_input = input(prompt).strip()

                    # Handle commands
                    if user_input.lower() in ['quit', 'exit', 'q']:
                        print("\n👋 Thanks for the conversation! Goodbye!")
                        break

                    elif user_input.lower() == 'clear':
                        orchestrator.clear_conversation_history()
                        conversation_count = 0
                        print("🧹 Conversation history cleared!")
                        continue

                    elif user_input.lower() == 'history':
                        history = orchestrator.get_conversation_history()
                        if not history:
                            print("📝 No conversation history yet.")
                        else:
                            print(f"\n📝 Conversation History ({len(history)} messages):")
                            print("-" * 50)
                            for i, msg in enumerate(history, 1):
                                timestamp = time.strftime("%H:%M:%S", time.localtime(msg.timestamp))
                                role_icon = "👤" if msg.role == "user" else "🤖"
                                agent_info = f" [{msg.agent_used}]" if msg.agent_used else ""
                                print(f"{i}. [{timestamp}] {role_icon} {msg.role.title()}{agent_info}:")
                                # Show first 100 characters for brevity
                                content = msg.content[:200] + "..." if len(msg.content) > 200 else msg.content
                                print(f"   {content}")
                                print()
                        continue

                    elif user_input.lower() == 'summary':
                        summary = orchestrator.get_conversation_summary()
                        print(f"\n📊 {summary}")
                        continue

                    if not user_input:
                        continue

                    conversation_count += 1
                    print(f"\n🤖 Processing your request (Message {conversation_count})...")
                    print("-" * 50)

                    # Process with conversation history enabled
                    response = await orchestrator.process_request(user_input, include_history=True)
                    print(response)

                    # Add a separator for readability
                    print("\n" + "─" * 70)

                except KeyboardInterrupt:
                    print("\n\n👋 Conversation interrupted. Goodbye!")
                    break
                except Exception as e:
                    print(f"❌ Error processing request: {str(e)}")
                    print("Try again or type 'quit' to exit.")

    except Exception as e:
        logger.error(f"Interactive mode failed: {str(e)}")
        print(f"\n❌ Interactive mode failed: {str(e)}")
        print("\nPlease ensure:")
        print("1. All environment variables are set (PROJECT_ENDPOINT, MODEL_DEPLOYMENT_NAME, BING_CONNECTION_NAME)")
        print("2. You're authenticated via Azure CLI (az login)")
        print("3. Bing Search resource is configured in Azure AI Foundry")

async def main():
    """Main function - entry point for the application."""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        await run_interactive()
    else:
        await run_demo()

if __name__ == "__main__":
    asyncio.run(main())