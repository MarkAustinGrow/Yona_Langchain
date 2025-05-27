#!/usr/bin/env python3
"""
Test script for Yona MCP Server
Validates that all tools are properly exposed and functional
"""
import subprocess
import json
import time
import logging
import sys
from typing import Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_mcp_server_startup():
    """Test that the MCP server starts without errors"""
    try:
        logger.info("Testing MCP server startup...")
        
        # Start the MCP server as a subprocess
        process = subprocess.Popen(
            [sys.executable, "yona_mcp_server.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Give it a moment to start
        time.sleep(2)
        
        # Check if process is still running
        if process.poll() is None:
            logger.info("✅ MCP server started successfully")
            process.terminate()
            process.wait()
            return True
        else:
            stdout, stderr = process.communicate()
            logger.error(f"❌ MCP server failed to start")
            logger.error(f"STDOUT: {stdout}")
            logger.error(f"STDERR: {stderr}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error testing MCP server startup: {e}")
        return False

def test_tool_imports():
    """Test that all tools can be imported successfully"""
    try:
        logger.info("Testing tool imports...")
        
        # Test Yona tools import
        from src.tools.yona_tools import (
            generate_song_concept,
            generate_lyrics,
            create_song,
            list_songs,
            get_song_by_id,
            search_songs,
            process_feedback
        )
        
        # Test Coral tools import
        from src.tools.coral_tools import (
            post_comment,
            get_story_comments,
            create_story,
            moderate_comment,
            get_story_by_url,
            reply_to_comment
        )
        
        logger.info("✅ All tools imported successfully")
        
        # Test tool properties
        all_tools = [
            generate_song_concept, generate_lyrics, create_song,
            list_songs, get_song_by_id, search_songs, process_feedback,
            post_comment, get_story_comments, create_story,
            moderate_comment, get_story_by_url, reply_to_comment
        ]
        
        for tool in all_tools:
            assert hasattr(tool, 'name'), f"Tool {tool} missing name attribute"
            assert hasattr(tool, 'description'), f"Tool {tool} missing description attribute"
            logger.info(f"  ✅ {tool.name}: {tool.description[:50]}...")
        
        logger.info(f"✅ All {len(all_tools)} tools validated")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error testing tool imports: {e}")
        return False

def test_environment_setup():
    """Test that required environment variables and dependencies are available"""
    try:
        logger.info("Testing environment setup...")
        
        # Test core imports
        import langchain
        import openai
        from src.core.config import OPENAI_KEY, YONA_PERSONA
        
        logger.info("✅ Core dependencies available")
        
        # Test configuration
        assert OPENAI_KEY, "OPENAI_KEY not configured"
        assert YONA_PERSONA, "YONA_PERSONA not configured"
        
        logger.info("✅ Configuration validated")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error testing environment: {e}")
        return False

def test_mcp_toolkit_compatibility():
    """Test MCP toolkit compatibility (if available)"""
    try:
        logger.info("Testing MCP toolkit compatibility...")
        
        # Try to import MCP components
        try:
            from langchain_mcp import MCPToolkit
            logger.info("✅ langchain_mcp available")
        except ImportError:
            logger.warning("⚠️ langchain_mcp not available - install with: pip install langchain-mcp")
            return False
        
        try:
            from langchain.tools.mcp import mcp_server
            logger.info("✅ langchain.tools.mcp available")
        except ImportError:
            logger.warning("⚠️ langchain.tools.mcp not available")
            return False
        
        logger.info("✅ MCP toolkit compatibility confirmed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error testing MCP toolkit: {e}")
        return False

def run_all_tests():
    """Run all tests and report results"""
    logger.info("🧪 Starting Yona MCP Server Tests")
    logger.info("=" * 50)
    
    tests = [
        ("Environment Setup", test_environment_setup),
        ("Tool Imports", test_tool_imports),
        ("MCP Toolkit Compatibility", test_mcp_toolkit_compatibility),
        ("MCP Server Startup", test_mcp_server_startup),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n🔍 Running: {test_name}")
        try:
            result = test_func()
            results[test_name] = result
            if result:
                logger.info(f"✅ {test_name}: PASSED")
            else:
                logger.error(f"❌ {test_name}: FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name}: ERROR - {e}")
            results[test_name] = False
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("📊 TEST SUMMARY")
    logger.info("=" * 50)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status}: {test_name}")
    
    logger.info(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Yona MCP Server is ready.")
        return True
    else:
        logger.error("⚠️ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
