"""
LangChain tool wrappers for Coral Protocol integration
Enables community interaction through comments and stories
"""
import json
import logging
from typing import Dict, Any, Optional, List
from langchain.tools import tool
import httpx

from ..core.config import CORAL_SERVER_URL

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@tool
def post_comment(story_id: str, body: str, author_name: str = "Yona") -> str:
    """
    Post a comment to a Coral story.
    
    Args:
        story_id: ID of the Coral story to comment on
        body: Content of the comment
        author_name: Name of the comment author (default: "Yona")
        
    Returns:
        JSON string containing the posted comment details
    """
    try:
        # GraphQL mutation for creating comments
        mutation = """
        mutation CreateComment($input: CreateCommentInput!) {
          createComment(input: $input) {
            comment { 
              id 
              body 
              author { 
                username 
              }
              createdAt
              status
            }
            errors {
              field
              message
            }
          }
        }
        """
        
        variables = {
            "input": {
                "storyID": story_id,
                "body": body
            }
        }
        
        payload = {
            "query": mutation,
            "variables": variables
        }
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{CORAL_SERVER_URL}/api/graphql",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            
            result = response.json()
            
            if "errors" in result:
                return json.dumps({
                    "error": f"GraphQL errors: {result['errors']}"
                })
            
            comment_data = result.get("data", {}).get("createComment", {})
            
            if comment_data.get("errors"):
                return json.dumps({
                    "error": f"Comment creation errors: {comment_data['errors']}"
                })
            
            comment = comment_data.get("comment", {})
            
            logger.info(f"Posted comment to story {story_id}: {comment.get('id')}")
            
            return json.dumps({
                "success": True,
                "comment": {
                    "id": comment.get("id"),
                    "body": comment.get("body"),
                    "author": comment.get("author", {}).get("username"),
                    "created_at": comment.get("createdAt"),
                    "status": comment.get("status")
                },
                "story_id": story_id
            })
            
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error posting comment: {e}")
        return json.dumps({
            "error": f"HTTP error posting comment: {e.response.status_code} - {e.response.text}"
        })
    except Exception as e:
        logger.error(f"Error posting comment: {e}")
        return json.dumps({
            "error": f"Failed to post comment: {str(e)}"
        })

@tool
def get_story_comments(story_id: str, limit: int = 10) -> str:
    """
    Retrieve comments from a Coral story.
    
    Args:
        story_id: ID of the Coral story
        limit: Maximum number of comments to retrieve (default: 10)
        
    Returns:
        JSON string containing the story comments
    """
    try:
        # GraphQL query for fetching comments
        query = """
        query GetComments($storyID: ID!, $first: Int) {
          story(id: $storyID) {
            id
            url
            comments(first: $first, orderBy: CREATED_AT_DESC) {
              edges {
                node {
                  id
                  body
                  createdAt
                  status
                  author {
                    username
                  }
                  replies {
                    edges {
                      node {
                        id
                        body
                        createdAt
                        author {
                          username
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
        """
        
        variables = {
            "storyID": story_id,
            "first": limit
        }
        
        payload = {
            "query": query,
            "variables": variables
        }
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{CORAL_SERVER_URL}/api/graphql",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            
            result = response.json()
            
            if "errors" in result:
                return json.dumps({
                    "error": f"GraphQL errors: {result['errors']}"
                })
            
            story_data = result.get("data", {}).get("story", {})
            
            if not story_data:
                return json.dumps({
                    "error": f"Story not found: {story_id}"
                })
            
            comments_data = story_data.get("comments", {}).get("edges", [])
            
            formatted_comments = []
            for edge in comments_data:
                comment = edge.get("node", {})
                
                # Format replies
                replies = []
                reply_edges = comment.get("replies", {}).get("edges", [])
                for reply_edge in reply_edges:
                    reply = reply_edge.get("node", {})
                    replies.append({
                        "id": reply.get("id"),
                        "body": reply.get("body"),
                        "author": reply.get("author", {}).get("username"),
                        "created_at": reply.get("createdAt")
                    })
                
                formatted_comments.append({
                    "id": comment.get("id"),
                    "body": comment.get("body"),
                    "author": comment.get("author", {}).get("username"),
                    "created_at": comment.get("createdAt"),
                    "status": comment.get("status"),
                    "replies": replies
                })
            
            logger.info(f"Retrieved {len(formatted_comments)} comments from story {story_id}")
            
            return json.dumps({
                "success": True,
                "story_id": story_id,
                "story_url": story_data.get("url"),
                "comment_count": len(formatted_comments),
                "comments": formatted_comments
            })
            
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error retrieving comments: {e}")
        return json.dumps({
            "error": f"HTTP error retrieving comments: {e.response.status_code} - {e.response.text}"
        })
    except Exception as e:
        logger.error(f"Error retrieving comments: {e}")
        return json.dumps({
            "error": f"Failed to retrieve comments: {str(e)}"
        })

