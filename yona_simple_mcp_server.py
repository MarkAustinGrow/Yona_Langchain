#!/usr/bin/env python3
"""
Simple MCP Server for Yona Tools
Provides MCP-compatible STDIO interface without langchain-mcp dependency
"""

import sys
import json
import logging
from typing import Dict, Any, List
from src.tools.yona_tools import (
    generate_song_concept, generate_lyrics, create_song,
    list_songs, get_song_by_id, search_songs, process_feedback
)
from src.tools.coral_tools import (
    post_comment, get_story_comments, create_story,
    moderate_comment, get_story_by_url, reply_to_comment
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleMCPServer:
    def __init__(self):
        """Initialize the simple MCP server with Yona tools."""
        self.tools = {}
        self._load_tools()
        
    def _load_tools(self):
        """Load all Yona and Coral tools."""
        try:
            # Explicitly load all tools
            all_tools = [
                # Yona tools
                generate_song_concept, generate_lyrics, create_song,
                list_songs, get_song_by_id, search_songs, process_feedback,
                # Coral tools
                post_comment, get_story_comments, create_story,
                moderate_comment, get_story_by_url, reply_to_comment
            ]
            
            for tool in all_tools:
                self.tools[tool.name] = tool
                
            logger.info(f"Loaded {len(self.tools)} tools: {list(self.tools.keys())}")
            
        except Exception as e:
            logger.error(f"Error loading tools: {e}")
            
    def list_tools(self) -> List[Dict[str, Any]]:
        """Return list of available tools in MCP format."""
        tools_list = []
        for name, tool in self.tools.items():
            # Handle LangChain tool schema properly
            input_schema = {"type": "object", "properties": {}, "required": []}
            
            if hasattr(tool, 'args_schema') and tool.args_schema:
                try:
                    # If args_schema is a Pydantic model, get its schema
                    if hasattr(tool.args_schema, 'schema'):
                        schema = tool.args_schema.schema()
                        input_schema["properties"] = schema.get('properties', {})
                        input_schema["required"] = schema.get('required', [])
                    elif hasattr(tool.args_schema, '__fields__'):
                        # Handle Pydantic v1 style
                        properties = {}
                        required = []
                        for field_name, field in tool.args_schema.__fields__.items():
                            properties[field_name] = {
                                "type": "string",  # Default to string
                                "description": field.field_info.description or ""
                            }
                            if field.required:
                                required.append(field_name)
                        input_schema["properties"] = properties
                        input_schema["required"] = required
                except Exception:
                    # Fallback to basic schema
                    pass
            
            tools_list.append({
                "name": name,
                "description": tool.description,
                "inputSchema": input_schema
            })
        return tools_list
        
    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool with given arguments."""
        if name not in self.tools:
            return {"error": f"Tool '{name}' not found"}
            
        try:
            tool = self.tools[name]
            result = tool.run(arguments)
            return {"content": [{"type": "text", "text": str(result)}]}
            
        except Exception as e:
            logger.error(f"Error executing tool {name}: {e}")
            return {"error": str(e)}
            
    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP request."""
        method = request.get("method")
        params = request.get("params", {})
        
        if method == "tools/list":
            return {
                "tools": self.list_tools()
            }
            
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            return self.call_tool(tool_name, arguments)
            
        else:
            return {"error": f"Unknown method: {method}"}
            
    def run(self):
        """Run the MCP server in STDIO mode."""
        logger.info("🚀 Starting Yona Simple MCP Server")
        logger.info(f"📋 Available tools: {list(self.tools.keys())}")
        
        # Send ready signal
        print(json.dumps({"jsonrpc": "2.0", "method": "initialized"}), flush=True)
        
        try:
            for line in sys.stdin:
                line = line.strip()
                if not line:
                    continue
                    
                try:
                    request = json.loads(line)
                    response = self.handle_request(request)
                    
                    # Add jsonrpc and id to response
                    if "id" in request:
                        response["id"] = request["id"]
                    response["jsonrpc"] = "2.0"
                    
                    print(json.dumps(response), flush=True)
                    
                except json.JSONDecodeError as e:
                    error_response = {
                        "jsonrpc": "2.0",
                        "error": {"code": -32700, "message": f"Parse error: {e}"}
                    }
                    print(json.dumps(error_response), flush=True)
                    
                except Exception as e:
                    logger.error(f"Error handling request: {e}")
                    error_response = {
                        "jsonrpc": "2.0", 
                        "error": {"code": -32603, "message": f"Internal error: {e}"}
                    }
                    print(json.dumps(error_response), flush=True)
                    
        except KeyboardInterrupt:
            logger.info("🛑 Server stopped by user")
        except Exception as e:
            logger.error(f"Server error: {e}")

def main():
    """Main entry point."""
    server = SimpleMCPServer()
    server.run()

if __name__ == "__main__":
    main()
