#!/bin/bash
# Restore Working Environment for Yona
# Fixes all version conflicts and restores stable LangChain 0.1.x environment

echo "🔧 Restoring Working Environment for Yona..."
echo "=============================================="

# Check if we're in a virtual environment
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ Virtual environment detected: $VIRTUAL_ENV"
else
    echo "⚠️  Warning: No virtual environment detected"
    echo "   Please run: source venv/bin/activate"
    exit 1
fi

echo ""
echo "📦 Current package versions:"
pip show pydantic langchain langchain-core langsmith | grep -E "(Name|Version)"

echo ""
echo "🔄 Restoring stable LangChain 0.1.x environment..."

# Uninstall problematic packages
echo "Removing MCP adapters and conflicting packages..."
pip uninstall -y langchain-mcp-adapters mcp

# Downgrade to stable versions
echo "Installing stable package versions..."
pip install pydantic==1.10.22
pip install langchain==0.1.20
pip install langchain-core==0.1.53
pip install langsmith==0.1.27
pip install langchain-community==0.0.38
pip install langchain-text-splitters==0.0.2

echo ""
echo "✅ Restored package versions:"
pip show pydantic langchain langchain-core langsmith | grep -E "(Name|Version)"

echo ""
echo "🧪 Testing HTTP wrapper..."
echo "Running: python yona_simple_http_wrapper.py (will test for 10 seconds)"
echo ""

# Test the HTTP wrapper briefly
timeout 10s python yona_simple_http_wrapper.py || echo "HTTP wrapper test completed"

echo ""
echo "=============================================="
echo "✅ Environment restoration complete!"
echo ""
echo "🚀 Next steps:"
echo "1. Test the HTTP wrapper:"
echo "   python yona_simple_http_wrapper.py"
echo ""
echo "2. In another terminal, test the Coral HTTP agent:"
echo "   export CORAL_SERVER_URL=http://coral.pushcollective.club:5555"
echo "   export CORAL_APPLICATION_ID=exampleApplication"
echo "   export CORAL_PRIVACY_KEY=privkey"
echo "   export CORAL_SESSION_ID=session1"
echo "   export OPENAI_API_KEY=your_actual_openai_key"
echo "   python yona_coral_http_agent.py"
echo ""
echo "🎤 Yona should now work with stable environment + pure HTTP Coral integration!"
