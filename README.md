# Multi-Agent Orchestrator with Azure AI Foundry SDK

A sophisticated multi-agent system that demonstrates how to create, manage, and orchestrate multiple AI agents using Azure AI Foundry SDK with optional Semantic Kernel integration.

## 🏗️ Architecture

This project implements a multi-agent orchestration pattern with:

1. **Code Interpreter Agent** - Specialized for data analysis, mathematical calculations, and Python code execution
2. **Bing Search Agent** - Specialized for web search, current information retrieval, and fact-finding
3. **Orchestrator** - Routes requests to appropriate agents and manages collaborative workflows

## 🚀 Features

- **Smart Routing**: Automatically routes user requests to the most appropriate agent
- **Collaborative Processing**: Combines capabilities of multiple agents for complex tasks
- **Azure Integration**: Uses Azure AI Foundry SDK with secure authentication
- **Semantic Kernel Ready**: Optional integration with Microsoft Semantic Kernel for advanced orchestration
- **Interactive Mode**: Chat directly with the multi-agent system
- **Demo Mode**: Run predefined scenarios to test capabilities

## 📋 Prerequisites

1. **Azure Account** with AI Foundry access
2. **Azure AI Foundry Project** with:
   - Model deployment (e.g., GPT-4, GPT-3.5-turbo)
   - Bing Search connection configured
3. **Azure CLI** installed and authenticated (`az login`)
4. **Python 3.8+** with pip

## 🛠️ Setup

### 1. Clone and Install Dependencies

```bash
# Install required packages
pip install -r requirements.txt

# Or run the setup script
python setup.py
```

### 2. Configure Environment

```bash
# Copy the template
cp .env.template .env

# Edit .env with your Azure AI Foundry details
```

Required environment variables:
- `PROJECT_ENDPOINT`: Your Azure AI Foundry project endpoint
- `MODEL_DEPLOYMENT_NAME`: Your model deployment name (e.g., "gpt-4")
- `BING_CONNECTION_NAME`: Full resource path to your Bing Search connection

### 3. Azure Authentication

```bash
# Login to Azure CLI
az login

# Verify authentication
az account show
```

## 🎯 Usage

### Quick Start

```bash
# Run the orchestrator
python src/main.py

# Or use the simplified version
python src/simple_orchestrator.py
```

### Interactive Mode

### Interactive Mode

```python
# Start interactive chat
python src/main.py --interactive

💬 Your question: What is the weather in Seattle today?
🤖 Processing your request...
**Routing Decision:** Current information lookup
**Agent Used:** BingSearchAgent
[Current weather information from Bing Search...]

💬 Your question: Calculate compound interest on $10,000 at 5% for 10 years
🤖 Processing your request...
**Routing Decision:** Mathematical calculation
**Agent Used:** CodeInterpreterAgent
[Mathematical calculation with Python code...]

💬 Your question: quit
👋 Goodbye!
```

### Demo Mode

```python
# Run demonstration scenarios
python src/main.py

🚀 Multi-Agent Orchestrator Demo
============================================================

📝 Test 1: What is the current weather in Seattle?
--------------------------------------------------
**Routing Decision:** Current information lookup
**Agent Used:** BingSearchAgent
[Response...]
```

### Programmatic Usage

```python
from src.simple_orchestrator import SimpleOrchestrator

async def example():
    orchestrator = SimpleOrchestrator()
    await orchestrator.initialize_agents()
    
    # Single agent request
    response = await orchestrator.process_request(
        "Calculate the fibonacci sequence up to 100"
    )
    print(response)
    
    # Collaborative request
    response = await orchestrator.collaborative_request(
        "Search for Python data science trends and analyze the results"
    )
    print(response)

asyncio.run(example())
```

## 🧠 Agent Capabilities

### Code Interpreter Agent
- Mathematical calculations and statistical analysis
- Python code generation and execution
- Data visualization (charts, graphs, plots)
- Data processing and transformation
- Algorithm implementation and optimization

### Bing Search Agent
- Real-time web search and information retrieval
- Current events and news lookup
- Fact verification and research
- Weather and location-based queries
- Recent developments and updates

## 🔄 Orchestration Logic

The system uses intelligent routing to determine which agent should handle each request:

1. **Keyword Analysis**: Analyzes user input for domain-specific keywords
2. **Context Awareness**: Considers the type of task being requested
3. **Collaborative Detection**: Identifies requests that benefit from multiple agents
4. **Fallback Logic**: Defaults to search agent for general queries

## 🔧 Advanced Configuration

### Semantic Kernel Integration

For advanced orchestration capabilities:

```bash
# Install Semantic Kernel
pip install semantic-kernel

# Use the full orchestrator
python src/main.py
```

### Custom Agent Configuration

```python
# Modify agent instructions and capabilities
agent_configs = {
    "code_interpreter": AgentConfig(
        name="CustomCodeAgent",
        instructions="Your specialized instructions here...",
        tools=CodeInterpreterTool().definitions
    )
}
```

### Adding New Agents

```python
# Define new agent type
new_agent_config = AgentConfig(
    name="NewSpecializedAgent",
    instructions="Agent-specific instructions...",
    tools=[CustomTool().definitions]
)

# Add to orchestrator
orchestrator.agent_configs["new_agent"] = new_agent_config
```

## 📁 Project Structure

```
ai-foundry-multi-agent/
├── src/
│   ├── main.py                    # Entry point and demo runner
│   ├── orchestrator.py           # Core orchestration logic
│   └── agents/                    # Modular agent definitions
│       ├── __init__.py           # Package exports
│       ├── base_agent.py         # Base classes and utilities
│       ├── routing_agent.py      # Intelligent routing agent
│       ├── code_interpreter_agent.py  # Code execution agent
│       ├── bing_search_agent.py  # Web search agent
│       └── README.md             # Agent module documentation
├── examples/                      # Example scripts
├── notebooks/                     # Jupyter notebooks
├── requirements.txt              # Python dependencies
├── .env.template                 # Environment variables template
└── README.md                     # This file
```

## 🔐 Security Best Practices

- Uses Azure Default Credential for secure authentication
- No hardcoded secrets or API keys
- Environment-based configuration
- Secure Azure resource connections

## 🐛 Troubleshooting

### Common Issues

1. **Authentication Errors**
   ```bash
   # Re-authenticate with Azure CLI
   az login --use-device-code
   ```

2. **Missing Environment Variables**
   ```bash
   # Check configuration
   python setup.py
   ```

3. **Bing Search Connection Issues**
   - Verify Bing Search resource is created in Azure AI Foundry
   - Check connection string format in environment variables

4. **Model Deployment Errors**
   - Ensure model is deployed and accessible
   - Verify model deployment name matches environment variable

### Debug Mode

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📚 Resources

- [Azure AI Foundry Documentation](https://learn.microsoft.com/en-us/azure/ai-foundry/)
- [Create an Agent with Python SDK](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/quickstart?pivots=programming-language-python-azure)
- [Use Grounding with Bing Search](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/how-to/tools/bing-code-samples?pivots=python)
- [Microsoft Semantic Kernel](https://learn.microsoft.com/en-us/semantic-kernel/)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests and documentation
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review Azure AI Foundry project configuration
3. Verify all environment variables are set correctly
4. Ensure Azure CLI authentication is active

For additional support, refer to the Azure AI Foundry documentation or community forums.
