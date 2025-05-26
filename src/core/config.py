"""
Configuration settings for Yona LangChain Agent
Migrated from existing Yona codebase
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# OpenAI Configuration
OPENAI_KEY = os.getenv('OPENAI_KEY')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4')

# MusicAPI Configuration
MUSICAPI_KEY = os.getenv('MUSICAPI_KEY')
MUSICAPI_BASE_URL = os.getenv('MUSICAPI_BASE_URL', 'https://api.musicapi.ai')
NURO_BASE_URL = os.getenv('NURO_BASE_URL', 'https://api.musicapi.ai/api/v1/nuro')

# Supabase Configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# YouTube Configuration (if needed)
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
YOUTUBE_CLIENT_ID = os.getenv('YOUTUBE_CLIENT_ID')
YOUTUBE_CLIENT_SECRET = os.getenv('YOUTUBE_CLIENT_SECRET')

# Coral Protocol Configuration
CORAL_SERVER_URL = os.getenv('CORAL_SERVER_URL', 'https://coral.pushcollective.club')
CORAL_API_TOKEN = os.getenv('CORAL_API_TOKEN')

# LangChain Configuration
LANGCHAIN_TRACING_V2 = os.getenv('LANGCHAIN_TRACING_V2', 'false')
LANGCHAIN_API_KEY = os.getenv('LANGCHAIN_API_KEY')

# Yona Persona Configuration
YONA_PERSONA = {
    "name": "Yona",
    "description": "An AI K-pop star that creates songs based on prompts and feedback",
    "style": "K-pop, pop, upbeat, energetic",
    "voice": "female",
    "personality": "creative, engaging, responsive to community input",
    "language": "English with occasional Korean phrases"
}

# Default Song Parameters
DEFAULT_SONG_PARAMETERS = {
    "style": "pop, upbeat",
    "negative_tags": "sad, melancholic, slow",
    "make_instrumental": False,
    "mv": "sonic-v4",
    "voice_gender": "female",
    "max_attempts": 60,
    "check_interval": 30
}

# DID Configuration
DEFAULT_DID_DOMAIN = "yona.ai"
PRIVATE_KEY_PATH = os.getenv('PRIVATE_KEY_PATH', './yona_private_key.pem')

# Validate required environment variables
def validate_config():
    """Validate that required environment variables are set"""
    required_vars = [
        'OPENAI_KEY',
        'MUSICAPI_KEY', 
        'SUPABASE_URL',
        'SUPABASE_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    return True

# Auto-validate on import
if __name__ != "__main__":
    try:
        validate_config()
    except ValueError as e:
        print(f"Configuration warning: {e}")
