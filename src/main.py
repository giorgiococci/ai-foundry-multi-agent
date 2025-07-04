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
    # Example interactions showcasing different routing scenarios
    test_messages = [
        "What is the current weather in Seattle?",
        "Calculate the compound interest on $10,000 invested at 5% annual rate for 10 years",
        "Find the latest news about artificial intelligence developments",
        "Create a Python function to calculate fibonacci numbers and show the first 10 numbers",
        "Search for information about quantum computing trends and create a visualization of market growth"
    ]

    print("🚀 Multi-Agent Orchestrator Demo")
    print("=" * 60)

    try:
        # Initialize orchestrator and use it as a context manager
        async with MultiAgentOrchestrator() as orchestrator:
            await orchestrator.initialize_agents()

            # Process each test message
            for i, message in enumerate(test_messages, 1):
                print(f"\n📝 Test {i}: {message}")
                print("-" * 50)

                try:
                    response = await orchestrator.process_request(message)
                    print(response)
                except Exception as e:
                    print(f"❌ Error processing message: {str(e)}")

                print("-" * 50)

            print(f"\n✅ Demo completed successfully! Processed {len(test_messages)} test messages.")

    except Exception as e:
        logger.error(f"Demo failed: {str(e)}")
        print(f"\n❌ Demo failed: {str(e)}")
        print("\nPlease ensure:")
        print("1. All environment variables are set (PROJECT_ENDPOINT, MODEL_DEPLOYMENT_NAME, BING_CONNECTION_NAME)")
        print("2. You're authenticated via Azure CLI (az login)")
        print("3. Bing Search resource is configured in Azure AI Foundry")

async def run_interactive():
    """Run the multi-agent orchestrator in interactive mode."""
    print("🚀 Multi-Agent Orchestrator - Interactive Mode")
    print("=" * 60)
    print("Type your questions and the system will route them to the appropriate agents.")
    print("Type 'quit' or 'exit' to stop.\n")

    try:
        async with MultiAgentOrchestrator() as orchestrator:
            await orchestrator.initialize_agents()

            while True:
                try:
                    user_input = input("\n💬 Your question: ").strip()

                    if user_input.lower() in ['quit', 'exit', 'q']:
                        print("👋 Goodbye!")
                        break

                    if not user_input:
                        continue

                    print("\n🤖 Processing your request...")
                    print("-" * 50)

                    response = await orchestrator.process_request(user_input)
                    print(response)

                except KeyboardInterrupt:
                    print("\n👋 Goodbye!")
                    break
                except Exception as e:
                    print(f"❌ Error processing request: {str(e)}")

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