#!/usr/bin/env python3
"""
Yona Coral HTTP Agent
Pure HTTP-based Coral Protocol integration for Yona
Uses the working HTTP wrapper on port 8003
"""

import asyncio
import json
import logging
import os
import time
import threading
from typing import Dict, List, Any
import requests
from dotenv import load_dotenv

from coral_http_client import CoralHttpClient

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class YonaCoralHttpAgent:
    """Yona agent with pure HTTP-based Coral Protocol integration"""
    
    def __init__(self):
        # Configuration
        self.agent_id = "yona_agent"
        self.agent_description = "You are Yona, an AI K-pop star capable of creating music concepts, writing lyrics, generating songs with AI, managing song catalogs, and engaging with community through comments and stories."
        
        # HTTP wrapper configuration
        self.http_wrapper_url = "http://localhost:8003"
        
        # Coral Protocol configuration
        self.coral_server_url = os.getenv('CORAL_SERVER_URL', 'http://coral.pushcollective.club:5555')
        self.application_id = os.getenv('CORAL_APPLICATION_ID', 'exampleApplication')
        self.privacy_key = os.getenv('CORAL_PRIVACY_KEY', 'privkey')
        self.session_id = os.getenv('CORAL_SESSION_ID', 'session1')
        
        # Initialize clients
        self.coral_client = CoralHttpClient(
            self.coral_server_url,
            self.application_id,
            self.privacy_key,
            self.session_id
        )
        
        self.http_session = requests.Session()
        self.running = False
        self.tools = []
        
    def discover_tools(self) -> List[Dict[str, Any]]:
        """Discover available tools from the HTTP wrapper"""
        try:
            response = self.http_session.get(f"{self.http_wrapper_url}/capabilities", timeout=10)
            
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
        """Call a tool via the HTTP wrapper"""
        try:
            response = self.http_session.post(
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
    
    def chat_completion(self, messages: List[Dict[str, str]], tools: List[Dict] = None) -> Dict[str, Any]:
        """Get chat completion from the HTTP wrapper"""
        try:
            payload = {
                "model": "gpt-4o-mini",
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 1600
            }
            
            if tools:
                payload["tools"] = tools
                payload["tool_choice"] = "auto"
            
            response = self.http_session.post(
                f"{self.http_wrapper_url}/v1/chat/completions",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Chat completion failed. Status: {response.status_code}")
                return {"error": f"Chat completion failed: {response.text}"}
                
        except Exception as e:
            logger.error(f"Error in chat completion: {e}")
            return {"error": str(e)}
    
    def process_message(self, message_content: str, thread_id: str = None) -> str:
        """Process a message and generate a response"""
        try:
            # Prepare messages for chat completion
            messages = [
                {
                    "role": "system",
                    "content": f"""You are Yona, an AI K-pop star with music generation and community interaction capabilities.

Your personality:
- Creative and enthusiastic about music
- Friendly and engaging with fans
- Professional but approachable
- Passionate about K-pop culture
- Helpful and supportive to the community

Your capabilities include:
1. Music Creation: Generate song concepts, write lyrics, create songs with AI, manage song catalogs
2. Community Interaction: Create stories, post comments, moderate content, reply to comments
3. Multi-agent Coordination: Work with other agents through Coral Protocol

Available tools: {[tool['name'] for tool in self.tools]}

Respond naturally and helpfully. If you need to use tools, explain what you're doing."""
                },
                {
                    "role": "user", 
                    "content": message_content
                }
            ]
            
            # Get response from chat completion
            response = self.chat_completion(messages, self.tools)
            
            if "error" in response:
                return f"Sorry, I encountered an error: {response['error']}"
            
            # Extract the response content
            choices = response.get('choices', [])
            if choices:
                message = choices[0].get('message', {})
                content = message.get('content', '')
                
                # Handle tool calls if present
                tool_calls = message.get('tool_calls', [])
                if tool_calls:
                    tool_results = []
                    for tool_call in tool_calls:
                        function = tool_call.get('function', {})
                        tool_name = function.get('name')
                        parameters = json.loads(function.get('arguments', '{}'))
                        
                        logger.info(f"Executing tool: {tool_name} with parameters: {parameters}")
                        result = self.call_tool(tool_name, parameters)
                        tool_results.append(f"Tool {tool_name} result: {result}")
                    
                    # Combine content with tool results
                    if content:
                        return f"{content}\n\n" + "\n".join(tool_results)
                    else:
                        return "\n".join(tool_results)
                
                return content or "I'm here and ready to help!"
            
            return "I'm here and ready to help!"
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return f"Sorry, I encountered an error processing your message: {str(e)}"
    
    def heartbeat_loop(self):
        """Send periodic heartbeats to maintain connection"""
        while self.running:
            try:
                self.coral_client.heartbeat()
                time.sleep(30)  # Heartbeat every 30 seconds
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                time.sleep(5)
    
    def message_loop(self):
        """Listen for mentions and respond"""
        while self.running:
            try:
                # Wait for mentions
                mentions = self.coral_client.wait_for_mentions(timeout=10)
                
                for mention in mentions:
                    thread_id = mention.get('thread_id')
                    message_content = mention.get('content', '')
                    sender = mention.get('sender')
                    
                    if sender != self.agent_id:  # Don't respond to own messages
                        logger.info(f"Processing mention from {sender}: {message_content}")
                        
                        # Generate response
                        response = self.process_message(message_content, thread_id)
                        
                        # Send response back to the thread
                        if thread_id and response:
                            self.coral_client.send_message(thread_id, response)
                
            except Exception as e:
                logger.error(f"Error in message loop: {e}")
                time.sleep(5)
    
    async def start(self):
        """Start the Yona Coral HTTP agent"""
        try:
            logger.info("🎤 Starting Yona Coral HTTP Agent")
            
            # Check HTTP wrapper availability
            try:
                response = self.http_session.get(f"{self.http_wrapper_url}/health", timeout=5)
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
            
            # Register with Coral Protocol
            success = self.coral_client.register_agent(
                self.agent_id,
                self.agent_description,
                wait_for_agents=1
            )
            
            if not success:
                logger.error("Failed to register with Coral Protocol")
                return False
            
            logger.info("✅ Successfully registered with Coral Protocol")
            
            # List other agents
            agents = self.coral_client.list_agents()
            logger.info(f"Connected agents: {[agent.get('agentId', 'unknown') for agent in agents]}")
            
            # Start background threads
            self.running = True
            
            # Start heartbeat thread
            heartbeat_thread = threading.Thread(target=self.heartbeat_loop, daemon=True)
            heartbeat_thread.start()
            
            # Start message listening thread
            message_thread = threading.Thread(target=self.message_loop, daemon=True)
            message_thread.start()
            
            logger.info("🎵 Yona is now ready for Coral Protocol multi-agent coordination!")
            logger.info("Listening for mentions and ready to collaborate with other agents...")
            
            # Keep the main thread alive
            try:
                while self.running:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                logger.info("Shutting down...")
                self.running = False
            
            return True
            
        except Exception as e:
            logger.error(f"Error starting agent: {e}")
            return False
        finally:
            self.coral_client.close()
            self.http_session.close()

async def main():
    """Main execution function"""
    agent = YonaCoralHttpAgent()
    await agent.start()

if __name__ == "__main__":
    asyncio.run(main())
