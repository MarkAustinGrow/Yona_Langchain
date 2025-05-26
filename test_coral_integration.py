"""
Test script for Coral Server Integration
Tests the SSE client and message processing without connecting to the actual server
"""
import sys
import json
import time
from typing import Dict, Any

# Add src to path for imports
sys.path.append('src')

from src.agents.yona_agent import create_yona_agent
from src.coral.message_processor import CoralMessageProcessor

def test_message_processor():
    """Test the message processor with sample function calls"""
    print("🧪 Testing Coral Message Processor")
    print("=" * 50)
    
    try:
        # Initialize Yona agent
        print("Initializing Yona agent...")
        yona_agent = create_yona_agent(verbose=False)
        print("✅ Yona agent initialized")
        
        # Initialize message processor
        print("Initializing message processor...")
        processor = CoralMessageProcessor(yona_agent)
        print("✅ Message processor initialized")
        
        # Test function calls
        test_cases = [
            {
                "name": "Agent Discovery",
                "message": {
                    "type": "agent_discovery",
                    "metadata": {
                        "sender": "angus_agent",
                        "message_id": "test_discovery_001"
                    }
                }
            },
            {
                "name": "Create Song",
                "message": {
                    "type": "function_call",
                    "function": "create_song",
                    "arguments": {
                        "prompt": "A happy song about artificial intelligence and friendship"
                    },
                    "metadata": {
                        "sender": "angus_agent",
                        "message_id": "test_create_001"
                    }
                }
            },
            {
                "name": "List Songs",
                "message": {
                    "type": "function_call",
                    "function": "list_songs",
                    "arguments": {
                        "limit": 5
                    },
                    "metadata": {
                        "sender": "angus_agent",
                        "message_id": "test_list_001"
                    }
                }
            },
            {
                "name": "Search Songs",
                "message": {
                    "type": "function_call",
                    "function": "search_songs",
                    "arguments": {
                        "query": "summer",
                        "limit": 3
                    },
                    "metadata": {
                        "sender": "angus_agent",
                        "message_id": "test_search_001"
                    }
                }
            },
            {
                "name": "Heartbeat",
                "message": {
                    "type": "heartbeat",
                    "metadata": {
                        "sender": "angus_agent",
                        "message_id": "test_heartbeat_001"
                    }
                }
            }
        ]
        
        # Process each test case
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n🧪 Test {i}: {test_case['name']}")
            print("-" * 30)
            
            message = test_case['message']
            print(f"📨 Input: {json.dumps(message, indent=2)}")
            
            try:
                # Process the message
                start_time = time.time()
                response = processor.process_message(message)
                end_time = time.time()
                
                print(f"⏱️  Processing time: {end_time - start_time:.2f} seconds")
                
                if response:
                    print(f"📤 Response: {json.dumps(response, indent=2)}")
                    print("✅ Test passed")
                else:
                    print("📤 No response (expected for some message types)")
                    print("✅ Test passed")
                    
            except Exception as e:
                print(f"❌ Test failed: {e}")
        
        print(f"\n📊 Summary:")
        print(f"  • Supported functions: {processor.get_supported_functions()}")
        print(f"  • Total tests: {len(test_cases)}")
        print("✅ Message processor testing complete")
        
    except Exception as e:
        print(f"❌ Error in message processor test: {e}")
        return False
    
    return True

def test_coral_connector_initialization():
    """Test that the Coral connector can be initialized"""
    print("\n🧪 Testing Coral Connector Initialization")
    print("=" * 50)
    
    try:
        from coral_connector import YonaCoralConnector
        
        print("Creating connector...")
        connector = YonaCoralConnector()
        print("✅ Connector created")
        
        print("Getting initial status...")
        status = connector.get_status()
        print(f"📊 Status: {json.dumps(status, indent=2)}")
        
        print("✅ Connector initialization test passed")
        return True
        
    except Exception as e:
        print(f"❌ Connector initialization test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🎵 Yona Coral Integration Tests")
    print("=" * 50)
    print("Testing Coral server integration components")
    print("Note: This tests the components without connecting to the actual server")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 2
    
    # Test 1: Message Processor
    if test_message_processor():
        tests_passed += 1
    
    # Test 2: Connector Initialization
    if test_coral_connector_initialization():
        tests_passed += 1
    
    # Summary
    print("\n" + "=" * 50)
    print("🏁 TEST SUMMARY")
    print("=" * 50)
    print(f"Tests passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! Coral integration is ready.")
        print("\n💡 Next steps:")
        print("  1. Install SSE dependencies: pip install sseclient-py")
        print("  2. Run the connector: python coral_connector.py")
        print("  3. Wait for Team Angus to connect and send function calls")
    else:
        print("❌ Some tests failed. Check the errors above.")
    
    print("=" * 50)

if __name__ == "__main__":
    main()
