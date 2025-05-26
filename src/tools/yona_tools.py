"""
LangChain tool wrappers for Yona capabilities
Migrates existing YonaAgent functionality to LangChain tools
"""
import json
import time
import logging
from typing import Dict, Any, Optional, List
from langchain.tools import tool
from openai import OpenAI

from ..core.music_api import MusicAPI
from ..core.supabase_client import SupabaseClient
from ..core.config import (
    MUSICAPI_KEY, OPENAI_KEY, YONA_PERSONA, 
    DEFAULT_SONG_PARAMETERS, DEFAULT_DID_DOMAIN
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize clients
music_api = MusicAPI(api_key=MUSICAPI_KEY)
supabase_client = SupabaseClient()
openai_client = OpenAI(api_key=OPENAI_KEY)

@tool
def generate_song_concept(prompt: str) -> str:
    """
    Generate a creative song concept based on a user prompt.
    
    Args:
        prompt: User's request or idea for a song
        
    Returns:
        A detailed song concept including theme, mood, and style suggestions
    """
    try:
        system_prompt = f"""
        You are {YONA_PERSONA['name']}, {YONA_PERSONA['description']}.
        
        Generate a detailed song concept based on the user's prompt. Include:
        1. Theme and message
        2. Mood and emotional tone
        3. Musical style suggestions
        4. Target audience
        5. Key elements to include
        
        Keep the concept creative and aligned with {YONA_PERSONA['style']} style.
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Create a song concept for: {prompt}"}
            ],
            temperature=0.8,
            max_tokens=500
        )
        
        concept = response.choices[0].message.content
        logger.info(f"Generated song concept for prompt: {prompt[:50]}...")
        return concept
        
    except Exception as e:
        logger.error(f"Error generating song concept: {e}")
        return f"Error generating concept: {str(e)}"

@tool
def generate_lyrics(concept: str) -> str:
    """
    Generate song lyrics based on a concept.
    
    Args:
        concept: The song concept to base lyrics on
        
    Returns:
        Complete song lyrics with verses, chorus, and bridge
    """
    try:
        system_prompt = f"""
        You are {YONA_PERSONA['name']}, a talented songwriter.
        
        Create complete song lyrics based on the provided concept. Include:
        - Verse 1
        - Chorus
        - Verse 2
        - Chorus
        - Bridge
        - Final Chorus
        
        Style: {YONA_PERSONA['style']}
        Language: {YONA_PERSONA['language']}
        
        Make the lyrics catchy, emotionally resonant, and suitable for the concept.
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Write lyrics for this concept: {concept}"}
            ],
            temperature=0.7,
            max_tokens=800
        )
        
        lyrics = response.choices[0].message.content
        logger.info("Generated song lyrics successfully")
        return lyrics
        
    except Exception as e:
        logger.error(f"Error generating lyrics: {e}")
        return f"Error generating lyrics: {str(e)}"

