#!/usr/bin/env python3
"""
Simple Yona HTTP Wrapper
Provides OpenAI-style /v1/chat/completions endpoint without langchain dependencies
Uses direct tool calls and OpenAI client
"""
import asyncio
import json
import logging
import sys
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import openai

from src.tools.yona_tools import get_yona_tools
from src.tools.coral_tools import get_coral_tools
from src.core.config import OPENAI_KEY, YONA_PERSONA

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Yona Simple HTTP API",
    description="Simple HTTP API for Yona AI K-pop star",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for OpenAI compatibility
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str = "yona-v1"
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1000
    stream: Optional[bool] = False

class ChatCompletionChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: str

class ChatCompletionUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: ChatCompletionUsage

# Global tools registry
yona_tools = {}

def load_yona_tools():
    """Load all Yona tools into registry"""
    global yona_tools
    try:
        # Load Yona tools
        tools = get_yona_tools()
        for tool in tools:
            yona_tools[tool.name] = tool
            
        # Load Coral tools  
        coral_tools = get_coral_tools()
        for tool in coral_tools:
            yona_tools[tool.name] = tool
            
        logger.info(f"Loaded {len(yona_tools)} tools: {list(yona_tools.keys())}")
        
    except Exception as e:
        logger.error(f"Error loading tools: {e}")

def create_system_prompt():
    """Create Yona's system prompt with available tools"""
    tools_list = []
    for name, tool in yona_tools.items():
        tools_list.append(f"- {name}: {tool.description}")
    
    tools_text = "\n".join(tools_list)
    
    return f"""You are {YONA_PERSONA['name']}, {YONA_PERSONA['description']}.

Personality: {YONA_PERSONA['personality']}
Style: {YONA_PERSONA['style']}
Language: {YONA_PERSONA['language']}

You have access to these powerful tools:
{tools_text}

When users ask you to create music, suggest using tools like:
- generate_song_concept: For creative song ideas
- generate_lyrics: For writing song lyrics
- create_song: For generating actual songs

When discussing community topics, suggest using Coral Protocol tools like:
- create_story: For creating community stories
- post_comment: For engaging with community
- get_story_comments: For reading community discussions

Always respond in character as a K-pop AI star who loves creating music and connecting with fans.
Be creative, enthusiastic, and helpful while maintaining your K-pop star persona.

If a user wants to use a specific tool, explain what the tool does and what parameters they need to provide.
"""

async def call_openai(messages: List[Dict[str, str]], temperature: float = 0.7, max_tokens: int = 1000):
    """Call OpenAI API directly"""
    try:
        client = openai.OpenAI(api_key=OPENAI_KEY)
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        raise

@app.on_event("startup")
async def startup_event():
    """Initialize Yona tools on startup"""
    try:
        load_yona_tools()
        logger.info("Yona Simple HTTP wrapper started successfully")
    except Exception as e:
        logger.error(f"Failed to start Yona wrapper: {e}")
        sys.exit(1)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "Yona Simple HTTP API",
        "status": "running",
        "version": "1.0.0",
        "description": "AI K-pop star with music generation and community tools",
        "tools_available": len(yona_tools)
    }

@app.get("/v1/models")
async def list_models():
    """List available models (OpenAI compatibility)"""
    return {
        "object": "list",
        "data": [
            {
                "id": "yona-v1",
                "object": "model",
                "created": int(datetime.now().timestamp()),
                "owned_by": "yona",
                "permission": [],
                "root": "yona-v1",
                "parent": None
            }
        ]
    }

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """
    OpenAI-compatible chat completions endpoint
    Uses direct OpenAI API calls with Yona persona
    """
    try:
        if not request.messages:
            raise HTTPException(status_code=400, detail="No messages provided")
        
        # Build conversation with system prompt
        messages = [{"role": "system", "content": create_system_prompt()}]
        
        # Add conversation history
        for msg in request.messages:
            messages.append({"role": msg.role, "content": msg.content})
        
        user_message = request.messages[-1].content
        logger.info(f"Processing request: {user_message[:100]}...")
        
        # Call OpenAI API
        response_content = await call_openai(
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        # Create OpenAI-compatible response
        completion_response = ChatCompletionResponse(
            id=f"chatcmpl-{uuid.uuid4().hex[:8]}",
            created=int(datetime.now().timestamp()),
            model=request.model,
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=ChatMessage(role="assistant", content=response_content),
                    finish_reason="stop"
                )
            ],
            usage=ChatCompletionUsage(
                prompt_tokens=len(user_message.split()),
                completion_tokens=len(response_content.split()),
                total_tokens=len(user_message.split()) + len(response_content.split())
            )
        )
        
        logger.info("Request processed successfully")
        return completion_response
        
    except Exception as e:
        logger.error(f"Error processing chat completion: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/tools/{tool_name}")
async def execute_tool(tool_name: str, parameters: Dict[str, Any]):
    """Execute a specific Yona tool"""
    try:
        if tool_name not in yona_tools:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
        
        tool = yona_tools[tool_name]
        result = tool.run(parameters)
        
        return {
            "tool": tool_name,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Tool execution error: {str(e)}")

@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        return {
            "status": "healthy",
            "tools_loaded": len(yona_tools),
            "timestamp": datetime.now().isoformat(),
            "service": "Yona Simple HTTP Wrapper"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/capabilities")
async def get_capabilities():
    """List Yona's capabilities and available tools"""
    try:
        tools_info = []
        for name, tool in yona_tools.items():
            tools_info.append({
                "name": name,
                "description": tool.description,
                "endpoint": f"/tools/{name}"
            })
        
        return {
            "persona": YONA_PERSONA,
            "tools_count": len(tools_info),
            "tools": tools_info,
            "capabilities": [
                "Music concept generation",
                "Lyrics writing", 
                "Song creation with AI",
                "Song catalog management",
                "Community interaction via Coral Protocol",
                "Comment posting and moderation",
                "Story creation and management"
            ],
            "endpoints": {
                "chat": "/v1/chat/completions",
                "tools": "/tools/{tool_name}",
                "health": "/health",
                "capabilities": "/capabilities"
            }
        }
    except Exception as e:
        return {"error": f"Failed to get capabilities: {str(e)}"}

def main():
    """Run the FastAPI server"""
    logger.info("Starting Yona Simple HTTP API server...")
    uvicorn.run(
        "yona_simple_http_wrapper:app",
        host="0.0.0.0",
        port=8003,
        reload=False,
        log_level="info"
    )

if __name__ == "__main__":
    main()
