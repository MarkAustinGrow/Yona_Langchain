"""
MusicAPI client for song generation
Migrated from existing Yona codebase with LangChain compatibility
"""
import os
import json
import time
import logging
import httpx
from typing import Dict, Any, Optional, List, Union
from .config import MUSICAPI_KEY, MUSICAPI_BASE_URL, NURO_BASE_URL

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MusicAPI:
    """
    Client for interacting with MusicAPI.ai services
    Supports both Sonic and Nuro APIs with automatic fallback
    """
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or MUSICAPI_KEY
        self.base_url = base_url or MUSICAPI_BASE_URL
        self.nuro_base_url = NURO_BASE_URL
        
        if not self.api_key:
            raise ValueError("MusicAPI key is required")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def create_song(self, prompt: str, title: Optional[str] = None, style: Optional[str] = None,
                   negative_tags: Optional[str] = None, make_instrumental: bool = False,
                   mv: str = 'sonic-v4', gpt_description_prompt: Optional[str] = None,
                   voice_gender: str = 'female') -> Dict[str, Any]:
        """
        Create a song using the Sonic API
        
        Args:
            prompt: Lyrics or text prompt for the song
            title: Title of the song
            style: Style tags for the song
            negative_tags: Tags to avoid in generation
            make_instrumental: Whether the song should be instrumental
            mv: Music video generation type
            gpt_description_prompt: Additional description for guiding generation
            voice_gender: Gender of the singer's voice
            
        Returns:
            Dict containing task_id and other response data
        """
        url = f"{self.base_url}/api/v1/music/generate"
        
        payload = {
            "prompt": prompt,
            "make_instrumental": make_instrumental,
            "mv": mv
        }
        
        if title:
            payload["title"] = title
        if style:
            payload["style"] = style
        if negative_tags:
            payload["negative_tags"] = negative_tags
        if gpt_description_prompt:
            payload["gpt_description_prompt"] = gpt_description_prompt
        if voice_gender:
            payload["voice_gender"] = voice_gender
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, headers=self.headers, json=payload)
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"Song creation initiated with task_id: {result.get('task_id')}")
                return result
                
        except httpx.HTTPStatusError as e:
            if "maintenance" in str(e).lower():
                logger.warning("Sonic API under maintenance, falling back to Nuro API")
                return self._fallback_to_nuro(prompt, title, style, voice_gender)
            else:
                logger.error(f"HTTP error creating song: {e}")
                raise
        except Exception as e:
            logger.error(f"Error creating song: {e}")
            raise
    
    def _fallback_to_nuro(self, prompt: str, title: Optional[str] = None, 
                         style: Optional[str] = None, voice_gender: str = 'female') -> Dict[str, Any]:
        """
        Fallback to Nuro API when Sonic API is unavailable
        """
        # Map style to genre and mood
        genre = "Pop"
        mood = "Happy"
        
        if style:
            style_lower = style.lower()
            if "rock" in style_lower:
                genre = "Rock"
            elif "folk" in style_lower:
                genre = "Folk"
            elif "jazz" in style_lower:
                genre = "Jazz"
            
            if "sad" in style_lower or "melancholic" in style_lower:
                mood = "Sad"
            elif "energetic" in style_lower or "upbeat" in style_lower:
                mood = "Energetic"
        
        return self.create_song_nuro(
            lyrics=prompt,
            gender=voice_gender.capitalize(),
            genre=genre,
            mood=mood
        )
    
    def check_song_status(self, task_id: str) -> Dict[str, Any]:
        """
        Check the status of a song generation task (Sonic API)
        
        Args:
            task_id: The task ID returned from create_song
            
        Returns:
            Dict containing status and song data if complete
        """
        url = f"{self.base_url}/api/v1/music/tasks/{task_id}"
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(url, headers=self.headers)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error checking song status: {e}")
            raise
    
    def create_song_nuro(self, lyrics: str, gender: Optional[str] = None,
                        genre: Optional[str] = None, mood: Optional[str] = None,
                        timbre: Optional[str] = None, duration: Optional[int] = None) -> Dict[str, Any]:
        """
        Create a song using the Nuro API
        
        Args:
            lyrics: Lyrics for the song
            gender: Singer's gender (Female/Male)
            genre: Genre of the song
            mood: Mood of the song
            timbre: Timbre of the singer's voice
            duration: Duration in seconds (30-240)
            
        Returns:
            Dict containing task_id and other response data
        """
        url = f"{self.nuro_base_url}/generate"
        
        payload = {"lyrics": lyrics}
        
        if gender:
            payload["gender"] = gender
        if genre:
            payload["genre"] = genre
        if mood:
            payload["mood"] = mood
        if timbre:
            payload["timbre"] = timbre
        if duration:
            payload["duration"] = duration
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, headers=self.headers, json=payload)
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"Nuro song creation initiated with task_id: {result.get('task_id')}")
                return result
                
        except Exception as e:
            logger.error(f"Error creating song with Nuro API: {e}")
            raise
    
    def check_song_status_nuro(self, task_id: str) -> Dict[str, Any]:
        """
        Check the status of a Nuro song generation task
        
        Args:
            task_id: The task ID returned from create_song_nuro
            
        Returns:
            Dict containing status and song data if complete
        """
        url = f"{self.nuro_base_url}/tasks/{task_id}"
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(url, headers=self.headers)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error checking Nuro song status: {e}")
            raise
    
    def create_persona(self, name: str, description: str, 
                      continue_clip_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a persona for consistent voice generation
        
        Args:
            name: Name of the persona
            description: Description of the persona
            continue_clip_id: Optional clip ID to base the persona on
            
        Returns:
            Dict containing persona data
        """
        url = f"{self.base_url}/api/v1/personas"
        
        payload = {
            "name": name,
            "description": description
        }
        
        if continue_clip_id:
            payload["continue_clip_id"] = continue_clip_id
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, headers=self.headers, json=payload)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error creating persona: {e}")
            raise
    
    def create_cover(self, continue_clip_id: str, prompt: str, title: Optional[str] = None,
                    style: Optional[str] = None, negative_tags: Optional[str] = None,
                    make_instrumental: bool = False, mv: str = 'sonic-v4',
                    gpt_description_prompt: Optional[str] = None,
                    voice_gender: str = 'female') -> Dict[str, Any]:
        """
        Create a cover song using an existing clip as reference
        
        Args:
            continue_clip_id: ID of the clip to use as reference
            prompt: Lyrics or text prompt for the cover
            title: Title of the cover song
            style: Style tags for the song
            negative_tags: Tags to avoid in generation
            make_instrumental: Whether the song should be instrumental
            mv: Music video generation type
            gpt_description_prompt: Additional description
            voice_gender: Gender of the singer's voice
            
        Returns:
            Dict containing task_id and other response data
        """
        url = f"{self.base_url}/api/v1/music/covers"
        
        payload = {
            "continue_clip_id": continue_clip_id,
            "prompt": prompt,
            "make_instrumental": make_instrumental,
            "mv": mv
        }
        
        if title:
            payload["title"] = title
        if style:
            payload["style"] = style
        if negative_tags:
            payload["negative_tags"] = negative_tags
        if gpt_description_prompt:
            payload["gpt_description_prompt"] = gpt_description_prompt
        if voice_gender:
            payload["voice_gender"] = voice_gender
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, headers=self.headers, json=payload)
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"Cover creation initiated with task_id: {result.get('task_id')}")
                return result
                
        except Exception as e:
            logger.error(f"Error creating cover: {e}")
            raise
