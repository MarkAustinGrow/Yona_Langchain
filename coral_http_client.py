#!/usr/bin/env python3
"""
Pure HTTP-based Coral Protocol Client
No MCP dependencies - uses only requests library
"""

import requests
import json
import time
import logging
from typing import Dict, List, Optional, Any
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

class CoralHttpClient:
    """Pure HTTP client for Coral Protocol communication"""
    
    def __init__(self, coral_server_url: str, application_id: str = "exampleApplication", 
                 privacy_key: str = "privkey", session_id: str = "session1"):
        self.coral_server_url = coral_server_url.rstrip('/')
        self.application_id = application_id
        self.privacy_key = privacy_key
        self.session_id = session_id
        self.agent_id = None
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def register_agent(self, agent_id: str, agent_description: str, wait_for_agents: int = 1) -> bool:
        """Register agent with Coral Protocol"""
        try:
            self.agent_id = agent_id
            
            # Build registration URL
            params = {
                "waitForAgents": wait_for_agents,
                "agentId": agent_id,
                "agentDescription": agent_description
            }
            query_string = urlencode(params)
            registration_url = f"{self.coral_server_url}/devmode/{self.application_id}/{self.privacy_key}/{self.session_id}/register?{query_string}"
            
            logger.info(f"Registering agent '{agent_id}' with Coral Protocol")
            logger.info(f"Registration URL: {registration_url}")
            
            response = self.session.post(registration_url, timeout=30)
            
            if response.status_code == 200:
                logger.info(f"Successfully registered agent: {agent_id}")
                return True
            else:
                logger.error(f"Failed to register agent. Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error registering agent: {e}")
            return False
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """List all connected agents in the session"""
        try:
            url = f"{self.coral_server_url}/devmode/{self.application_id}/{self.privacy_key}/{self.session_id}/agents"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                agents = response.json()
                logger.info(f"Found {len(agents)} connected agents")
                return agents
            else:
                logger.error(f"Failed to list agents. Status: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error listing agents: {e}")
            return []
    
    def create_thread(self, thread_name: str, participants: List[str] = None) -> Optional[str]:
        """Create a new communication thread"""
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
    
    def send_message(self, thread_id: str, message: str, mentions: List[str] = None) -> bool:
        """Send a message in a thread"""
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
                logger.info(f"Sent message to thread {thread_id}")
                return True
            else:
                logger.error(f"Failed to send message. Status: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    def get_messages(self, thread_id: str, since: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get messages from a thread"""
        try:
            url = f"{self.coral_server_url}/devmode/{self.application_id}/{self.privacy_key}/{self.session_id}/threads/{thread_id}/messages"
            
            params = {}
            if since:
                params['since'] = since
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                messages = response.json()
                logger.info(f"Retrieved {len(messages)} messages from thread {thread_id}")
                return messages
            else:
                logger.error(f"Failed to get messages. Status: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting messages: {e}")
            return []
    
    def wait_for_mentions(self, timeout: int = 30) -> List[Dict[str, Any]]:
        """Wait for messages that mention this agent"""
        try:
            url = f"{self.coral_server_url}/devmode/{self.application_id}/{self.privacy_key}/{self.session_id}/mentions/{self.agent_id}"
            
            response = self.session.get(url, timeout=timeout)
            
            if response.status_code == 200:
                mentions = response.json()
                logger.info(f"Received {len(mentions)} mentions")
                return mentions
            else:
                logger.error(f"Failed to get mentions. Status: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error waiting for mentions: {e}")
            return []
    
    def heartbeat(self) -> bool:
        """Send heartbeat to maintain connection"""
        try:
            url = f"{self.coral_server_url}/devmode/{self.application_id}/{self.privacy_key}/{self.session_id}/agents/{self.agent_id}/heartbeat"
            
            response = self.session.post(url, timeout=5)
            
            if response.status_code == 200:
                return True
            else:
                logger.warning(f"Heartbeat failed. Status: {response.status_code}")
                return False
                
        except Exception as e:
            logger.warning(f"Heartbeat error: {e}")
            return False
    
    def close(self):
        """Close the HTTP session"""
        if self.session:
            self.session.close()
