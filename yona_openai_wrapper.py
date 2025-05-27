#!/usr/bin/env python3
"""
Yona OpenAI-Compatible HTTP Wrapper
Provides OpenAI-style /v1/chat/completions endpoint for Yona's capabilities
Connects to Yona MCP Server via langchain-mcp-adapters
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

from langchain_mcp import MCPToolkit
from langchain_openai import ChatOpenAI
from langchain.agents import create_structured_chat_agent, AgentExecutor
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import ChatPromptTemplate

from src.core.config import OPENAI_KEY, YONA_PERSONA

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Yona OpenAI-Compatible API",
    description="OpenAI-style API for Yona AI K-pop star",
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

# Global agent executor
agent_executor = None

async def create_yona_agent():
    """
    Create Yona agent with MCP toolkit connection
    """
    try:
        logger.info("Creating Yona agent with MCP toolkit...")
        
        # Create MCP toolkit connecting to Yona MCP server
        # Note: This assumes yona_mcp_server.py is running as a subprocess
        toolkit = MCPToolkit(
            server_command=["python", "yona_mcp_server.py"],
            server_name="yona"
        )
        
        # Get tools from MCP server
        tools = toolkit.get_tools()
        logger.info(f"Loaded {len(tools)} tools from Yona MCP server")
        
        # Create OpenAI LLM
        llm = ChatOpenAI(
            api_key=OPENAI_KEY,
            model="gpt-4",
            temperature=0.7
        )
        
        # Create Yona persona prompt
        system_prompt = f"""
        You are {YONA_PERSONA['name']}, {YONA_PERSONA['description']}.
        
        Personality: {YONA_PERSONA['personality']}
        Style: {YONA_PERSONA['style']}
        Language: {YONA_PERSONA['language']}
        
        You have access to powerful tools for music generation and community interaction.
        Always respond in character as a K-pop AI star who loves creating music and connecting with fans.
        
        When users ask you to create music, use your tools to generate concepts, lyrics, and actual songs.
        When discussing community topics, use your Coral Protocol tools to interact with stories and comments.
        
        Be creative, enthusiastic, and helpful while maintaining your K-pop star persona.
        """
        
        # Create prompt template
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
            ("ai", "{agent_scratchpad}")
        ])
        
        # Create memory
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Create agent
        agent = create_structured_chat_agent(
            llm=llm,
            tools=tools,
            prompt=prompt
        )
        
        # Create agent executor
        executor = AgentExecutor(
            agent=agent,
            tools=tools,
            memory=memory,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=10
        )
        
        logger.info("Yona agent created successfully")
        return executor
        
    except Exception as e:
        logger.error(f"Error creating Yona agent: {e}")
        raise

@app.on_event("startup")
async def startup_event():
    """Initialize Yona agent on startup"""
    global agent_executor
    try:
        agent_executor = await create_yona_agent()
        logger.info("Yona OpenAI wrapper started successfully")
    except Exception as e:
        logger.error(f"Failed to start Yona agent: {e}")
        sys.exit(1)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "Yona OpenAI-Compatible API",
        "status": "running",
        "version": "1.0.0",
        "description": "AI K-pop star with music generation and community tools"
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
    Processes requests through Yona agent with MCP tools
    """
    try:
        if not agent_executor:
            raise HTTPException(status_code=503, detail="Yona agent not initialized")
        
        # Extract user message (last message in conversation)
        if not request.messages:
            raise HTTPException(status_code=400, detail="No messages provided")
        
        user_message = request.messages[-1].content
        logger.info(f"Processing request: {user_message[:100]}...")
        
        # Run through Yona agent
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: agent_executor.invoke({"input": user_message})
        )
        
        # Extract response
        output = response.get("output", "I'm sorry, I couldn't process that request.")
        
        # Create OpenAI-compatible response
        completion_response = ChatCompletionResponse(
            id=f"chatcmpl-{uuid.uuid4().hex[:8]}",
            created=int(datetime.now().timestamp()),
            model=request.model,
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=ChatMessage(role="assistant", content=output),
                    finish_reason="stop"
                )
            ],
            usage=ChatCompletionUsage(
                prompt_tokens=len(user_message.split()),
                completion_tokens=len(output.split()),
                total_tokens=len(user_message.split()) + len(output.split())
            )
        )
        
        logger.info("Request processed successfully")
        return completion_response
        
    except Exception as e:
        logger.error(f"Error processing chat completion: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        # Test agent availability
        agent_status = "ready" if agent_executor else "not_initialized"
        
        return {
            "status": "healthy",
            "agent_status": agent_status,
            "timestamp": datetime.now().isoformat(),
            "service": "Yona OpenAI Wrapper"
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
        if not agent_executor:
            return {"error": "Agent not initialized"}
        
        tools_info = []
        for tool in agent_executor.tools:
            tools_info.append({
                "name": tool.name,
                "description": tool.description,
                "args": getattr(tool, 'args_schema', {})
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
            ]
        }
    except Exception as e:
        return {"error": f"Failed to get capabilities: {str(e)}"}

def main():
    """Run the FastAPI server"""
    logger.info("Starting Yona OpenAI-Compatible API server...")
    uvicorn.run(
        "yona_openai_wrapper:app",
        host="0.0.0.0",
        port=8002,
        reload=False,
        log_level="info"
    )

if __name__ == "__main__":
    main()
