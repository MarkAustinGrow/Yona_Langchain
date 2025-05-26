"""
Message Processor for Coral Server Integration
Handles function calls from Team Angus and routes them to appropriate Yona tools
"""
import json
import logging
from typing import Dict, Any, Optional
from ..agents.yona_agent import YonaLangChainAgent

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CoralMessageProcessor:
    """
    Processes incoming function calls from Team Angus and routes them to Yona's capabilities
    """
    
    def __init__(self, yona_agent: YonaLangChainAgent):
        """
        Initialize the message processor
        
        Args:
            yona_agent: The YonaLangChainAgent instance to use for processing
        """
        self.yona_agent = yona_agent
        self.supported_functions = {
            "create_song": self._handle_create_song,
            "list_songs": self._handle_list_songs,
            "get_song": self._handle_get_song,
            "search_songs": self._handle_search_songs
        }
        
        logger.info(f"Initialized CoralMessageProcessor with {len(self.supported_functions)} supported functions")
    
    def process_message(self, message_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process an incoming message from Team Angus
        
        Args:
            message_data: The message data received from Coral server
            
        Returns:
            Response data to send back, or None if no response needed
        """
        try:
            message_type = message_data.get("type")
            
            if message_type == "function_call":
                return self._handle_function_call(message_data)
            elif message_type == "heartbeat":
                return self._handle_heartbeat(message_data)
            elif message_type == "agent_discovery":
                return self._handle_agent_discovery(message_data)
            else:
                logger.warning(f"Unknown message type: {message_type}")
                return None
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                "type": "error",
                "error": str(e),
                "original_message": message_data
            }
    
    def _handle_function_call(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a function call from Team Angus
        
        Args:
            message_data: Function call message data
            
        Returns:
            Function response data
        """
        try:
            function_name = message_data.get("function")
            arguments = message_data.get("arguments", {})
            metadata = message_data.get("metadata", {})
            correlation_id = metadata.get("message_id")
            
            logger.info(f"Processing function call: {function_name} with args: {arguments}")
            
            if function_name not in self.supported_functions:
                error_msg = f"Unsupported function: {function_name}. Supported functions: {list(self.supported_functions.keys())}"
                logger.error(error_msg)
                return {
                    "type": "function_error",
                    "function": function_name,
                    "error": error_msg,
                    "correlation_id": correlation_id
                }
            
            # Call the appropriate handler
            handler = self.supported_functions[function_name]
            result = handler(arguments)
            
            return {
                "type": "function_response",
                "function": function_name,
                "result": result,
                "metadata": {
                    "sender": "yona_agent",
                    "correlation_id": correlation_id
                }
            }
            
        except Exception as e:
            logger.error(f"Error handling function call: {e}")
            return {
                "type": "function_error",
                "function": message_data.get("function", "unknown"),
                "error": str(e),
                "correlation_id": message_data.get("metadata", {}).get("message_id")
            }
    
    def _handle_create_song(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle create_song function call
        
        Args:
            arguments: Function arguments from Team Angus
            
        Returns:
            Song creation result
        """
        try:
            prompt = arguments.get("prompt", "")
            if not prompt:
                raise ValueError("Missing required argument: prompt")
            
            logger.info(f"Creating song with prompt: {prompt}")
            
            # Use Yona's agent to create the song
            request = f"Create a song based on this prompt: {prompt}"
            response = self.yona_agent.process_request(request)
            
            # Parse the response to extract song details
            # Note: This is a simplified version - in practice, you might want to
            # parse the actual JSON response from the create_song tool
            result = {
                "title": f"Song for Team Angus",
                "prompt": prompt,
                "response": response,
                "status": "completed",
                "created_by": "yona_agent"
            }
            
            logger.info(f"Successfully created song: {result['title']}")
            return result
            
        except Exception as e:
            logger.error(f"Error creating song: {e}")
            raise
    
    def _handle_list_songs(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle list_songs function call
        
        Args:
            arguments: Function arguments
            
        Returns:
            List of songs
        """
        try:
            limit = arguments.get("limit", 10)
            
            logger.info(f"Listing songs with limit: {limit}")
            
            # Use Yona's agent to list songs
            request = f"List the {limit} most recent songs"
            response = self.yona_agent.process_request(request)
            
            result = {
                "songs": response,
                "limit": limit,
                "status": "completed"
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error listing songs: {e}")
            raise
    
    def _handle_get_song(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle get_song function call
        
        Args:
            arguments: Function arguments
            
        Returns:
            Song details
        """
        try:
            song_id = arguments.get("song_id")
            if not song_id:
                raise ValueError("Missing required argument: song_id")
            
            logger.info(f"Getting song with ID: {song_id}")
            
            # Use Yona's agent to get the song
            request = f"Get details for song ID: {song_id}"
            response = self.yona_agent.process_request(request)
            
            result = {
                "song_id": song_id,
                "details": response,
                "status": "completed"
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting song: {e}")
            raise
    
    def _handle_search_songs(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle search_songs function call
        
        Args:
            arguments: Function arguments
            
        Returns:
            Search results
        """
        try:
            query = arguments.get("query", "")
            if not query:
                raise ValueError("Missing required argument: query")
            
            limit = arguments.get("limit", 10)
            
            logger.info(f"Searching songs with query: {query}, limit: {limit}")
            
            # Use Yona's agent to search songs
            request = f"Search for songs matching: {query}, limit {limit} results"
            response = self.yona_agent.process_request(request)
            
            result = {
                "query": query,
                "results": response,
                "limit": limit,
                "status": "completed"
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error searching songs: {e}")
            raise
    
    def _handle_heartbeat(self, message_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Handle heartbeat message
        
        Args:
            message_data: Heartbeat message data
            
        Returns:
            Heartbeat response or None
        """
        logger.debug("Received heartbeat from Team Angus")
        
        # Respond with our own heartbeat
        return {
            "type": "heartbeat_response",
            "agent_id": "yona_agent",
            "status": "alive",
            "capabilities": list(self.supported_functions.keys())
        }
    
    def _handle_agent_discovery(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle agent discovery message
        
        Args:
            message_data: Discovery message data
            
        Returns:
            Agent capabilities response
        """
        logger.info("Received agent discovery request")
        
        return {
            "type": "agent_info",
            "agent_id": "yona_agent",
            "description": "Yona agent for creating songs and other creative content",
            "capabilities": {
                "functions": list(self.supported_functions.keys()),
                "description": {
                    "create_song": "Create a new song based on a text prompt",
                    "list_songs": "List recent songs from the database",
                    "get_song": "Get details for a specific song by ID",
                    "search_songs": "Search songs by title or lyrics"
                }
            },
            "status": "ready"
        }
    
    def get_supported_functions(self) -> list:
        """
        Get list of supported function names
        
        Returns:
            List of function names
        """
        return list(self.supported_functions.keys())
