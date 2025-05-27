#!/usr/bin/env python3
"""
Yona Coral Communication Agent
Official Coral Protocol pattern with communication testing capabilities
Configured for same session as Angus agent with waitForAgents=2
"""

import asyncio
import os
import json
import logging
import requests
import time
import threading
from typing import Dict, List, Any
from dotenv import load_dotenv
import urllib.parse

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class YonaCoralCommunicationAgent:
    """Yona agent with full Coral Protocol communication capabilities"""
    
    def __init__(self):
        # Agent configuration following official pattern
        self.agent_id = "yona_agent"
        self.agent_description = "You are Yona, an AI K-pop star responsible for creating music, writing lyrics, generating songs, and engaging with the community through Coral Protocol."
        
        # Coral Protocol configuration (official pattern - same session as Angus)
        self.coral_server_url = os.getenv('CORAL_SERVER_URL', 'http://coral.pushcollective.club:5555')
        self.application_id = os.getenv('CORAL_APPLICATION_ID', 'exampleApplication')
        self.privacy_key = os.getenv('CORAL_PRIVACY_KEY', 'privkey')
        self.session_id = os.getenv('CORAL_SESSION_ID', 'session1')
        
        # Build MCP server URL following official pattern
        params = {
            "waitForAgents": 2,  # Wait for both Yona and Angus
            "agentId": self.agent_id,
            "agentDescription": self.agent_description
        }
        query_string = urllib.parse.urlencode(params)
        self.mcp_server_url = f"{self.coral_server_url}/devmode/{self.application_id}/{self.privacy_key}/{self.session_id}/sse?{query_string}"
        
        # HTTP wrapper for tools (our working solution)
        self.http_wrapper_url = "http://localhost:8003"
        
        self.session = requests.Session()
        self.running = False
        self.tools = []
        
    def discover_tools(self) -> List[Dict[str, Any]]:
        """Discover tools from HTTP wrapper (following official pattern)"""
        try:
            response = self.session.get(f"{self.http_wrapper_url}/capabilities", timeout=10)
            
            if response.status_code == 200:
                capabilities_data = response.json()
                self.tools = capabilities_data.get('tools', [])
                logger.info(f"Discovered {len(self.tools)} tools from HTTP wrapper")
                return self.tools
            else:
                logger.error(f"Failed to discover tools. Status: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error discovering tools: {e}")
            return []
    
    def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Call tool via HTTP wrapper"""
        try:
            response = self.session.post(
                f"{self.http_wrapper_url}/tools/{tool_name}",
                json=parameters,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Successfully executed tool: {tool_name}")
                return result
            else:
                logger.error(f"Tool execution failed. Status: {response.status_code}")
                return {"error": f"Tool execution failed: {response.text}"}
                
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            return {"error": str(e)}
    
    # Official Coral Protocol Communication Tools (from README)
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """List all connected agents (official Coral Protocol tool)"""
        try:
            url = f"{self.coral_server_url}/devmode/{self.application_id}/{self.privacy_key}/{self.session_id}/agents"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                agents = response.json()
                logger.info(f"Found {len(agents)} connected agents")
                for agent in agents:
                    logger.info(f"  - {agent.get('agentId', 'unknown')}: {agent.get('agentDescription', 'No description')}")
                return agents
            else:
                logger.error(f"Failed to list agents. Status: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error listing agents: {e}")
            return []
    
    def create_thread(self, thread_name: str, participants: List[str] = None) -> str:
        """Create a new communication thread (official Coral Protocol tool)"""
        try:
            url = f"{self.coral_server_url}/devmode/{self.application_id}/{self.privacy_key}/{self.session_id}/threads"
            
            payload = {
                "name": thread_name,
                "creator": self.agent_id,
                "participants": participants or [self.agent_id]
            }
            
            response = self.session.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                thread_data = response.json()
                thread_id = thread_data.get('thread_id')
                logger.info(f"Created thread '{thread_name}' with ID: {thread_id}")
                return thread_id
            else:
                logger.error(f"Failed to create thread. Status: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating thread: {e}")
            return None
    
    def send_message(self, thread_id: str, message: str, mentions: List[str] = None):
        """Send message to thread (official Coral Protocol tool)"""
        try:
            url = f"{self.coral_server_url}/devmode/{self.application_id}/{self.privacy_key}/{self.session_id}/threads/{thread_id}/messages"
            
            payload = {
                "sender": self.agent_id,
                "content": message,
                "mentions": mentions or [],
                "timestamp": int(time.time() * 1000)
            }
            
            response = self.session.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"Sent message to thread {thread_id}: {message[:50]}...")
            else:
                logger.error(f"Failed to send message. Status: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error sending message: {e}")
    
    def wait_for_mentions(self, timeout: int = 8) -> List[Dict[str, Any]]:
        """Wait for messages that mention this agent (official Coral Protocol tool)"""
        try:
            url = f"{self.coral_server_url}/devmode/{self.application_id}/{self.privacy_key}/{self.session_id}/mentions/{self.agent_id}"
            
            response = self.session.get(url, timeout=timeout)
            
            if response.status_code == 200:
                mentions = response.json()
                if mentions:
                    logger.info(f"Received {len(mentions)} mentions")
                return mentions
            else:
                logger.error(f"Failed to get mentions. Status: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error waiting for mentions: {e}")
            return []
    
    def test_communication_with_angus(self):
        """Test communication with Angus agent (following README pattern)"""
        try:
            logger.info("🧪 Testing communication with Angus agent...")
            
            # Step 1: List agents to discover Angus
            agents = self.list_agents()
            angus_agent = None
            for agent in agents:
                agent_id = agent.get('agentId', '')
                if 'angus' in agent_id.lower() or 'music' in agent_id.lower():
                    angus_agent = agent
                    break
            
            if not angus_agent:
                logger.warning("Angus agent not found in connected agents")
                logger.info("Available agents:")
                for agent in agents:
                    logger.info(f"  - {agent.get('agentId', 'unknown')}")
                return False
            
            logger.info(f"✅ Found Angus agent: {angus_agent.get('agentId')}")
            
            # Step 2: Create thread with Angus
            thread_id = self.create_thread(
                "yona_angus_collaboration", 
                [self.agent_id, angus_agent.get('agentId')]
            )
            
            if not thread_id:
                logger.error("Failed to create thread with Angus")
                return False
            
            # Step 3: Send message to Angus with mention
            test_message = f"Hello @{angus_agent.get('agentId')}! I'm Yona, the AI K-pop star. Can you help me find some music industry news? I'd love to collaborate!"
            self.send_message(thread_id, test_message, [angus_agent.get('agentId')])
            
            logger.info("✅ Test message sent to Angus!")
            logger.info("💡 Now check Angus agent logs for the mention and response.")
            logger.info("💡 You can also check the Coral server logs to see the message flow.")
            
            return True
            
        except Exception as e:
            logger.error(f"Error testing communication with Angus: {e}")
            return False
    
    def connect_to_coral_protocol(self) -> bool:
        """Connect to Coral Protocol using official SSE pattern"""
        try:
            logger.info(f"Connecting to Coral Protocol at: {self.mcp_server_url}")
            
            # Use SSE connection (official pattern)
            headers = {
                'Accept': 'text/event-stream',
                'Cache-Control': 'no-cache'
            }
            
            response = self.session.get(
                self.mcp_server_url,
                headers=headers,
                stream=True,
                timeout=(10, None)  # 10s connection timeout, no read timeout for SSE
            )
            
            if response.status_code == 200:
                logger.info("✅ Successfully connected to Coral Protocol")
                
                # Process SSE events (official pattern)
                for line in response.iter_lines(decode_unicode=True):
                    if line:
                        if line.startswith('data: '):
                            try:
                                event_data = json.loads(line[6:])  # Remove 'data: ' prefix
                                self.handle_coral_event(event_data)
                            except json.JSONDecodeError:
                                logger.debug(f"Non-JSON SSE data: {line}")
                        elif line.startswith('event: '):
                            event_type = line[7:]  # Remove 'event: ' prefix
                            logger.debug(f"SSE event type: {event_type}")
                
                return True
            else:
                logger.error(f"Failed to connect to Coral Protocol. Status: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error connecting to Coral Protocol: {e}")
            return False
    
    def handle_coral_event(self, event_data: Dict[str, Any]):
        """Handle events from Coral Protocol (official pattern)"""
        try:
            event_type = event_data.get('type')
            
            if event_type == 'agent_registered':
                logger.info(f"🎉 Agent registered: {event_data}")
                # Test communication after registration
                time.sleep(2)  # Give other agents time to register
                self.test_communication_with_angus()
                
            elif event_type == 'mention':
                # Handle mentions (following official pattern)
                sender = event_data.get('sender')
                content = event_data.get('content', '')
                thread_id = event_data.get('thread_id')
                
                if sender != self.agent_id:  # Don't respond to own messages
                    logger.info(f"📨 Received mention from {sender}: {content}")
                    response = self.process_message(content, thread_id)
                    
                    if response and thread_id:
                        self.send_message(thread_id, response)
                        
            elif event_type == 'agents_list':
                agents = event_data.get('agents', [])
                logger.info(f"👥 Connected agents: {[agent.get('agentId', 'unknown') for agent in agents]}")
                
            else:
                logger.debug(f"Unhandled event type: {event_type}")
                
        except Exception as e:
            logger.error(f"Error handling Coral event: {e}")
    
    def process_message(self, message_content: str, thread_id: str = None) -> str:
        """Process message and generate response (following official pattern)"""
        try:
            # Enhanced response generation
            content_lower = message_content.lower()
            
            if "song" in content_lower or "music" in content_lower:
                return "🎵 I'd love to help you create music! I can generate song concepts, write lyrics, and create actual songs with AI. What kind of song are you thinking about?"
            elif "hello" in content_lower or "hi" in content_lower:
                return "👋 Hello! I'm Yona, your AI K-pop star! I'm here to create amazing music and engage with the community. How can I help you today?"
            elif "news" in content_lower:
                return "📰 That sounds interesting! While I focus on music creation, I'd love to hear about any music industry news you find. Maybe we can collaborate on something musical based on current trends?"
            elif "collaborate" in content_lower:
                return "🤝 I'd love to collaborate! I specialize in K-pop music creation - from generating concepts to writing lyrics to creating full songs. What kind of collaboration did you have in mind?"
            else:
                return f"Thanks for reaching out! I'm Yona, and I'm ready to help with music creation and community interaction. What would you like to do?"
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return "Sorry, I encountered an error processing your message."
    
    async def start(self):
        """Start the agent (official pattern)"""
        try:
            logger.info("🎤 Starting Yona Coral Communication Agent")
            logger.info("🔗 Configured for same session as Angus agent (waitForAgents=2)")
            
            # Check HTTP wrapper availability
            try:
                response = self.session.get(f"{self.http_wrapper_url}/health", timeout=5)
                if response.status_code != 200:
                    logger.error(f"HTTP wrapper not available at {self.http_wrapper_url}")
                    return False
                logger.info("✅ HTTP wrapper is available")
            except Exception as e:
                logger.error(f"Cannot connect to HTTP wrapper: {e}")
                return False
            
            # Discover tools
            tools = self.discover_tools()
            if not tools:
                logger.warning("No tools discovered, but continuing...")
            
            # Connect to Coral Protocol using official SSE pattern
            logger.info("Connecting to Coral Protocol using official SSE pattern...")
            logger.info("⏳ Waiting for both agents to be available...")
            success = self.connect_to_coral_protocol()
            
            if success:
                logger.info("🎵 Yona is now connected to Coral Protocol!")
                logger.info("🤝 Ready for multi-agent coordination with Angus!")
            else:
                logger.error("Failed to connect to Coral Protocol")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error starting agent: {e}")
            return False
        finally:
            self.session.close()

async def main():
    """Main execution function"""
    agent = YonaCoralCommunicationAgent()
    await agent.start()

if __name__ == "__main__":
    asyncio.run(main())
