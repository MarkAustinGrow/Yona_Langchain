"""
Command Line Interface for Yona LangChain Agent
Provides easy access to Yona's capabilities
"""
import sys
import argparse
from dotenv import load_dotenv

# Add src to path for imports
sys.path.append('src')

# Load environment variables
load_dotenv()

def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description="Yona LangChain Agent - AI K-pop star with music generation and community interaction",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python yona_cli.py --interactive
  python yona_cli.py --request "Create a happy pop song about summer"
  python yona_cli.py --test
  python yona_cli.py --capabilities
        """
    )
    
    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Run in interactive mode for ongoing conversation'
    )
    
    parser.add_argument(
        '--request', '-r',
        type=str,
        help='Process a single request and exit'
    )
    
    parser.add_argument(
        '--test', '-t',
        action='store_true',
        help='Run basic tests to verify setup'
    )
    
    parser.add_argument(
        '--capabilities', '-c',
        action='store_true',
        help='Show Yona\'s capabilities and available tools'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--temperature',
        type=float,
        default=0.7,
        help='LLM temperature for creativity (0.0-1.0, default: 0.7)'
    )
    
    args = parser.parse_args()
    
    # If no arguments provided, show help
    if not any([args.interactive, args.request, args.test, args.capabilities]):
        parser.print_help()
        return
    
    try:
        # Run tests if requested
        if args.test:
            print("🧪 Running Yona LangChain Agent tests...")
            from test_yona_agent import main as test_main
            test_main()
            return
        
        # Import and create agent
        from src.agents.yona_agent import create_yona_agent
        
        print("🎤 Initializing Yona LangChain Agent...")
        agent = create_yona_agent(temperature=args.temperature, verbose=args.verbose)
        print("✅ Yona is ready!")
        
        # Show capabilities if requested
        if args.capabilities:
            capabilities = agent.get_capabilities()
            print("\n" + "=" * 50)
            print("🎵 YONA'S CAPABILITIES")
            print("=" * 50)
            print(f"Agent: {capabilities['agent']}")
            print(f"Description: {capabilities['description']}")
            print(f"Framework: {capabilities['framework']}")
            print(f"Version: {capabilities['version']}")
            print(f"\nAvailable Tools ({len(capabilities['tools'])}):")
            for i, tool in enumerate(capabilities['tools'], 1):
                print(f"  {i:2d}. {tool}")
            print(f"\nCapabilities:")
            for capability in capabilities['capabilities']:
                print(f"  • {capability.replace('_', ' ').title()}")
            print("=" * 50)
            return
        
        # Process single request
        if args.request:
            print(f"\n🎵 Processing request: {args.request}")
            print("-" * 50)
            response = agent.process_request(args.request)
            print(f"\n🤖 Yona: {response}")
            return
        
        # Run interactive mode
        if args.interactive:
            agent.interactive_mode()
            return
            
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure all dependencies are installed: pip install -r requirements.txt")
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()
