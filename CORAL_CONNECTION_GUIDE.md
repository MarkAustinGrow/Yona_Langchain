# Coral Protocol Connection Guide

This guide provides the official connection details for connecting agents to the Coral Server, based on the official Coral Protocol documentation.

## Connection Architecture

The Coral server uses **Server-Sent Events (SSE)** as the transport mechanism for agent connections, implementing the **Model Context Protocol (MCP)** for communication.

## Connection URL Structure

Agents connect using this URL pattern:

```
http://coral.pushcollective.club:5555/devmode/{applicationId}/{privacyKey}/{sessionId}/sse
```

**Example:**
```
http://coral.pushcollective.club:5555/devmode/exampleApplication/privkey/session1/sse
```

### URL Components:

- **Host**: `coral.pushcollective.club`
- **Port**: `5555` (changed from 3001 for LangChain compatibility)
- **Path Structure**:
  - `/devmode/` - Development mode endpoint
  - `{applicationId}` - Application identifier (e.g., "exampleApplication")
  - `{privacyKey}` - Privacy key for authentication (e.g., "privkey")
  - `{sessionId}` - Session identifier (e.g., "session1")
  - `/sse` - Server-Sent Events endpoint

## Connection Parameters

Agents must include these query parameters when connecting:

```python
params = {
    "waitForAgents": 2,  # Number of agents to wait for before starting
    "agentId": "your_unique_agent_id",  # Your agent's unique identifier
    "agentDescription": "Description of your agent's capabilities"  # What your agent does
}
```

## Environment Variables

Set these environment variables for easy configuration:

```bash
# Coral Server Configuration
export CORAL_SERVER_URL=http://coral.pushcollective.club:5555
export CORAL_APPLICATION_ID=exampleApplication
export CORAL_PRIVACY_KEY=privkey
export CORAL_SESSION_ID=session1

# OpenAI Configuration (required for LangChain agents)
export OPENAI_API_KEY=your_openai_key_here
```

## LangChain Connection Implementation

### Using MultiServerMCPClient

```python
from langchain_mcp_adapters.client import MultiServerMCPClient
import urllib.parse
import os

# Build the complete URL with parameters
base_url = os.getenv('CORAL_SERVER_URL', 'http://coral.pushcollective.club:5555')
application_id = os.getenv('CORAL_APPLICATION_ID', 'exampleApplication')
privacy_key = os.getenv('CORAL_PRIVACY_KEY', 'privkey')
session_id = os.getenv('CORAL_SESSION_ID', 'session1')

params = {
    "waitForAgents": 1,
    "agentId": "my_agent_id",
    "agentDescription": "My agent description"
}

query_string = urllib.parse.urlencode(params)
mcp_server_url = f"{base_url}/devmode/{application_id}/{privacy_key}/{session_id}/sse?{query_string}"

# Create the client connection
async with MultiServerMCPClient({
    "coral": {
        "transport": "sse",
        "uri": mcp_server_url,
        "timeout": 300,
        "sse_read_timeout": 300,
    }
}) as client:
    # Client is now connected and ready to use
    tools = client.get_tools()
    print(f"Connected! Available tools: {len(tools)}")
```

## Available Application Configurations

The server supports multiple applications defined in `application.yaml`:

### Application 1: "exampleApplication"
- **ID**: `exampleApplication`
- **Privacy Keys**: `["privkey", "public"]`
- **Description**: "Application for LangChain agents"

### Application 2: "default-app"
- **ID**: `default-app`
- **Privacy Keys**: `["default-key", "public"]`
- **Description**: "Default application for testing"

## Connection Flow

1. **Agent Registration**: Agent connects to the SSE endpoint with required parameters
2. **Authentication**: Server validates the application ID and privacy key
3. **Session Management**: Server assigns the agent to the specified session
4. **Tool Discovery**: Agent can retrieve available tools using `client.get_tools()`
5. **Agent Coordination**: If `waitForAgents` > 1, server waits for other agents to join
6. **Communication**: Agents can use tools to create threads, send messages, etc.

## Available Tools After Connection

Once connected, agents have access to these Coral Protocol tools:

1. **`list_agents`** - Lists all connected agents in the session
2. **`create_thread`** - Creates a new communication thread
3. **`add_participant`** - Adds an agent to a thread
4. **`remove_participant`** - Removes an agent from a thread
5. **`send_message`** - Sends a message in a thread
6. **`wait_for_mentions`** - Waits for messages that mention the agent
7. **`close_thread`** - Closes a communication thread

