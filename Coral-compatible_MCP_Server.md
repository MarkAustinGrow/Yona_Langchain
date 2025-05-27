🔧 1. Define Yona's Tools
Identify Yona’s internal functions or LangChain tools (e.g. search_music, get_pending_uploads) and define them in a Python file using LangChain’s tool decorator:

python
Copy
Edit
from langchain.tools import tool

@tool
def get_pending_songs():
    """Returns songs pending for upload."""
    return ["song1", "song2"]

@tool
def analyze_music_content(song: str):
    """Analyzes a song's musical features."""
    return {"genre": "jazz", "tempo": "slow"}
🏗 2. Build an MCP Server
Use langchain.tools.mcp.mcp_server to serve those tools via STDIO:

python
Copy
Edit
from langchain.tools.mcp import mcp_server

if __name__ == "__main__":
    mcp_server([get_pending_songs, analyze_music_content])
Save this as yona_mcp_server.py.

▶ 3. Run the STDIO Server
bash
Copy
Edit
python yona_mcp_server.py
This is now an MCP-compatible server over STDIO — but not yet Coraliser-compatible.

🌉 4. (Optional for Coraliser) Add HTTP Wrapper (OpenAI-style)
As with Angus, create a FastAPI wrapper around a create_yona_client() adapter to expose /v1/chat/completions.

Use the same pattern as above with a new file: yona_openai_wrapper.py.

📄 5. Update Coraliser Settings
json
Copy
Edit
{
  "agents": [
    {
      "name": "yona",
      "host": "http://localhost:8002",
      "description": "Music data and metadata orchestration agent",
      "api_key": ""
    }
  ],
  "coral_server_url": "http://localhost:5000"
}
▶ 6. Run Coraliser
bash
Copy
Edit
cd coraliser
python coraliser.py --settings coraliser_settings.json
🧭 Final Architecture After These Steps
scss
Copy
Edit
                         ┌──────────────────────────┐
                         │        Coral Server       │
                         └────────────┬─────────────┘
                                      │
                ┌────────────────────┼────────────────────┐
                ▼                    ▼                    ▼
     Angus (OpenAI wrapper)   Yona (OpenAI wrapper)   [other agents...]
       → MCP STDIO                → MCP tools