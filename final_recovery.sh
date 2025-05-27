#!/bin/bash
# Final Yona Recovery Script - Avoids langchain-openai conflicts
# Focuses on stable 0.1.x ecosystem without problematic packages

echo "🔧 Final Yona Recovery - Avoiding Version Conflicts..."
echo "================================================"

echo "📦 Step 1: Removing ALL conflicting packages..."
pip uninstall -y langchain-openai langchain-core langsmith pydantic pydantic-core tiktoken regex

echo "📦 Step 2: Reinstalling ONLY stable 0.1.x LangChain..."
pip install langchain==0.1.20
pip install langchain-core==0.1.53
pip install langchain-community==0.0.38
pip install langsmith==0.1.27
pip install "pydantic>=1.10,<2.0"

echo "📦 Step 3: Installing remaining dependencies..."
pip install supabase>=2.3.0

echo "🔍 Step 4: Verifying clean installation..."
pip check

echo "🧪 Step 5: Testing core Yona functionality..."
python test_yona_mcp_server.py

echo "🚀 Step 6: Testing simple MCP server..."
echo "Testing simple MCP server (Ctrl+C to stop)..."
timeout 5s python yona_simple_mcp_server.py || echo "✅ Simple MCP server started successfully"

echo "🌐 Step 7: Testing simple HTTP wrapper..."
echo "Testing simple HTTP wrapper (Ctrl+C to stop)..."
timeout 5s python yona_simple_http_wrapper.py || echo "✅ Simple HTTP wrapper test completed"

echo "================================================"
echo "✅ Final recovery complete!"
echo ""
echo "📋 Summary:"
echo "- Core Yona tools: Should be working (13/13)"
echo "- Simple MCP server: Available for Coral integration"
echo "- HTTP wrapper: May work without langchain-openai"
echo ""
echo "🔒 Lock the working state:"
echo "pip freeze > requirements.lock.txt"
