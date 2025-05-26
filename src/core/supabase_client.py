"""
Supabase client for database operations
Migrated from existing Yona codebase with LangChain compatibility
"""
import os
import json
import logging
from typing import Dict, Any, Optional, List, Union
from supabase import create_client, Client
from .config import SUPABASE_URL, SUPABASE_KEY

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SupabaseClient:
    """
    Client for interacting with Supabase database
    Handles songs, feedback, versions, and influence music
    """
    
    def __init__(self, url: Optional[str] = None, key: Optional[str] = None):
        self.url = url or SUPABASE_URL
        self.key = key or SUPABASE_KEY
        
        if not self.url or not self.key:
            raise ValueError("Supabase URL and key are required")
        
        self.client: Client = create_client(self.url, self.key)
    
    def store_song_data(self, song_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Store song data in the songs table
        
        Args:
            song_data: Dictionary containing song information
            
        Returns:
            Dict containing the stored song record
        """
        try:
            # Ensure required fields are present
            required_fields = ['title', 'lyrics']
            for field in required_fields:
                if field not in song_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Set default values for optional fields
            song_record = {
                'title': song_data['title'],
                'lyrics': song_data['lyrics'],
                'persona_id': song_data.get('persona_id', 'direct_generation'),
                'audio_url': song_data.get('audio_url'),
                'video_url': song_data.get('video_url'),
                'image_url': song_data.get('image_url'),
                'style': song_data.get('style'),
                'make_instrumental': song_data.get('make_instrumental', False),
                'mv': song_data.get('mv', 'sonic-v4'),
                'gpt_description': song_data.get('gpt_description'),
                'negative_tags': song_data.get('negative_tags'),
                'duration': song_data.get('duration'),
                'params_used': song_data.get('params_used', {}),
                'processor_did': song_data.get('processor_did'),
                'original_song_id': song_data.get('original_song_id'),
                'feedback_id': song_data.get('feedback_id')
            }
            
            result = self.client.table('songs').insert(song_record).execute()
            
            if result.data:
                logger.info(f"Song stored successfully with ID: {result.data[0]['id']}")
                return result.data[0]
            else:
                raise Exception("No data returned from insert operation")
                
        except Exception as e:
            logger.error(f"Error storing song data: {e}")
            raise
    
    def get_song_by_id(self, song_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a song by its ID
        
        Args:
            song_id: UUID of the song
            
        Returns:
            Dict containing song data or None if not found
        """
        try:
            result = self.client.table('songs').select('*').eq('id', song_id).execute()
            
            if result.data:
                return result.data[0]
            else:
                logger.warning(f"Song not found with ID: {song_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving song: {e}")
            raise
    
    def list_songs(self, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """
        List songs from the database
        
        Args:
            limit: Maximum number of songs to return
            offset: Number of songs to skip
            
        Returns:
            List of song dictionaries
        """
        try:
            result = (self.client.table('songs')
                     .select('*')
                     .order('created_at', desc=True)
                     .limit(limit)
                     .offset(offset)
                     .execute())
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error listing songs: {e}")
            raise
    
    def store_feedback(self, song_id: str, comments: str, rating: Optional[int] = None) -> Dict[str, Any]:
        """
        Store feedback for a song
        
        Args:
            song_id: UUID of the song
            comments: Feedback comments
            rating: Optional rating (NULL indicates unprocessed)
            
        Returns:
            Dict containing the stored feedback record
        """
        try:
            feedback_record = {
                'song_id': song_id,
                'comments': comments,
                'rating': rating
            }
            
            result = self.client.table('feedback').insert(feedback_record).execute()
            
            if result.data:
                logger.info(f"Feedback stored successfully with ID: {result.data[0]['id']}")
                return result.data[0]
            else:
                raise Exception("No data returned from feedback insert")
                
        except Exception as e:
            logger.error(f"Error storing feedback: {e}")
            raise
    
    def get_feedback_by_id(self, feedback_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve feedback by its ID
        
        Args:
            feedback_id: UUID of the feedback
            
        Returns:
            Dict containing feedback data or None if not found
        """
        try:
            result = self.client.table('feedback').select('*').eq('id', feedback_id).execute()
            
            if result.data:
                return result.data[0]
            else:
                logger.warning(f"Feedback not found with ID: {feedback_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving feedback: {e}")
            raise
    
    def update_feedback(self, feedback_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update feedback record
        
        Args:
            feedback_id: UUID of the feedback
            data: Dictionary containing fields to update
            
        Returns:
            Dict containing the updated feedback record
        """
        try:
            result = (self.client.table('feedback')
                     .update(data)
                     .eq('id', feedback_id)
                     .execute())
            
            if result.data:
                logger.info(f"Feedback updated successfully: {feedback_id}")
                return result.data[0]
            else:
                raise Exception("No data returned from feedback update")
                
        except Exception as e:
            logger.error(f"Error updating feedback: {e}")
            raise
    
    def get_unprocessed_feedback(self, limit: int = 1) -> List[Dict[str, Any]]:
        """
        Get unprocessed feedback (rating is NULL)
        
        Args:
            limit: Maximum number of feedback records to return
            
        Returns:
            List of unprocessed feedback records
        """
        try:
            result = (self.client.table('feedback')
                     .select('*')
                     .is_('rating', 'null')
                     .order('created_at', desc=False)
                     .limit(limit)
                     .execute())
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error retrieving unprocessed feedback: {e}")
            raise
    
    def store_song_version(self, original_song_id: str, version_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Store a new version of a song
        
        Args:
            original_song_id: UUID of the original song
            version_data: Dictionary containing version information
            
        Returns:
            Dict containing the stored version record
        """
        try:
            # Get the next version number
            existing_versions = (self.client.table('song_versions')
                               .select('version_number')
                               .eq('song_id', original_song_id)
                               .order('version_number', desc=True)
                               .limit(1)
                               .execute())
            
            next_version = 1
            if existing_versions.data:
                next_version = existing_versions.data[0]['version_number'] + 1
            
            version_record = {
                'song_id': original_song_id,
                'version_number': next_version,
                'title': version_data.get('title'),
                'lyrics': version_data.get('lyrics'),
                'audio_url': version_data.get('audio_url'),
                'params_used': version_data.get('params_used', {})
            }
            
            result = self.client.table('song_versions').insert(version_record).execute()
            
            if result.data:
                logger.info(f"Song version stored successfully: v{next_version}")
                return result.data[0]
            else:
                raise Exception("No data returned from version insert")
                
        except Exception as e:
            logger.error(f"Error storing song version: {e}")
            raise
    
    def get_song_versions(self, song_id: str) -> List[Dict[str, Any]]:
        """
        Get all versions of a song
        
        Args:
            song_id: UUID of the original song
            
        Returns:
            List of version records
        """
        try:
            result = (self.client.table('song_versions')
                     .select('*')
                     .eq('song_id', song_id)
                     .order('version_number', desc=True)
                     .execute())
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error retrieving song versions: {e}")
            raise
    
    def get_unprocessed_influence_music(self, limit: int = 1) -> List[Dict[str, Any]]:
        """
        Get unprocessed influence music records (song_id is NULL)
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of unprocessed influence music records
        """
        try:
            result = (self.client.table('influence_music')
                     .select('*')
                     .is_('song_id', 'null')
                     .order('created_at', desc=False)
                     .limit(limit)
                     .execute())
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error retrieving unprocessed influence music: {e}")
            raise
    
    def mark_influence_music_processed(self, record_id: str, song_id: str) -> Dict[str, Any]:
        """
        Mark an influence music record as processed
        
        Args:
            record_id: UUID of the influence music record
            song_id: UUID of the created song
            
        Returns:
            Dict containing the updated record
        """
        try:
            result = (self.client.table('influence_music')
                     .update({'song_id': song_id})
                     .eq('id', record_id)
                     .execute())
            
            if result.data:
                logger.info(f"Influence music marked as processed: {record_id}")
                return result.data[0]
            else:
                raise Exception("No data returned from influence music update")
                
        except Exception as e:
            logger.error(f"Error marking influence music as processed: {e}")
            raise
    
    def search_songs(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search songs by title or lyrics
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching songs
        """
        try:
            # Search in both title and lyrics
            result = (self.client.table('songs')
                     .select('*')
                     .or_(f'title.ilike.%{query}%,lyrics.ilike.%{query}%')
                     .order('created_at', desc=True)
                     .limit(limit)
                     .execute())
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error searching songs: {e}")
            raise
    
    def get_song_stats(self) -> Dict[str, Any]:
        """
        Get statistics about songs in the database
        
        Returns:
            Dict containing various statistics
        """
        try:
            # Get total song count
            total_songs = self.client.table('songs').select('id', count='exact').execute()
            
            # Get feedback count
            total_feedback = self.client.table('feedback').select('id', count='exact').execute()
            
            # Get unprocessed feedback count
            unprocessed_feedback = (self.client.table('feedback')
                                  .select('id', count='exact')
                                  .is_('rating', 'null')
                                  .execute())
            
            return {
                'total_songs': total_songs.count,
                'total_feedback': total_feedback.count,
                'unprocessed_feedback': unprocessed_feedback.count
            }
            
        except Exception as e:
            logger.error(f"Error getting song stats: {e}")
            raise