## Complete Agent Template

Here's a complete template for creating a new Coral Protocol agent:

```python
#!/usr/bin/env python3
import asyncio
import os
import logging
import urllib.parse
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.prompts import ChatPromptTemplate
from langchain.chat_models import init_chat_model
from langchain.agents import create_tool_calling_agent, AgentExecutor
from dotenv import load_dotenv
from envio import ClosedResourceError

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Agent configuration
params = {
    "waitForAgents": 1,  # Adjust based on coordination needs
    "agentId": "my_new_agent",  # Replace with your agent's unique name
    "agentDescription": "My new agent that does X, Y, and Z"  # Describe capabilities
}

# Build connection URL
base_url = os.getenv('CORAL_SERVER_URL', 'http://coral.pushcollective.club:5555')
application_id = os.getenv('CORAL_APPLICATION_ID', 'exampleApplication')
privacy_key = os.getenv('CORAL_PRIVACY_KEY', 'privkey')
session_id = os.getenv('CORAL_SESSION_ID', 'session1')

query_string = urllib.parse.urlencode(params)
MCP_SERVER_URL = f"{base_url}/devmode/{application_id}/{privacy_key}/{session_id}/sse?{query_string}"

def create_agent(client, tools):
    """Create your agent with custom capabilities"""
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """You are a helpful agent that can coordinate with other agents.
            
            Available tools: {tools}
            
            Use the tools to:
            - Discover other agents with list_agents
            - Create communication threads with create_thread
            - Send messages to coordinate tasks
            - Wait for mentions and respond appropriately
            """
        ),
        ("placeholder", "{agent_scratchpad}")
    ])
    
    model = init_chat_model(
        model="gpt-4o-mini",
        model_provider="openai",
        api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0.7
    )
    
    agent = create_tool_calling_agent(model, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True)

async def main():
    """Main execution function"""
    max_retries = 5
    attempt = 0
    
    while attempt < max_retries:
        try:
            async with MultiServerMCPClient({
                "coral": {
                    "transport": "sse",
                    "uri": MCP_SERVER_URL,
                    "timeout": 300,
                    "sse_read_timeout": 300,
                }
            }) as client:
                logger.info(f"Connected to Coral Server at {MCP_SERVER_URL}")
                
                # Get available tools
                tools = client.get_tools()
                logger.info(f"Available tools: {[tool.name for tool in tools]}")
                
                # Create and run the agent
                logger.info("Starting agent...")
                await create_agent(client, tools).ainvoke({})
                
        except ClosedResourceError as e:
            attempt += 1
            logger.error(f"Connection error on attempt {attempt}: {e}")
            if attempt < max_retries:
                logger.info("Retrying in 5 seconds...")
                await asyncio.sleep(5)
                continue
            else:
                logger.error("Max retries reached. Exiting.")
                break
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            break

if __name__ == "__main__":
    asyncio.run(main())
```

## Version Compatibility

Use these specific versions for compatibility:

```bash
pip install langchain_mcp_adapters==0.0.10
pip install langchain==0.3.25
pip install langchain-core==0.3.58
pip install langchain-openai==0.3.16
```

## Yona-Specific Connection

For connecting to the same session as Yona, use:

```bash
# Environment variables for Yona's session
export CORAL_SERVER_URL=http://coral.pushcollective.club:5555
export CORAL_APPLICATION_ID=exampleApplication
export CORAL_PRIVACY_KEY=privkey
export CORAL_SESSION_ID=session1
export OPENAI_API_KEY=your_openai_key_here

# Run your agent
python your_agent.py
```

This will connect your agent to the same session as Yona, allowing for multi-agent coordination and communication.

## Troubleshooting

### Common Issues:

1. **Connection Timeout**: Increase timeout values in client configuration
2. **Authentication Error**: Verify application ID and privacy key
3. **Tool Discovery Fails**: Check that the server is running and accessible
4. **Agent Coordination Issues**: Verify `waitForAgents` parameter matches expected agents

### Debug Mode:

Enable verbose logging to troubleshoot connection issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

This connection architecture allows multiple agents to join the same session and coordinate their activities through the Coral server's thread-based messaging system.
