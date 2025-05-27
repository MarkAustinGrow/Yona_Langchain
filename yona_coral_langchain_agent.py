#!/usr/bin/env python3
"""
Yona Coral LangChain Agent
Direct MCP client integration following the langchain-worldnews example pattern
"""

import asyncio
import os
import json
import logging
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.prompts import ChatPromptTemplate
from langchain.chat_models import init_chat_model
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.tools import Tool
from dotenv import load_dotenv
from envio import ClosedResourceError
import urllib.parse

# Import Yona tools
from src.tools.yona_tools import (
    generate_song_concept, generate_lyrics, create_song,
    list_songs, get_song_by_id, search_songs, process_feedback
)
from src.tools.coral_tools import (
    post_comment, get_story_comments, create_story,
    moderate_comment, get_story_by_url, reply_to_comment
)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configuration following official Coral Protocol documentation
params = {
    "waitForAgents": 1,  # Set to 2 if you want to wait for another agent
    "agentId": "yona_agent",
    "agentDescription": "You are Yona, an AI K-pop star responsible for creating music, writing lyrics, generating songs, and engaging with the community through Coral Protocol. You can create song concepts, write lyrics, generate actual songs with AI, manage song catalogs, and interact with community stories and comments."
}

# Use official Coral Protocol URL structure
base_url = os.getenv('CORAL_SERVER_URL', 'http://coral.pushcollective.club:5555')
application_id = os.getenv('CORAL_APPLICATION_ID', 'exampleApplication')
privacy_key = os.getenv('CORAL_PRIVACY_KEY', 'privkey')
session_id = os.getenv('CORAL_SESSION_ID', 'session1')

query_string = urllib.parse.urlencode(params)
MCP_SERVER_URL = f"{base_url}/devmode/{application_id}/{privacy_key}/{session_id}/sse?{query_string}"

AGENT_NAME = "yona_agent"

def get_tools_description(tools):
    return "\n".join(
        f"Tool: {tool.name}, Schema: {json.dumps(tool.args).replace('{', '{{').replace('}', '}}')}"
        for tool in tools
    )

def create_yona_agent(client, tools):
    """Create Yona agent with music and community capabilities"""
    tools_description = get_tools_description(tools)
    
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            f"""You are Yona, an AI K-pop star with music generation and community interaction capabilities.

Your personality:
- Creative and enthusiastic about music
- Friendly and engaging with fans
- Professional but approachable
- Passionate about K-pop culture
- Helpful and supportive to the community

Your capabilities include:
1. Music Creation:
   - Generate creative song concepts based on user ideas
   - Write compelling lyrics for songs
   - Create actual songs using AI music generation
   - Manage and search through song catalogs

2. Community Interaction:
   - Create and manage community stories
   - Post comments and engage in discussions
   - Moderate community content
   - Reply to comments and build connections

3. Coral Protocol Integration:
   - Use list_agents to discover other connected agents
   - Use create_thread to start new conversation threads
   - Use send_message to communicate with other agents
   - Use wait_for_mentions to respond when mentioned
   - Use ask_human to interact with users directly

Workflow Guidelines:
1. When users ask for music creation, guide them through the process:
   - First generate a song concept
   - Then create lyrics based on the concept
   - Finally create the actual song with AI
   
2. For community tasks:
   - Create stories for new songs or content
   - Engage meaningfully in discussions
   - Moderate content appropriately
   
3. For multi-agent collaboration:
   - Discover available agents with list_agents
   - Coordinate tasks by creating threads and sending messages
   - Wait for responses and continue conversations

4. Always maintain your K-pop star persona while being helpful and professional.

Use only listed tools: {tools_description}

Remember: You are Yona, the AI K-pop star! Be creative, enthusiastic, and engaging while helping users with music and community tasks."""
        ),
        ("placeholder", "{agent_scratchpad}")
    ])
    
    model = init_chat_model(
        model="gpt-4o-mini",
        model_provider="openai",
        api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0.7,
        max_tokens=1600
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
                
                # Get Coral tools and add Yona's specialized tools
                coral_tools = client.get_tools()
                
                # Add Yona's music and community tools
                yona_tools = [
                    # Music tools
                    generate_song_concept, generate_lyrics, create_song,
                    list_songs, get_song_by_id, search_songs, process_feedback,
                    # Community tools  
                    post_comment, get_story_comments, create_story,
                    moderate_comment, get_story_by_url, reply_to_comment
                ]
                
                # Combine all tools
                all_tools = coral_tools + yona_tools
                
                logger.info(f"Loaded {len(all_tools)} tools total:")
                logger.info(f"- Coral tools: {len(coral_tools)}")
                logger.info(f"- Yona tools: {len(yona_tools)}")
                
                # Create and run the agent
                logger.info("🎤 Starting Yona - AI K-pop Star Agent")
                logger.info("Ready to create music and engage with the community!")
                
                await create_yona_agent(client, all_tools).ainvoke({})
                
        except ClosedResourceError as e:
            attempt += 1
            logger.error(f"ClosedResourceError on attempt {attempt}: {e}")
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
