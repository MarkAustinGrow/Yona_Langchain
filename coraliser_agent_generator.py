import asyncio
import traceback, json, copy, os
from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()

class AgentGenerator:

    def __init__(self, agent_name, mcp_json):
        self.agent_name = agent_name
        self.mcp_json = mcp_json
        self.client = None
    
    def get_tools_description(self):
        tools = self.client.get_tools()
        return "\n".join(
            f"Tool: {tool.name}, Schema: {json.dumps(tool.args).replace('{', '{{').replace('}', '}}')}"
            for tool in tools
        )
    
    def get_agent_config(self):
        return copy.deepcopy(self.mcp_json[self.agent_name])
    
    def get_mcp_description(self):
        print('Creating MCP description for coral')
        formatted_tools = self.get_tools_description()
        system_prompt = (
            "You are an AI system tasked with summarizing the purpose and capabilities of an agent, "
            "based solely on the tools it has access to. "
            "Below is a list of tools available to the agent:\n"
            f"{formatted_tools}\n\n"
            "Using this information, write a concise 1-2 sentence description of what this agent is capable of doing. "
            "Focus on the agent's core functionality as inferred from the tools. "
            "Your response must be a valid JSON object in the following format:\n"
            f"The description must always start with `You are an {self.agent_name} agent capable of...`"
            "{\"description\": \"<insert your concise summary here>\"}"
        )

        llm_helper = ChatOpenAI(
            model=os.getenv('llm_model_name', 'gpt-4o-mini'),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            temperature=0.3,
            max_tokens=16000,
            model_kwargs={"response_format": {"type": "json_object"}}
        )

        response = llm_helper.invoke(system_prompt)
        response = response.content
        description = json.loads(response)["description"]
        print(f"Generated description: {description}")

        return description

    def get_env_or_raise(self, key):
        val = os.getenv(key)
        if not val:
            raise EnvironmentError(f'Missing required environment variable: {key}')
        return val

    async def check_connection(self):
        try:
            mcp_object = self.get_agent_config()
            if "env" in mcp_object:
                mcp_object['env'] = {key: self.get_env_or_raise(key) for key in mcp_object['env']}
            print(f"Checking connection with the MCP: {self.agent_name}")
            async with MultiServerMCPClient(connections={self.agent_name: mcp_object}) as client:
                self.client = client
                session = self.client.sessions
                return True
        except Exception as e:
            print(f"Failed to establish connection: {e}")
            print(traceback.format_exc())
            return False    
    
    def create_agent(self, agent_description):
	
        items = []
        env_code_str = None
        mcp_object = self.get_agent_config()

        for key, val in mcp_object.items():
            if key == "env":
                env_code_str = "{" + ", ".join(
                    f'"{k}": os.getenv("{k}")' for k in val
                ) + "}"
                val_str = env_code_str
            else:
                val_str = repr(val)
            items.append(f'"{key}": {val_str}')

        mcp_dict_code = f'"{self.agent_name}": {{' + ", ".join(items) + "}"

        base_dir = os.path.dirname(__file__)
        coraliser_path = os.path.join(base_dir, 'base_coraliser.py')
        
        # Check if base_coraliser.py exists, if not create a basic template
        if not os.path.exists(coraliser_path):
            print(f"base_coraliser.py not found, creating basic template...")
            self.create_base_coraliser_template(coraliser_path)
        
        with open(coraliser_path, 'r') as py_file:
                base_code = py_file.read()
        
        base_code = base_code.replace('"agentId": "",', f'"agentId": "{self.agent_name}",')
        base_code = base_code.replace('"agentDescription": ""', f'"agentDescription": "{agent_description}"')
        base_code = base_code.replace('"mcp": ""', mcp_dict_code)
        base_code = base_code.replace("agent_tools = multi_connection_client.server_name_to_tools['mcp']",
                                      f"agent_tools = multi_connection_client.server_name_to_tools['{self.agent_name}']")

        filename = f"{self.agent_name.lower()}_coral_agent.py"
        
        with open(filename, "w") as f:
            f.write(base_code)
        print(f"File '{filename}' created successfully.")

    def create_base_coraliser_template(self, coraliser_path):
        """Create a basic base_coraliser.py template if it doesn't exist"""
        template = '''#!/usr/bin/env python3
"""
Base Coraliser Template for Coral Protocol Agent Generation
"""

import asyncio
import os
import json
import logging
import urllib.parse
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.prompts import ChatPromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configuration - will be replaced by generator
params = {
    "waitForAgents": 1,
    "agentId": "",
    "agentDescription": ""
}

# Coral Protocol URL structure
base_url = os.getenv('CORAL_SERVER_URL', 'http://coral.pushcollective.club:5555')
application_id = os.getenv('CORAL_APPLICATION_ID', 'exampleApplication')
privacy_key = os.getenv('CORAL_PRIVACY_KEY', 'privkey')
session_id = os.getenv('CORAL_SESSION_ID', 'session1')

query_string = urllib.parse.urlencode(params)
CORAL_SERVER_URL = f"{base_url}/devmode/{application_id}/{privacy_key}/{session_id}/sse?{query_string}"

def create_agent(client, tools):
    """Create agent with Coral Protocol capabilities"""
    
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            f"""You are an AI agent with access to various tools and Coral Protocol integration capabilities.

Your capabilities include:
- Use list_agents to discover other connected agents
- Use create_thread to start new conversation threads
- Use send_message to communicate with other agents
- Use wait_for_mentions to respond when mentioned
- Use ask_human to interact with users directly

Available tools: {[tool.name for tool in tools]}

Use the tools to accomplish tasks and coordinate with other agents through the Coral Protocol."""
        ),
        ("placeholder", "{agent_scratchpad}")
    ])
    
    model = ChatOpenAI(
        model="gpt-4o-mini",
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0.7,
        max_tokens=1600
    )
    
    agent = create_tool_calling_agent(model, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True)

async def main():
    """Main execution function"""
    max_retries = 5
    attempt = 0
    
    # MCP connection configuration - will be replaced by generator
    mcp_connections = {
        "mcp": ""
    }
    
    while attempt < max_retries:
        try:
            async with MultiServerMCPClient(connections=mcp_connections) as multi_connection_client:
                logger.info(f"Connected to Coral Server at {CORAL_SERVER_URL}")
                
                # Get tools from MCP server
                agent_tools = multi_connection_client.server_name_to_tools['mcp']
                
                logger.info(f"Loaded {len(agent_tools)} tools")
                
                # Create and run the agent
                logger.info("🤖 Starting Coral Protocol Agent")
                logger.info("Ready for multi-agent coordination!")
                
                await create_agent(multi_connection_client, agent_tools).ainvoke({})
                
        except (ConnectionError, OSError, Exception) as e:
            attempt += 1
            logger.error(f"Connection error on attempt {attempt}: {e}")
            if attempt < max_retries:
                logger.info("Retrying in 5 seconds...")
                await asyncio.sleep(5)
                continue
            else:
                logger.error("Max retries reached. Exiting.")
                break

if __name__ == "__main__":
    asyncio.run(main())
'''
        with open(coraliser_path, 'w') as f:
            f.write(template)
        print(f"Created base template: {coraliser_path}")

async def main():
    with open(r'coraliser_settings.json', 'r') as f:
        config = f.read()
    
    mcp_json = json.loads(config)
    agent_list = list(mcp_json['mcpServers'].keys())
    print(f"List of available agents: {agent_list}")
    mcp_json = mcp_json['mcpServers']
    
    for agent_name in agent_list:
        try:
            agent_generator = AgentGenerator(agent_name, mcp_json)
            if await agent_generator.check_connection():
                description = agent_generator.get_mcp_description()
                agent_generator.create_agent(description)
        except Exception as e:
            print(f"Failed creating coralised agent: {e}")
            print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main())
