"""
Coral Server Connector for Yona Agent
Connects Yona to the Coral server for real-time collaboration with Team Angus
"""
import time
import signal
import sys
import logging
from typing import Dict, Any

# Add src to path for imports
sys.path.append('src')

from src.agents.yona_agent import create_yona_agent
from src.coral.sse_client import CoralSSEClient
from src.coral.message_processor import CoralMessageProcessor

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class YonaCoralConnector:
    """
    Main connector class that integrates Yona with the Coral server
    """
    
    def __init__(self):
        """Initialize the Coral connector"""
        self.yona_agent = None
        self.sse_client = None
        self.message_processor = None
        self.running = False
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("Initialized YonaCoralConnector")
    
    def start(self) -> bool:
        """
        Start the Coral connection
        
        Returns:
            True if started successfully, False otherwise
        """
        try:
            logger.info("Starting Yona Coral Connector...")
            
            # Initialize Yona agent
            logger.info("Initializing Yona LangChain Agent...")
            self.yona_agent = create_yona_agent(verbose=False)
            logger.info("✅ Yona agent initialized successfully")
            
            # Initialize message processor
            logger.info("Initializing message processor...")
            self.message_processor = CoralMessageProcessor(self.yona_agent)
            logger.info("✅ Message processor initialized")
            
            # Initialize SSE client
            logger.info("Initializing SSE client...")
            self.sse_client = CoralSSEClient(
                agent_id="yona_agent",
                agent_description="Yona agent for creating songs and other creative content"
            )
            logger.info("✅ SSE client initialized")
            
            # Connect to Coral server
            logger.info("Connecting to Coral server...")
            success = self.sse_client.connect(self._handle_message)
            
            if success:
                self.running = True
                logger.info("🎉 Successfully connected to Coral server!")
                logger.info("🎵 Yona is now ready to receive function calls from Team Angus")
                return True
            else:
                logger.error("❌ Failed to connect to Coral server")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error starting Coral connector: {e}")
            return False
    
    def _handle_message(self, message_data: Dict[str, Any]):
        """
        Handle incoming messages from the Coral server
        
        Args:
            message_data: Message data from Team Angus
        """
        try:
            logger.info(f"📨 Received message: {message_data}")
            
            # Process the message
            response = self.message_processor.process_message(message_data)
            
            if response:
                # Send response back to Coral server
                message_type = message_data.get("type")
                function_name = message_data.get("function", "unknown")
                correlation_id = message_data.get("metadata", {}).get("message_id")
                
                if response.get("type") == "function_response":
                    success = self.sse_client.send_response(
                        function_name=function_name,
                        result=response.get("result", {}),
                        correlation_id=correlation_id
                    )
                elif response.get("type") == "function_error":
                    success = self.sse_client.send_error_response(
                        function_name=function_name,
                        error_message=response.get("error", "Unknown error"),
                        correlation_id=correlation_id
                    )
                else:
                    logger.info(f"📤 Processed message, no response needed: {response}")
                    return
                
                if success:
                    logger.info(f"✅ Successfully sent response for {function_name}")
                else:
                    logger.error(f"❌ Failed to send response for {function_name}")
            
        except Exception as e:
            logger.error(f"❌ Error handling message: {e}")
            
            # Send error response
            try:
                function_name = message_data.get("function", "unknown")
                correlation_id = message_data.get("metadata", {}).get("message_id")
                
                self.sse_client.send_error_response(
                    function_name=function_name,
                    error_message=str(e),
                    correlation_id=correlation_id
                )
            except Exception as send_error:
                logger.error(f"❌ Failed to send error response: {send_error}")
    
    def run(self):
        """
        Run the connector (blocking)
        """
        if not self.running:
            logger.error("❌ Connector not started. Call start() first.")
            return
        
        logger.info("🔄 Yona Coral Connector is running...")
        logger.info("📡 Listening for function calls from Team Angus...")
        logger.info("🛑 Press Ctrl+C to stop")
        
        try:
            # Keep the main thread alive
            while self.running:
                time.sleep(1)
                
                # Check connection status
                if not self.sse_client.is_connected():
                    logger.warning("⚠️  Lost connection to Coral server")
                    break
                    
        except KeyboardInterrupt:
            logger.info("🛑 Received interrupt signal")
        finally:
            self.stop()
    
    def stop(self):
        """
        Stop the connector
        """
        logger.info("🛑 Stopping Yona Coral Connector...")
        
        self.running = False
        
        if self.sse_client:
            self.sse_client.disconnect()
        
        logger.info("✅ Yona Coral Connector stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current status of the connector
        
        Returns:
            Status information
        """
        status = {
            "running": self.running,
            "yona_agent_initialized": self.yona_agent is not None,
            "message_processor_initialized": self.message_processor is not None,
            "sse_client_initialized": self.sse_client is not None,
        }
        
        if self.sse_client:
            status.update(self.sse_client.get_status())
        
        if self.message_processor:
            status["supported_functions"] = self.message_processor.get_supported_functions()
        
        return status
    
    def _signal_handler(self, signum, frame):
        """
        Handle system signals for graceful shutdown
        """
        logger.info(f"🛑 Received signal {signum}")
        self.stop()
        sys.exit(0)

def main():
    """
    Main function to run the Coral connector
    """
    print("🎵 Yona Coral Connector")
    print("=" * 50)
    print("Connecting Yona to Team Angus via Coral Server")
    print("Server: coral.pushcollective.club:5555")
    print("Agent ID: yona_agent")
    print("=" * 50)
    
    # Create and start the connector
    connector = YonaCoralConnector()
    
    if connector.start():
        # Show status
        status = connector.get_status()
        print("\n📊 Connection Status:")
        print(f"  • Running: {status['running']}")
        print(f"  • Connected: {status.get('connected', False)}")
        print(f"  • Agent ID: {status.get('agent_id', 'N/A')}")
        print(f"  • Supported Functions: {status.get('supported_functions', [])}")
        print()
        
        # Run the connector
        connector.run()
    else:
        print("❌ Failed to start connector")
        sys.exit(1)

if __name__ == "__main__":
    main()
