#!/bin/bash
# Install Coral Protocol Dependencies for Yona
# Safe installation script for MCP adapters

echo "🔧 Installing Coral Protocol Dependencies for Yona..."
echo "=================================================="

# Check if we're in a virtual environment
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ Virtual environment detected: $VIRTUAL_ENV"
else
    echo "⚠️  Warning: No virtual environment detected"
    echo "   Please run: source venv/bin/activate"
    exit 1
fi

echo ""
echo "📦 Step 1: Installing langchain-mcp-adapters..."
pip install langchain-mcp-adapters==0.1.1

echo ""
echo "📦 Step 2: Installing envio for error handling..."
pip install envio

echo ""
echo "🔍 Step 3: Verifying installation..."
python -c "
try:
    from langchain_mcp_adapters.client import MultiServerMCPClient
    print('✅ langchain_mcp_adapters imported successfully')
except ImportError as e:
    print(f'❌ Import error: {e}')

try:
    from envio import ClosedResourceError
    print('✅ envio imported successfully')
except ImportError as e:
    print(f'❌ Import error: {e}')
"

echo ""
echo "🧪 Step 4: Testing Yona Coral agent..."
echo "Running: python yona_coral_langchain_agent.py"
echo "Note: You may need to set OPENAI_API_KEY to your actual key"
echo ""

# Test the agent (will fail if OPENAI_API_KEY is not set properly, but that's expected)
python yona_coral_langchain_agent.py &
AGENT_PID=$!

# Let it run for a few seconds to see initial output
sleep 5

# Kill the test process
kill $AGENT_PID 2>/dev/null

echo ""
echo "=================================================="
echo "✅ Installation complete!"
echo ""
echo "🚀 Next steps:"
echo "1. Set your real OpenAI API key:"
echo "   export OPENAI_API_KEY=your_actual_openai_key"
echo ""
echo "2. Run the Coral Protocol agent:"
echo "   python yona_coral_langchain_agent.py"
echo ""
echo "3. The agent should connect to:"
echo "   http://coral.pushcollective.club:5555"
echo ""
echo "🎤 Yona will be ready for Coral Protocol multi-agent coordination!"
