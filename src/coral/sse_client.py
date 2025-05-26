"""
SSE Client for Coral Server Integration
Handles real-time communication with Team Angus via Server-Sent Events
"""
import json
import time
import logging
import asyncio
from typing import Dict, Any, Optional, Callable
import requests
from sseclient import SSEClient
import threading

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CoralSSEClient:
    """
    SSE Client for connecting to Coral server and handling agent-to-agent communication
    """
    
    def __init__(self, agent_id: str = "yona_agent", 
                 agent_description: str = "Yona agent for creating songs and other creative content"):
        """
        Initialize the Coral SSE client
        
        Args:
            agent_id: Must be "yona_agent" for Team Angus compatibility
            agent_description: Description of the agent's capabilities
        """
        self.agent_id = agent_id
        self.agent_description = agent_description
        self.base_url = "http://coral.pushcollective.club:5555/devmode/exampleApplication/privkey/session1/sse"
        self.connected = False
        self.client = None
        self.message_handler = None
        self.heartbeat_thread = None
        self.listen_thread = None
        self.stop_event = threading.Event()
        
        logger.info(f"Initialized CoralSSEClient with agent_id: {self.agent_id}")
    
    def connect(self, message_handler: Callable[[Dict[str, Any]], None]) -> bool:
        """
        Connect to the Coral server
        
        Args:
            message_handler: Function to handle incoming messages
            
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.message_handler = message_handler
            
            # Connection parameters
            params = {
                "waitForAgents": 2,  # Wait for both agents (Angus + Yona)
                "agentId": self.agent_id,
                "agentDescription": self.agent_description
            }
            
            logger.info(f"Connecting to Coral server: {self.base_url}")
            logger.info(f"Parameters: {params}")
            
            # Create SSE client
            response = requests.get(self.base_url, params=params, stream=True)
            response.raise_for_status()
            
            self.client = SSEClient(response)
            self.connected = True
            
            # Start listening thread
            self.listen_thread = threading.Thread(target=self._listen_for_messages, daemon=True)
            self.listen_thread.start()
            
            # Start heartbeat thread
            self.heartbeat_thread = threading.Thread(target=self._heartbeat, daemon=True)
            self.heartbeat_thread.start()
            
            logger.info("Successfully connected to Coral server")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Coral server: {e}")
            self.connected = False
            return False
    
    def _listen_for_messages(self):
        """
        Listen for incoming SSE messages
        """
        try:
            logger.info("Started listening for messages...")
            
            for event in self.client.events():
                if self.stop_event.is_set():
                    break
                
                try:
                    # Parse the SSE event
                    if event.data:
                        logger.info(f"Received SSE event: {event.event}, data: {event.data}")
                        
                        # Parse JSON data
                        message_data = json.loads(event.data)
                        
                        # Handle the message
                        if self.message_handler:
                            self.message_handler(message_data)
                        
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse message JSON: {e}")
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    
        except Exception as e:
            logger.error(f"Error in message listening loop: {e}")
            self.connected = False
    
    def _heartbeat(self):
        """
        Send periodic heartbeat to maintain connection
        """
        while self.connected and not self.stop_event.is_set():
            try:
                # Send heartbeat every 30 seconds
                time.sleep(30)
                
                if self.connected:
                    heartbeat_data = {
                        "type": "heartbeat",
                        "agent_id": self.agent_id,
                        "timestamp": time.time()
                    }
                    logger.debug(f"Sending heartbeat: {heartbeat_data}")
                    
            except Exception as e:
                logger.error(f"Error in heartbeat: {e}")
    
    def send_response(self, function_name: str, result: Dict[str, Any], 
                     correlation_id: Optional[str] = None) -> bool:
        """
        Send a function response back to the Coral server
        
        Args:
            function_name: Name of the function that was called
            result: Result data to send back
            correlation_id: ID to correlate with original request
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            response_data = {
                "type": "function_response",
                "function": function_name,
                "result": result,
                "metadata": {
                    "sender": self.agent_id,
                    "timestamp": time.time(),
                    "correlation_id": correlation_id
                }
            }
            
            # For SSE, we typically send responses via a separate HTTP POST
            response_url = "http://coral.pushcollective.club:5555/devmode/exampleApplication/privkey/session1/response"
            
            response = requests.post(response_url, json=response_data, timeout=10)
            response.raise_for_status()
            
            logger.info(f"Successfully sent response for function: {function_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send response: {e}")
            return False
    
    def send_error_response(self, function_name: str, error_message: str, 
                           correlation_id: Optional[str] = None) -> bool:
        """
        Send an error response back to the Coral server
        
        Args:
            function_name: Name of the function that failed
            error_message: Error description
            correlation_id: ID to correlate with original request
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            error_data = {
                "type": "function_error",
                "function": function_name,
                "error": error_message,
                "metadata": {
                    "sender": self.agent_id,
                    "timestamp": time.time(),
                    "correlation_id": correlation_id
                }
            }
            
            response_url = "http://coral.pushcollective.club:5555/devmode/exampleApplication/privkey/session1/response"
            
            response = requests.post(response_url, json=error_data, timeout=10)
            response.raise_for_status()
            
            logger.info(f"Successfully sent error response for function: {function_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send error response: {e}")
            return False
    
    def disconnect(self):
        """
        Disconnect from the Coral server
        """
        logger.info("Disconnecting from Coral server...")
        
        self.connected = False
        self.stop_event.set()
        
        # Wait for threads to finish
        if self.listen_thread and self.listen_thread.is_alive():
            self.listen_thread.join(timeout=5)
        
        if self.heartbeat_thread and self.heartbeat_thread.is_alive():
            self.heartbeat_thread.join(timeout=5)
        
        if self.client:
            try:
                self.client.close()
            except:
                pass
        
        logger.info("Disconnected from Coral server")
    
    def is_connected(self) -> bool:
        """
        Check if currently connected to the server
        
        Returns:
            True if connected, False otherwise
        """
        return self.connected
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current connection status
        
        Returns:
            Dictionary with status information
        """
        return {
            "connected": self.connected,
            "agent_id": self.agent_id,
            "agent_description": self.agent_description,
            "server_url": self.base_url,
            "listen_thread_alive": self.listen_thread.is_alive() if self.listen_thread else False,
            "heartbeat_thread_alive": self.heartbeat_thread.is_alive() if self.heartbeat_thread else False
        }
