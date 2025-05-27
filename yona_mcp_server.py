#!/usr/bin/env python3
"""
Yona MCP Server - STDIO Implementation
Exposes Yona's music generation and community tools via Model Context Protocol
"""
import sys
import logging
from typing import List
from langchain.tools.mcp import mcp_server

# Import all Yona tools
from src.tools.yona_tools import (
    generate_song_concept,
    generate_lyrics,
    create_song,
    list_songs,
    get_song_by_id,
    search_songs,
    process_feedback
)

from src.tools.coral_tools import (
    post_comment,
    get_story_comments,
    create_story,
    moderate_comment,
    get_story_by_url,
    reply_to_comment
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('yona_mcp_server.log'),
        logging.StreamHandler(sys.stderr)  # Use stderr to avoid interfering with STDIO protocol
    ]
)
logger = logging.getLogger(__name__)

def main():
    """
    Main entry point for Yona MCP Server
    Serves all 13 Yona tools via STDIO MCP protocol
    """
    try:
        logger.info("Starting Yona MCP Server...")
        
        # Collect all tools
        all_tools = [
            # Music generation tools
            generate_song_concept,
            generate_lyrics,
            create_song,
            list_songs,
            get_song_by_id,
            search_songs,
            process_feedback,
            
            # Community interaction tools
            post_comment,
            get_story_comments,
            create_story,
            moderate_comment,
            get_story_by_url,
            reply_to_comment
        ]
        
        logger.info(f"Loaded {len(all_tools)} tools for MCP server")
        for tool in all_tools:
            logger.info(f"  - {tool.name}: {tool.description}")
        
        # Start MCP server via STDIO
        logger.info("Starting MCP server via STDIO...")
        mcp_server(all_tools)
        
    except Exception as e:
        logger.error(f"Error starting Yona MCP Server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
