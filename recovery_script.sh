#!/bin/bash
# Yona LangChain Recovery Script
# Fixes version conflicts by downgrading to stable 0.1.x ecosystem

echo "🔧 Starting Yona LangChain Recovery..."
echo "================================================"

echo "📦 Step 1: Removing conflicting packages..."
pip uninstall -y langchain-mcp langchain-core langsmith pydantic pydantic-core typing-extensions

echo "📦 Step 2: Reinstalling stable LangChain 0.1.x stack..."
pip install langchain==0.1.20
pip install langchain-core==0.1.53
pip install langchain-community==0.0.38
pip install langsmith==0.1.27
pip install "pydantic>=1.10,<2.0"

echo "📦 Step 3: Installing missing packages..."
pip install langchain-openai
pip install supabase>=2.3.0

echo "🔍 Step 4: Verifying installation..."
pip check

echo "🧪 Step 5: Testing Yona functionality..."
python test_yona_mcp_server.py

echo "================================================"
echo "✅ Recovery complete! Check test results above."
echo "If all tests pass, run: pip freeze > requirements.lock.txt"