@tool
def create_story(url: str, title: str) -> str:
    """
    Create a new Coral story for a song or content.
    
    Args:
        url: URL of the content (e.g., song page)
        title: Title of the story
        
    Returns:
        JSON string containing the created story details
    """
    try:
        # GraphQL mutation for creating stories
        mutation = """
        mutation CreateStory($input: CreateStoryInput!) {
          createStory(input: $input) {
            story {
              id
              url
              metadata {
                title
              }
              createdAt
            }
            errors {
              field
              message
            }
          }
        }
        """
        
        variables = {
            "input": {
                "url": url,
                "metadata": {
                    "title": title
                }
            }
        }
        
        payload = {
            "query": mutation,
            "variables": variables
        }
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{CORAL_SERVER_URL}/api/graphql",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            
            result = response.json()
            
            if "errors" in result:
                return json.dumps({
                    "error": f"GraphQL errors: {result['errors']}"
                })
            
            story_data = result.get("data", {}).get("createStory", {})
            
            if story_data.get("errors"):
                return json.dumps({
                    "error": f"Story creation errors: {story_data['errors']}"
                })
            
            story = story_data.get("story", {})
            
            logger.info(f"Created story: {story.get('id')} for URL: {url}")
            
            return json.dumps({
                "success": True,
                "story": {
                    "id": story.get("id"),
                    "url": story.get("url"),
                    "title": story.get("metadata", {}).get("title"),
                    "created_at": story.get("createdAt")
                }
            })
            
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error creating story: {e}")
        return json.dumps({
            "error": f"HTTP error creating story: {e.response.status_code} - {e.response.text}"
        })
    except Exception as e:
        logger.error(f"Error creating story: {e}")
        return json.dumps({
            "error": f"Failed to create story: {str(e)}"
        })

@tool
def moderate_comment(comment_id: str, action: str) -> str:
    """
    Moderate a comment (approve, reject, etc.).
    
    Args:
        comment_id: ID of the comment to moderate
        action: Moderation action ("APPROVE", "REJECT", "NONE")
        
    Returns:
        JSON string containing moderation results
    """
    try:
        # GraphQL mutation for moderating comments
        mutation = """
        mutation ModerateComment($input: ModerateCommentInput!) {
          moderateComment(input: $input) {
            comment {
              id
              status
              body
              author {
                username
              }
            }
            errors {
              field
              message
            }
          }
        }
        """
        
        variables = {
            "input": {
                "commentID": comment_id,
                "status": action.upper()
            }
        }
        
        payload = {
            "query": mutation,
            "variables": variables
        }
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{CORAL_SERVER_URL}/api/graphql",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            
            result = response.json()
            
            if "errors" in result:
                return json.dumps({
                    "error": f"GraphQL errors: {result['errors']}"
                })
            
            moderation_data = result.get("data", {}).get("moderateComment", {})
            
            if moderation_data.get("errors"):
                return json.dumps({
                    "error": f"Moderation errors: {moderation_data['errors']}"
                })
            
            comment = moderation_data.get("comment", {})
            
            logger.info(f"Moderated comment {comment_id} with action: {action}")
            
            return json.dumps({
                "success": True,
                "comment": {
                    "id": comment.get("id"),
                    "status": comment.get("status"),
                    "body": comment.get("body"),
                    "author": comment.get("author", {}).get("username")
                },
                "action": action
            })
            
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error moderating comment: {e}")
        return json.dumps({
            "error": f"HTTP error moderating comment: {e.response.status_code} - {e.response.text}"
        })
    except Exception as e:
        logger.error(f"Error moderating comment: {e}")
        return json.dumps({
            "error": f"Failed to moderate comment: {str(e)}"
        })