@tool
def create_song(title: str, lyrics: str, style: Optional[str] = None, 
               negative_tags: Optional[str] = None, make_instrumental: bool = False,
               mv: str = 'sonic-v4', voice_gender: str = 'female',
               max_attempts: int = 60, check_interval: int = 30) -> str:
    """
    Create a song using MusicAPI with the provided parameters.
    
    Args:
        title: Title of the song
        lyrics: Lyrics for the song
        style: Style tags for the song (optional)
        negative_tags: Tags to avoid in generation (optional)
        make_instrumental: Whether the song should be instrumental
        mv: Music video generation type
        voice_gender: Gender of the singer's voice
        max_attempts: Maximum status check attempts
        check_interval: Seconds between status checks
        
    Returns:
        JSON string containing song creation results and database ID
    """
    try:
        # Use default parameters if not provided
        style = style or DEFAULT_SONG_PARAMETERS['style']
        negative_tags = negative_tags or DEFAULT_SONG_PARAMETERS['negative_tags']
        
        # Create song with MusicAPI
        logger.info(f"Creating song: {title}")
        result = music_api.create_song(
            prompt=lyrics,
            title=title,
            style=style,
            negative_tags=negative_tags,
            make_instrumental=make_instrumental,
            mv=mv,
            voice_gender=voice_gender
        )
        
        task_id = result.get('task_id')
        if not task_id:
            return json.dumps({"error": "No task_id returned from MusicAPI"})
        
        # Monitor song creation progress
        logger.info(f"Monitoring song creation with task_id: {task_id}")
        attempts = 0
        
        while attempts < max_attempts:
            try:
                status_result = music_api.check_song_status(task_id)
                status = status_result.get('status', 'unknown')
                
                logger.info(f"Song status: {status} (attempt {attempts + 1}/{max_attempts})")
                
                if status == 'completed':
                    # Song is complete, store in database
                    song_data = {
                        'title': title,
                        'lyrics': lyrics,
                        'audio_url': status_result.get('audio_url'),
                        'video_url': status_result.get('video_url'),
                        'image_url': status_result.get('image_url'),
                        'style': style,
                        'make_instrumental': make_instrumental,
                        'mv': mv,
                        'gpt_description': f"Song created by Yona: {title}",
                        'negative_tags': negative_tags,
                        'duration': status_result.get('duration'),
                        'params_used': {
                            'style': style,
                            'negative_tags': negative_tags,
                            'make_instrumental': make_instrumental,
                            'mv': mv,
                            'voice_gender': voice_gender
                        },
                        'processor_did': f"did:web:{DEFAULT_DID_DOMAIN}"
                    }
                    
                    stored_song = supabase_client.store_song_data(song_data)
                    
                    return json.dumps({
                        "success": True,
                        "message": f"Song '{title}' created successfully!",
                        "song_id": stored_song['id'],
                        "audio_url": stored_song.get('audio_url'),
                        "video_url": stored_song.get('video_url'),
                        "task_id": task_id
                    })
                
                elif status == 'failed':
                    return json.dumps({
                        "error": f"Song creation failed: {status_result.get('error', 'Unknown error')}"
                    })
                
                # Check if song has audio URL even if status is still pending
                elif status_result.get('audio_url'):
                    logger.info("Song has audio URL, considering it successful")
                    song_data = {
                        'title': title,
                        'lyrics': lyrics,
                        'audio_url': status_result.get('audio_url'),
                        'video_url': status_result.get('video_url'),
                        'image_url': status_result.get('image_url'),
                        'style': style,
                        'make_instrumental': make_instrumental,
                        'mv': mv,
                        'gpt_description': f"Song created by Yona: {title}",
                        'negative_tags': negative_tags,
                        'duration': status_result.get('duration'),
                        'params_used': {
                            'style': style,
                            'negative_tags': negative_tags,
                            'make_instrumental': make_instrumental,
                            'mv': mv,
                            'voice_gender': voice_gender
                        },
                        'processor_did': f"did:web:{DEFAULT_DID_DOMAIN}"
                    }
                    
                    stored_song = supabase_client.store_song_data(song_data)
                    
                    return json.dumps({
                        "success": True,
                        "message": f"Song '{title}' created successfully!",
                        "song_id": stored_song['id'],
                        "audio_url": stored_song.get('audio_url'),
                        "video_url": stored_song.get('video_url'),
                        "task_id": task_id,
                        "note": "Song completed with audio URL available"
                    })
                
            except Exception as status_error:
                logger.warning(f"Error checking status: {status_error}")
            
            attempts += 1
            if attempts < max_attempts:
                time.sleep(check_interval)
        
        return json.dumps({
            "error": f"Song creation timed out after {max_attempts} attempts",
            "task_id": task_id
        })
        
    except Exception as e:
        logger.error(f"Error creating song: {e}")
        return json.dumps({"error": f"Failed to create song: {str(e)}"})

@tool
def list_songs(limit: int = 10, offset: int = 0) -> str:
    """
    List songs from the Supabase database.
    
    Args:
        limit: Maximum number of songs to return (default: 10)
        offset: Number of songs to skip (default: 0)
        
    Returns:
        JSON string containing list of songs with their details
    """
    try:
        songs = supabase_client.list_songs(limit=limit, offset=offset)
        
        # Format songs for display
        formatted_songs = []
        for song in songs:
            formatted_songs.append({
                "id": song['id'],
                "title": song['title'],
                "style": song.get('style', 'Unknown'),
                "audio_url": song.get('audio_url'),
                "created_at": song.get('created_at'),
                "duration": song.get('duration')
            })
        
        return json.dumps({
            "success": True,
            "count": len(formatted_songs),
            "songs": formatted_songs
        })
        
    except Exception as e:
        logger.error(f"Error listing songs: {e}")
        return json.dumps({"error": f"Failed to list songs: {str(e)}"})

@tool
def get_song_by_id(song_id: str) -> str:
    """
    Retrieve a specific song by its ID.
    
    Args:
        song_id: UUID of the song to retrieve
        
    Returns:
        JSON string containing song details
    """
    try:
        song = supabase_client.get_song_by_id(song_id)
        
        if song:
            return json.dumps({
                "success": True,
                "song": {
                    "id": song['id'],
                    "title": song['title'],
                    "lyrics": song['lyrics'],
                    "style": song.get('style'),
                    "audio_url": song.get('audio_url'),
                    "video_url": song.get('video_url'),
                    "image_url": song.get('image_url'),
                    "created_at": song.get('created_at'),
                    "duration": song.get('duration')
                }
            })
        else:
            return json.dumps({
                "error": f"Song not found with ID: {song_id}"
            })
            
    except Exception as e:
        logger.error(f"Error retrieving song: {e}")
        return json.dumps({"error": f"Failed to retrieve song: {str(e)}"})

