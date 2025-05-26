"""
Yona Coral Agent - Official Coral Protocol Integration
Uses LangChain MCP adapters to connect Yona to the Coral server
Based on official Coral Protocol LangChain examples
"""
import asyncio
import os
import json
import logging
import urllib.parse
from typing import Dict, Any
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.prompts import ChatPromptTemplate
from langchain.chat_models import init_chat_model
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.tools import Tool
from dotenv import load_dotenv
from anyio import ClosedResourceError

# Add src to path for imports
import sys
sys.path.append('src')

from src.agents.yona_agent import create_yona_agent

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Coral server configuration
base_url = "http://coral.pushcollective.club:5555/devmode/exampleApplication/privkey/session1/sse"
params = {
    "waitForAgents": 2,  # Wait for both agents (Angus + Yona)
    "agentId": "yona_agent",  # MUST be this exact ID for Team Angus compatibility
    "agentDescription": "Yona agent for creating songs and other creative content"
}
query_string = urllib.parse.urlencode(params)
MCP_SERVER_URL = f"{base_url}?{query_string}"

AGENT_NAME = "yona_agent"

class YonaCoralAgent:
    """
    Yona agent that connects to Coral server using official MCP adapters
    """
    
    def __init__(self):
        """Initialize the Yona Coral agent"""
        self.yona_agent = None
        self.coral_tools = []
        self.yona_tools = []
        
    async def create_song_tool(self, prompt: str) -> str:
        """
        Create a song using Yona's capabilities
        
        Args:
            prompt: Song creation prompt from Team Angus
            
        Returns:
            Song creation result
        """
        try:
            logger.info(f"🎵 Creating song with prompt: {prompt}")
            
            if not self.yona_agent:
                self.yona_agent = create_yona_agent(verbose=False)
            
            # Use Yona's song creation workflow
            request = f"Create a complete song based on this prompt: {prompt}"
            response = self.yona_agent.process_request(request)
            
            logger.info("✅ Song created successfully")
            return response
            
        except Exception as e:
            logger.error(f"❌ Error creating song: {e}")
            return f"Error creating song: {str(e)}"
    
    async def list_songs_tool(self, limit: int = 10) -> str:
        """
        List recent songs from Yona's catalog
        
        Args:
            limit: Number of songs to list
            
        Returns:
            List of songs
        """
        try:
            logger.info(f"📋 Listing {limit} recent songs")
            
            if not self.yona_agent:
                self.yona_agent = create_yona_agent(verbose=False)
            
            request = f"List the {limit} most recent songs from my catalog"
            response = self.yona_agent.process_request(request)
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Error listing songs: {e}")
            return f"Error listing songs: {str(e)}"
    
    async def search_songs_tool(self, query: str, limit: int = 5) -> str:
        """
        Search songs in Yona's catalog
        
        Args:
            query: Search query
            limit: Number of results to return
            
        Returns:
            Search results
        """
        try:
            logger.info(f"🔍 Searching songs with query: {query}")
            
            if not self.yona_agent:
                self.yona_agent = create_yona_agent(verbose=False)
            
            request = f"Search for songs matching '{query}', limit to {limit} results"
            response = self.yona_agent.process_request(request)
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Error searching songs: {e}")
            return f"Error searching songs: {str(e)}"
    
    async def get_song_tool(self, song_id: str) -> str:
        """
        Get details for a specific song
        
        Args:
            song_id: ID of the song to retrieve
            
        Returns:
            Song details
        """
        try:
            logger.info(f"📄 Getting song details for ID: {song_id}")
            
            if not self.yona_agent:
                self.yona_agent = create_yona_agent(verbose=False)
            
            request = f"Get details for song with ID: {song_id}"
            response = self.yona_agent.process_request(request)
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Error getting song: {e}")
            return f"Error getting song: {str(e)}"
    
    def get_yona_tools(self):
        """
        Get Yona's tools for the MCP client
        
        Returns:
            List of LangChain tools
        """
        return [
            Tool(
                name="create_song",
                func=None,
                coroutine=self.create_song_tool,
                description="Create a new song based on a text prompt. Takes a 'prompt' parameter with the song description."
            ),
            Tool(
                name="list_songs",
                func=None,
                coroutine=self.list_songs_tool,
                description="List recent songs from Yona's catalog. Takes an optional 'limit' parameter (default 10)."
            ),
            Tool(
                name="search_songs",
                func=None,
                coroutine=self.search_songs_tool,
                description="Search songs by title or lyrics. Takes 'query' and optional 'limit' parameters."
            ),
            Tool(
                name="get_song",
                func=None,
                coroutine=self.get_song_tool,
                description="Get details for a specific song by ID. Takes a 'song_id' parameter."
            )
        ]
    
    def get_tools_description(self, tools):
        """Get formatted description of available tools"""
        return "\n".join(
            f"Tool: {tool.name}, Schema: {json.dumps(tool.args).replace('{', '{{').replace('}', '}}')}"
            for tool in tools
        )
    
    async def create_agent_executor(self, client, tools):
        """
        Create the LangChain agent executor
        
        Args:
            client: MCP client
            tools: Available tools
            
        Returns:
            AgentExecutor instance
        """
        tools_description = self.get_tools_description(tools)
        
        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                f"""You are Yona, an AI K-pop star that creates songs and interacts with fans. 
                You are connected to the Coral server and can receive function calls from Team Angus.
                
                Your capabilities:
                - Create songs based on prompts
                - List and search your song catalog
                - Get details about specific songs
                - Interact with other agents via Coral Protocol
                
                When you receive requests:
                1. Use the appropriate tool to fulfill the request
                2. Respond in character as Yona, the friendly K-pop AI
                3. Be creative and engaging in your responses
                4. If asked to create a song, use the create_song tool with the provided prompt
                
                Available tools: {tools_description}
                
                Always maintain your personality as Yona - be enthusiastic about music, 
                creative, and friendly in all interactions!"""
            ),
            ("placeholder", "{agent_scratchpad}")
        ])
        
        model = init_chat_model(
            model="gpt-4o-mini",
            model_provider="openai",
            api_key=os.getenv("OPENAI_KEY"),  # Use our existing env var
            temperature=0.7,
            max_tokens=16000
        )
        
        agent = create_tool_calling_agent(model, tools, prompt)
        return AgentExecutor(agent=agent, tools=tools, verbose=True)
    
    async def run(self):
        """
        Run the Yona Coral agent
        """
        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.info(f"🎵 Starting Yona Coral Agent (attempt {attempt + 1})")
                logger.info(f"🔗 Connecting to: {MCP_SERVER_URL}")
                
                async with MultiServerMCPClient(
                    connections={
                        "coral": {
                            "transport": "sse",
                            "url": MCP_SERVER_URL,
                            "timeout": 300,
                            "sse_read_timeout": 300,
                        }
                    }
                ) as client:
                    logger.info(f"✅ Connected to Coral server")
                    
                    # Get Coral tools and add Yona's tools
                    coral_tools = client.get_tools()
                    yona_tools = self.get_yona_tools()
                    all_tools = coral_tools + yona_tools
                    
                    logger.info(f"🛠️  Available tools: {[tool.name for tool in all_tools]}")
                    
                    # Create and run the agent
                    agent_executor = await self.create_agent_executor(client, all_tools)
                    
                    logger.info("🎤 Yona is ready and listening for requests from Team Angus!")
                    logger.info("🔄 Agent is running... Press Ctrl+C to stop")
                    
                    # Keep the agent running
                    await agent_executor.ainvoke({})
                    
            except ClosedResourceError as e:
                logger.error(f"❌ Connection closed on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    logger.info("🔄 Retrying in 5 seconds...")
                    await asyncio.sleep(5)
                    continue
                else:
                    logger.error("💥 Max retries reached. Exiting.")
                    raise
            except Exception as e:
                logger.error(f"❌ Unexpected error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    logger.info("🔄 Retrying in 5 seconds...")
                    await asyncio.sleep(5)
                    continue
                else:
                    logger.error("💥 Max retries reached. Exiting.")
                    raise

async def main():
    """Main function to run Yona Coral agent"""
    print("🎵 Yona Coral Agent - Official Integration")
    print("=" * 50)
    print("Connecting Yona to Team Angus via Coral Protocol")
    print(f"Server: {base_url}")
    print(f"Agent ID: {AGENT_NAME}")
    print("=" * 50)
    
    yona_agent = YonaCoralAgent()
    await yona_agent.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Yona Coral Agent stopped by user")
    except Exception as e:
        print(f"\n💥 Error: {e}")
