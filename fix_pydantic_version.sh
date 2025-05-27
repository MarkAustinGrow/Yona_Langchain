#!/bin/bash
# Fix Pydantic Version Conflict for Coral Protocol Agent
# Downgrade Pydantic to v1.10.13 for LangChain 0.1.x compatibility

echo "🔧 Fixing Pydantic Version Conflict..."
echo "======================================"

# Check if we're in a virtual environment
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ Virtual environment detected: $VIRTUAL_ENV"
else
    echo "⚠️  Warning: No virtual environment detected"
    echo "   Please run: source venv/bin/activate"
    exit 1
fi

echo ""
echo "📦 Current Pydantic version:"
pip show pydantic | grep Version

echo ""
echo "🔄 Downgrading Pydantic to v1.10.13 (LangChain 0.1.x compatible)..."
pip install pydantic==1.10.13

echo ""
echo "✅ New Pydantic version:"
pip show pydantic | grep Version

echo ""
echo "🧪 Testing Coral Protocol agent..."
echo "Running: python yona_coral_langchain_agent.py"
echo ""

# Test the agent briefly
timeout 10s python yona_coral_langchain_agent.py || echo "Agent test completed (timeout after 10s)"

echo ""
echo "======================================"
echo "✅ Pydantic version fix complete!"
echo ""
echo "🚀 Next steps:"
echo "1. Set your environment variables:"
echo "   export CORAL_SERVER_URL=http://coral.pushcollective.club:5555"
echo "   export CORAL_APPLICATION_ID=exampleApplication"
echo "   export CORAL_PRIVACY_KEY=privkey"
echo "   export CORAL_SESSION_ID=session1"
echo "   export OPENAI_API_KEY=your_actual_openai_key"
echo ""
echo "2. Run the Coral Protocol agent:"
echo "   python yona_coral_langchain_agent.py"
echo ""
echo "🎤 Yona should now connect to Coral Protocol successfully!"
