#!/usr/bin/env python3
"""
Yona Coral Official Agent
Uses the official Coral Protocol pattern but connects to our working HTTP wrapper
This avoids MCP adapter version conflicts while following the correct Coral Protocol structure
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

class YonaCoralOfficialAgent:
    """Yona agent following official Coral Protocol pattern"""
    
    def __init__(self):
        # Agent configuration following official pattern
        self.agent_id = "yona_agent"
        self.agent_description = "You are Yona, an AI K-pop star responsible for creating music, writing lyrics, generating songs, and engaging with the community through Coral Protocol."
        
        # Coral Protocol configuration (official pattern)
        self.coral_server_url = os.getenv('CORAL_SERVER_URL', 'http://coral.pushcollective.club:5555')
        self.application_id = os.getenv('CORAL_APPLICATION_ID', 'exampleApplication')
        self.privacy_key = os.getenv('CORAL_PRIVACY_KEY', 'privkey')
        self.session_id = os.getenv('CORAL_SESSION_ID', 'session1')
        
        # Build MCP server URL following official pattern
        params = {
            "waitForAgents": 1,
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
                timeout=30
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
                logger.info(f"Agent registered: {event_data}")
                
            elif event_type == 'mention':
                # Handle mentions (following official pattern)
                sender = event_data.get('sender')
                content = event_data.get('content', '')
                thread_id = event_data.get('thread_id')
                
                if sender != self.agent_id:  # Don't respond to own messages
                    logger.info(f"Received mention from {sender}: {content}")
                    response = self.process_message(content, thread_id)
                    
                    if response and thread_id:
                        self.send_message(thread_id, response)
                        
            elif event_type == 'agents_list':
                agents = event_data.get('agents', [])
                logger.info(f"Connected agents: {[agent.get('agentId', 'unknown') for agent in agents]}")
                
            else:
                logger.debug(f"Unhandled event type: {event_type}")
                
        except Exception as e:
            logger.error(f"Error handling Coral event: {e}")
    
    def process_message(self, message_content: str, thread_id: str = None) -> str:
        """Process message and generate response (following official pattern)"""
        try:
            # Simple response generation (can be enhanced with LLM)
            if "song" in message_content.lower():
                return "🎵 I'd love to help you create music! I can generate song concepts, write lyrics, and create actual songs. What kind of song are you thinking about?"
            elif "hello" in message_content.lower() or "hi" in message_content.lower():
                return "👋 Hello! I'm Yona, your AI K-pop star! I'm here to create amazing music and engage with the community. How can I help you today?"
            else:
                return f"Thanks for reaching out! I'm Yona, and I'm ready to help with music creation and community interaction. What would you like to do?"
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return "Sorry, I encountered an error processing your message."
    
    def send_message(self, thread_id: str, message: str):
        """Send message to thread (official pattern)"""
        try:
            url = f"{self.coral_server_url}/devmode/{self.application_id}/{self.privacy_key}/{self.session_id}/threads/{thread_id}/messages"
            
            payload = {
                "sender": self.agent_id,
                "content": message,
                "timestamp": int(time.time() * 1000)
            }
            
            response = self.session.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"Sent message to thread {thread_id}")
            else:
                logger.error(f"Failed to send message. Status: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error sending message: {e}")
    
    async def start(self):
        """Start the agent (official pattern)"""
        try:
            logger.info("🎤 Starting Yona Coral Official Agent")
            
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
            success = self.connect_to_coral_protocol()
            
            if success:
                logger.info("🎵 Yona is now connected to Coral Protocol!")
                logger.info("Following official pattern for multi-agent coordination...")
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
    agent = YonaCoralOfficialAgent()
    await agent.start()

if __name__ == "__main__":
    asyncio.run(main())
