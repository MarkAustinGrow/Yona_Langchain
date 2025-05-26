"""
Test script for Yona LangChain Agent
Simple test to verify the agent is working correctly
"""
import os
import sys
from dotenv import load_dotenv

# Add src to path for imports
sys.path.append('src')

# Load environment variables
load_dotenv()

def test_agent_initialization():
    """Test that the agent can be initialized without errors"""
    try:
        from src.agents.yona_agent import create_yona_agent
        
        print("🧪 Testing Yona LangChain Agent initialization...")
        
        # Create agent with minimal verbosity for testing
        agent = create_yona_agent(temperature=0.7, verbose=False)
        
        print("✅ Agent initialized successfully!")
        
        # Test capabilities
        capabilities = agent.get_capabilities()
        print(f"📋 Agent capabilities: {len(capabilities['tools'])} tools available")
        print(f"🎤 Agent name: {capabilities['agent']}")
        print(f"🔧 Framework: {capabilities['framework']}")
        
        return agent
        
    except Exception as e:
        print(f"❌ Error initializing agent: {e}")
        return None

def test_simple_request(agent):
    """Test a simple request to the agent"""
    try:
        print("\n🧪 Testing simple request...")
        
        # Test a simple greeting
        response = agent.process_request("Hello! Can you tell me about yourself?")
        
        print("✅ Simple request successful!")
        print(f"📝 Response preview: {response[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error with simple request: {e}")
        return False

def test_tool_availability():
    """Test that all tools are properly imported and available"""
    try:
        print("\n🧪 Testing tool availability...")
        
        # Test Yona tools
        from src.tools.yona_tools import (
            generate_song_concept, generate_lyrics, create_song,
            list_songs, get_song_by_id, search_songs
        )
        print("✅ Yona tools imported successfully")
        
        # Test Coral tools
        from src.tools.coral_tools import (
            post_comment, get_story_comments, create_story,
            moderate_comment, get_story_by_url, reply_to_comment
        )
        print("✅ Coral tools imported successfully")
        
        # Test core modules
        from src.core.config import YONA_PERSONA, CORAL_SERVER_URL
        from src.core.music_api import MusicAPI
        from src.core.supabase_client import SupabaseClient
        print("✅ Core modules imported successfully")
        
        print(f"🎤 Yona persona: {YONA_PERSONA['name']}")
        print(f"🌐 Coral server: {CORAL_SERVER_URL}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error importing tools: {e}")
        return False

def test_environment_variables():
    """Test that required environment variables are available"""
    try:
        print("\n🧪 Testing environment variables...")
        
        required_vars = [
            'OPENAI_KEY',
            'MUSICAPI_KEY',
            'SUPABASE_URL', 
            'SUPABASE_KEY'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"⚠️  Missing environment variables: {', '.join(missing_vars)}")
            print("💡 Note: Some features may not work without proper environment variables")
            return False
        else:
            print("✅ All required environment variables are set")
            return True
            
    except Exception as e:
        print(f"❌ Error checking environment variables: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Yona LangChain Agent Tests")
    print("=" * 50)
    
    # Test environment variables
    env_ok = test_environment_variables()
    
    # Test tool imports
    tools_ok = test_tool_availability()
    
    # Test agent initialization
    agent = test_agent_initialization()
    
    if agent and env_ok:
        # Test simple request
        request_ok = test_simple_request(agent)
        
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        print(f"Environment Variables: {'✅ PASS' if env_ok else '⚠️  PARTIAL'}")
        print(f"Tool Imports: {'✅ PASS' if tools_ok else '❌ FAIL'}")
        print(f"Agent Initialization: {'✅ PASS' if agent else '❌ FAIL'}")
        print(f"Simple Request: {'✅ PASS' if request_ok else '❌ FAIL'}")
        
        if agent and tools_ok and request_ok:
            print("\n🎉 All tests passed! Yona LangChain Agent is ready!")
            print("\n💡 To run interactive mode, use:")
            print("   python -c \"from src.agents.yona_agent import create_yona_agent; create_yona_agent().interactive_mode()\"")
        else:
            print("\n⚠️  Some tests failed. Check the errors above.")
    else:
        print("\n❌ Critical tests failed. Cannot proceed with full testing.")
        
    print("\n" + "=" * 50)

if __name__ == "__main__":
    main()