@tool
def get_story_by_url(url: str) -> str:
    """
    Get a Coral story by its URL.
    
    Args:
        url: URL of the story to retrieve
        
    Returns:
        JSON string containing story details
    """
    try:
        # GraphQL query for fetching story by URL
        query = """
        query GetStoryByURL($url: String!) {
          story(url: $url) {
            id
            url
            metadata {
              title
              description
            }
            createdAt
            commentCounts {
              total
              published
              rejected
            }
          }
        }
        """
        
        variables = {
            "url": url
        }
        
        payload = {
            "query": query,
            "variables": variables
        }
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{CORAL_SERVER_URL}/api/graphql",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            
            result = response.json()
            
            if "errors" in result:
                return json.dumps({
                    "error": f"GraphQL errors: {result['errors']}"
                })
            
            story = result.get("data", {}).get("story")
            
            if not story:
                return json.dumps({
                    "error": f"Story not found for URL: {url}"
                })
            
            logger.info(f"Retrieved story: {story.get('id')} for URL: {url}")
            
            return json.dumps({
                "success": True,
                "story": {
                    "id": story.get("id"),
                    "url": story.get("url"),
                    "title": story.get("metadata", {}).get("title"),
                    "description": story.get("metadata", {}).get("description"),
                    "created_at": story.get("createdAt"),
                    "comment_counts": story.get("commentCounts", {})
                }
            })
            
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error retrieving story: {e}")
        return json.dumps({
            "error": f"HTTP error retrieving story: {e.response.status_code} - {e.response.text}"
        })
    except Exception as e:
        logger.error(f"Error retrieving story: {e}")
        return json.dumps({
            "error": f"Failed to retrieve story: {str(e)}"
        })

@tool
def reply_to_comment(parent_comment_id: str, body: str, author_name: str = "Yona") -> str:
    """
    Reply to an existing comment.
    
    Args:
        parent_comment_id: ID of the comment to reply to
        body: Content of the reply
        author_name: Name of the reply author (default: "Yona")
        
    Returns:
        JSON string containing the posted reply details
    """
    try:
        # GraphQL mutation for creating reply comments
        mutation = """
        mutation CreateReply($input: CreateCommentInput!) {
          createComment(input: $input) {
            comment { 
              id 
              body 
              author { 
                username 
              }
              createdAt
              status
              parent {
                id
              }
            }
            errors {
              field
              message
            }
          }
        }
        """
        
        variables = {
            "input": {
                "parentID": parent_comment_id,
                "body": body
            }
        }
        
        payload = {
            "query": mutation,
            "variables": variables
        }
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{CORAL_SERVER_URL}/api/graphql",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            
            result = response.json()
            
            if "errors" in result:
                return json.dumps({
                    "error": f"GraphQL errors: {result['errors']}"
                })
            
            comment_data = result.get("data", {}).get("createComment", {})
            
            if comment_data.get("errors"):
                return json.dumps({
                    "error": f"Reply creation errors: {comment_data['errors']}"
                })
            
            comment = comment_data.get("comment", {})
            
            logger.info(f"Posted reply to comment {parent_comment_id}: {comment.get('id')}")
            
            return json.dumps({
                "success": True,
                "reply": {
                    "id": comment.get("id"),
                    "body": comment.get("body"),
                    "author": comment.get("author", {}).get("username"),
                    "created_at": comment.get("createdAt"),
                    "status": comment.get("status"),
                    "parent_id": comment.get("parent", {}).get("id")
                }
            })
            
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error posting reply: {e}")
        return json.dumps({
            "error": f"HTTP error posting reply: {e.response.status_code} - {e.response.text}"
        })
    except Exception as e:
        logger.error(f"Error posting reply: {e}")
        return json.dumps({
            "error": f"Failed to post reply: {str(e)}"
        })