@tool
def process_feedback(feedback_id: str) -> str:
    """
    Process feedback and create a new song version.
    
    Args:
        feedback_id: UUID of the feedback to process
        
    Returns:
        JSON string containing processing results
    """
    try:
        # Get feedback details
        feedback = supabase_client.get_feedback_by_id(feedback_id)
        if not feedback:
            return json.dumps({"error": f"Feedback not found: {feedback_id}"})
        
        # Get original song
        original_song = supabase_client.get_song_by_id(feedback['song_id'])
        if not original_song:
            return json.dumps({"error": f"Original song not found: {feedback['song_id']}"})
        
        # Use OpenAI to modify parameters based on feedback
        modified_params = _modify_parameters_with_openai(
            original_song.get('params_used', {}),
            feedback['comments']
        )
        
        # Generate new lyrics if needed
        if 'lyrics_feedback' in feedback['comments'].lower():
            new_lyrics = generate_lyrics(
                f"Improve these lyrics based on feedback: {feedback['comments']}\n\nOriginal lyrics: {original_song['lyrics']}"
            )
        else:
            new_lyrics = original_song['lyrics']
        
        # Create new song with modified parameters
        new_title = f"{original_song['title']} (v2)"
        result = create_song(
            title=new_title,
            lyrics=new_lyrics,
            style=modified_params.get('style'),
            negative_tags=modified_params.get('negative_tags'),
            make_instrumental=modified_params.get('make_instrumental', False),
            mv=modified_params.get('mv', 'sonic-v4'),
            voice_gender=modified_params.get('voice_gender', 'female')
        )
        
        # Mark feedback as processed
        supabase_client.update_feedback(feedback_id, {'rating': 1})
        
        return json.dumps({
            "success": True,
            "message": f"Processed feedback and created new version: {new_title}",
            "original_song_id": original_song['id'],
            "feedback_id": feedback_id,
            "new_song_result": json.loads(result)
        })
        
    except Exception as e:
        logger.error(f"Error processing feedback: {e}")
        return json.dumps({"error": f"Failed to process feedback: {str(e)}"})

@tool
def search_songs(query: str, limit: int = 10) -> str:
    """
    Search songs by title or lyrics.
    
    Args:
        query: Search query
        limit: Maximum number of results (default: 10)
        
    Returns:
        JSON string containing search results
    """
    try:
        songs = supabase_client.search_songs(query, limit=limit)
        
        formatted_songs = []
        for song in songs:
            formatted_songs.append({
                "id": song['id'],
                "title": song['title'],
                "style": song.get('style', 'Unknown'),
                "audio_url": song.get('audio_url'),
                "created_at": song.get('created_at')
            })
        
        return json.dumps({
            "success": True,
            "query": query,
            "count": len(formatted_songs),
            "songs": formatted_songs
        })
        
    except Exception as e:
        logger.error(f"Error searching songs: {e}")
        return json.dumps({"error": f"Failed to search songs: {str(e)}"})

def _modify_parameters_with_openai(original_params: Dict[str, Any], feedback: str) -> Dict[str, Any]:
    """
    Use OpenAI to intelligently modify song parameters based on feedback.
    
    Args:
        original_params: Original song parameters
        feedback: User feedback comments
        
    Returns:
        Modified parameters dictionary
    """
    try:
        system_prompt = """
        You are an AI music producer helping to improve songs based on user feedback.
        
        Given the original song parameters and user feedback, suggest modifications to improve the song.
        Return a JSON object with the modified parameters.
        
        Available parameters:
        - style: Musical style tags (e.g., "pop, upbeat, energetic")
        - negative_tags: Tags to avoid (e.g., "sad, slow, melancholic")
        - make_instrumental: Boolean for instrumental version
        - mv: Music video type ("sonic-v3-5" or "sonic-v4")
        - voice_gender: "female" or "male"
        
        Only modify parameters that are relevant to the feedback.
        """
        
        user_prompt = f"""
        Original parameters: {json.dumps(original_params)}
        User feedback: {feedback}
        
        Please suggest modifications to improve the song based on this feedback.
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=300
        )
        
        # Try to parse the response as JSON
        response_text = response.choices[0].message.content
        try:
            modified_params = json.loads(response_text)
            # Merge with original parameters
            result = original_params.copy()
            result.update(modified_params)
            return result
        except json.JSONDecodeError:
            logger.warning("Could not parse OpenAI response as JSON, using original parameters")
            return original_params
            
    except Exception as e:
        logger.error(f"Error modifying parameters with OpenAI: {e}")
        return original_params
