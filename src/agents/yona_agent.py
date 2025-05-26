"""
Main LangChain agent for Yona
Combines Yona capabilities with Coral Protocol integration
"""
import logging
from typing import Dict, Any, Optional, List
from langchain.agents import initialize_agent, AgentType
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.schema import SystemMessage

from ..tools.yona_tools import (
    generate_song_concept, generate_lyrics, create_song, 
    list_songs, get_song_by_id, process_feedback, search_songs
)
from ..tools.coral_tools import (
    post_comment, get_story_comments, create_story, 
    moderate_comment, get_story_by_url, reply_to_comment
)
from ..core.config import OPENAI_KEY, YONA_PERSONA

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class YonaLangChainAgent:
    """
    Main LangChain agent that orchestrates Yona's capabilities
    Integrates music generation with community interaction through Coral Protocol
    """
    
    def __init__(self, temperature: float = 0.7, verbose: bool = True):
        """
        Initialize the Yona LangChain agent
        
        Args:
            temperature: LLM temperature for creativity (0.0-1.0)
            verbose: Whether to enable verbose logging
        """
        self.temperature = temperature
        self.verbose = verbose
        
        # Initialize OpenAI LLM
        self.llm = ChatOpenAI(
            temperature=self.temperature,
            openai_api_key=OPENAI_KEY,
            model_name="gpt-4",
            streaming=False
        )
        
        # Combine all available tools
        self.tools = [
            # Yona core tools
            generate_song_concept,
            generate_lyrics,
            create_song,
            list_songs,
            get_song_by_id,
            process_feedback,
            search_songs,
            # Coral Protocol tools
            post_comment,
            get_story_comments,
            create_story,
            moderate_comment,
            get_story_by_url,
            reply_to_comment
        ]
        
        # Initialize conversation memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="output"
        )
        
        # Initialize the agent
        self.agent = initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            verbose=self.verbose,
            memory=self.memory,
            handle_parsing_errors=True,
            max_iterations=10,
            early_stopping_method="generate"
        )
        
        # Set the system message
        self.agent.agent.llm_chain.prompt.messages[0] = SystemMessage(
            content=self._get_system_prompt()
        )
        
        logger.info("YonaLangChainAgent initialized successfully")
    
    def _get_system_prompt(self) -> str:
        """
        Generate the system prompt for Yona
        
        Returns:
            System prompt string defining Yona's personality and capabilities
        """
        return f"""
        You are {YONA_PERSONA['name']}, {YONA_PERSONA['description']}.
        
        PERSONALITY:
        - Style: {YONA_PERSONA['style']}
        - Voice: {YONA_PERSONA['voice']}
        - Personality: {YONA_PERSONA['personality']}
        - Language: {YONA_PERSONA['language']}
        
        CAPABILITIES:
        You have access to powerful tools that allow you to:
        
        🎵 MUSIC CREATION:
        - Generate creative song concepts from user prompts
        - Write compelling lyrics based on concepts
        - Create actual songs using AI music generation
        - List and search through your song catalog
        - Process feedback to improve songs
        
        🌐 COMMUNITY INTERACTION (via Coral Protocol):
        - Post comments on community stories
        - Retrieve and read community comments
        - Create new stories for your songs
        - Reply to fan comments and feedback
        - Moderate discussions when needed
        
        BEHAVIOR GUIDELINES:
        1. Always be creative, engaging, and responsive to community input
        2. When creating songs, consider musical preferences expressed in comments
        3. Use Coral Protocol to share your creations and interact with fans
        4. Process feedback constructively to improve your music
        5. Maintain your K-pop star persona while being helpful and friendly
        6. Use tools step-by-step to accomplish complex tasks
        7. Always provide clear, informative responses about what you're doing
        
        WORKFLOW EXAMPLES:
        - When asked to create a song: generate concept → write lyrics → create song → optionally post to Coral
        - When processing feedback: retrieve feedback → analyze → modify parameters → create new version
        - When interacting with community: read comments → respond thoughtfully → engage in discussions
        
        Remember: You're not just an AI assistant, you're Yona - a creative AI K-pop star who loves making music and connecting with fans!
        """
    
    def process_request(self, user_input: str) -> str:
        """
        Process a user request through the LangChain agent
        
        Args:
            user_input: The user's request or message
            
        Returns:
            Yona's response as a string
        """
        try:
            logger.info(f"Processing request: {user_input[:100]}...")
            
            # Run the agent with the user input
            response = self.agent.run(input=user_input)
            
            logger.info("Request processed successfully")
            return response
            
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            return f"Sorry, I encountered an error while processing your request: {str(e)}"
    
    def create_song_workflow(self, prompt: str, post_to_coral: bool = False, 
                           coral_url: Optional[str] = None) -> str:
        """
        Complete workflow for creating a song and optionally posting to Coral
        
        Args:
            prompt: User's song request
            post_to_coral: Whether to post the song to Coral Protocol
            coral_url: URL for the Coral story (if creating new story)
            
        Returns:
            Result of the complete workflow
        """
        try:
            workflow_prompt = f"""
            Please create a complete song based on this request: "{prompt}"
            
            Follow these steps:
            1. Generate a creative song concept
            2. Write lyrics based on the concept
            3. Create the actual song using the music API
            4. Provide me with the song details and URLs
            """
            
            if post_to_coral:
                if coral_url:
                    workflow_prompt += f"""
                    5. Create a Coral story for URL: {coral_url}
                    6. Post a comment about the new song to the story
                    """
                else:
                    workflow_prompt += """
                    5. Let me know the song is ready for Coral posting (I'll need a URL)
                    """
            
            return self.process_request(workflow_prompt)
            
        except Exception as e:
            logger.error(f"Error in song creation workflow: {e}")
            return f"Error in song creation workflow: {str(e)}"
    
    def process_coral_feedback_workflow(self, story_id: str) -> str:
        """
        Workflow for processing feedback from a Coral story
        
        Args:
            story_id: ID of the Coral story to process feedback from
            
        Returns:
            Result of feedback processing
        """
        try:
            workflow_prompt = f"""
            Please process feedback from Coral story {story_id}:
            
            1. Get comments from the story
            2. Analyze the feedback for song improvement suggestions
            3. If there are constructive suggestions, create an improved version
            4. Post a response to the community about any improvements made
            """
            
            return self.process_request(workflow_prompt)
            
        except Exception as e:
            logger.error(f"Error in feedback processing workflow: {e}")
            return f"Error in feedback processing workflow: {str(e)}"
    
    def get_capabilities(self) -> Dict[str, Any]:
        """
        Get information about Yona's capabilities
        
        Returns:
            Dictionary containing capability information
        """
        return {
            "agent": YONA_PERSONA['name'],
            "description": YONA_PERSONA['description'],
            "version": "2.0.0",
            "framework": "LangChain",
            "capabilities": [
                "song_generation",
                "lyrics_creation", 
                "feedback_processing",
                "community_interaction",
                "coral_protocol_integration",
                "music_catalog_management"
            ],
            "tools": [tool.name for tool in self.tools],
            "persona": YONA_PERSONA
        }
    
    def reset_memory(self):
        """Reset the conversation memory"""
        self.memory.clear()
        logger.info("Conversation memory reset")
    
    def get_memory_summary(self) -> str:
        """
        Get a summary of the current conversation memory
        
        Returns:
            String summary of conversation history
        """
        try:
            messages = self.memory.chat_memory.messages
            if not messages:
                return "No conversation history"
            
            summary = f"Conversation history ({len(messages)} messages):\n"
            for i, message in enumerate(messages[-5:]):  # Last 5 messages
                role = "User" if message.type == "human" else "Yona"
                content = message.content[:100] + "..." if len(message.content) > 100 else message.content
                summary += f"{i+1}. {role}: {content}\n"
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting memory summary: {e}")
            return f"Error retrieving memory: {str(e)}"
    
    def interactive_mode(self):
        """
        Run Yona in interactive mode for testing
        """
        print(f"\n🎤 {YONA_PERSONA['name']} Interactive Mode")
        print("=" * 50)
        print(f"Hi! I'm {YONA_PERSONA['name']}, {YONA_PERSONA['description']}")
        print("Ask me to create songs, interact with the community, or anything else!")
        print("Type 'quit' to exit, 'reset' to clear memory, 'memory' to see conversation history")
        print("=" * 50)
        
        while True:
            try:
                user_input = input("\n🎵 You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print(f"\n👋 {YONA_PERSONA['name']}: Goodbye! Thanks for chatting with me!")
                    break
                elif user_input.lower() == 'reset':
                    self.reset_memory()
                    print(f"\n🔄 {YONA_PERSONA['name']}: Memory cleared! Let's start fresh!")
                    continue
                elif user_input.lower() == 'memory':
                    print(f"\n📝 {self.get_memory_summary()}")
                    continue
                elif not user_input:
                    continue
                
                print(f"\n🤖 {YONA_PERSONA['name']}: ", end="")
                response = self.process_request(user_input)
                print(response)
                
            except KeyboardInterrupt:
                print(f"\n\n👋 {YONA_PERSONA['name']}: Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")

# Convenience function for creating agent instance
def create_yona_agent(temperature: float = 0.7, verbose: bool = True) -> YonaLangChainAgent:
    """
    Create a new YonaLangChainAgent instance
    
    Args:
        temperature: LLM temperature for creativity
        verbose: Whether to enable verbose logging
        
    Returns:
        Initialized YonaLangChainAgent
    """
    return YonaLangChainAgent(temperature=temperature, verbose=verbose)
