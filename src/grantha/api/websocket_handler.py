"""WebSocket handler for real-time chat communication in the Grantha platform."""

import logging
import json
from typing import Dict, Any, Optional
from urllib.parse import unquote

import google.generativeai as genai
from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field, ValidationError

from ..core.config import get_config, configs
from ..utils.data_pipeline import count_tokens, get_file_content
from ..utils.rag import RAG
from ..models.api_models import ChatRequest

# Configure logging
logger = logging.getLogger(__name__)


class WebSocketChatMessage(BaseModel):
    """Model for WebSocket chat messages."""
    role: str = Field(..., description="Role of the message sender (user/assistant)")
    content: str = Field(..., description="Content of the message")


class WebSocketChatRequest(BaseModel):
    """Model for WebSocket chat completion requests."""
    repo_url: str = Field(..., description="URL of the repository to query")
    messages: list[WebSocketChatMessage] = Field(..., description="List of chat messages")
    filePath: Optional[str] = Field(None, description="Optional path to a file in the repository")
    token: Optional[str] = Field(None, description="Personal access token for private repositories")
    type: str = Field("github", description="Type of repository (github, gitlab, bitbucket)")
    
    # Model parameters
    provider: str = Field("google", description="Model provider (google, openai, etc.)")
    model: Optional[str] = Field(None, description="Model name for the specified provider")
    
    language: str = Field("en", description="Language for content generation")
    excluded_dirs: Optional[str] = Field(None, description="Comma-separated list of directories to exclude")
    excluded_files: Optional[str] = Field(None, description="Comma-separated list of file patterns to exclude")
    included_dirs: Optional[str] = Field(None, description="Comma-separated list of directories to include")
    included_files: Optional[str] = Field(None, description="Comma-separated list of file patterns to include")


class WebSocketManager:
    """Manages WebSocket connections and message handling."""
    
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        """Accept a WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_text(self, websocket: WebSocket, message: str):
        """Send text message to a specific WebSocket."""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            self.disconnect(websocket)
    
    async def send_json(self, websocket: WebSocket, data: Dict[str, Any]):
        """Send JSON message to a specific WebSocket."""
        try:
            await websocket.send_json(data)
        except Exception as e:
            logger.error(f"Error sending JSON: {str(e)}")
            self.disconnect(websocket)


# Global WebSocket manager instance
manager = WebSocketManager()


async def handle_websocket_chat(websocket: WebSocket):
    """
    Handle WebSocket connection for chat completions.
    This implements real-time streaming chat functionality.
    """
    await manager.connect(websocket)
    
    try:
        # Get configuration
        config = get_config()
        
        # Receive and parse the request data
        request_data = await websocket.receive_json()
        logger.info(f"Received WebSocket request: {request_data}")
        
        try:
            request = WebSocketChatRequest(**request_data)
        except ValidationError as e:
            await manager.send_json(websocket, {
                "type": "error",
                "message": f"Invalid request format: {str(e)}"
            })
            await websocket.close()
            return
        
        # Check if request contains very large input
        input_too_large = False
        if request.messages and len(request.messages) > 0:
            last_message = request.messages[-1]
            if last_message.content:
                tokens = count_tokens(last_message.content)
                logger.info(f"Request size: {tokens} tokens")
                if tokens > 8000:
                    logger.warning(f"Request exceeds recommended token limit ({tokens} > 8000)")
                    input_too_large = True
        
        # Initialize Google Generative AI if available
        if config.google_api_key:
            genai.configure(api_key=config.google_api_key)
            model_name = request.model or "gemini-2.0-flash-exp"
            gemini_model = genai.GenerativeModel(model_name)
        else:
            await manager.send_json(websocket, {
                "type": "error",
                "message": "Google API key not configured"
            })
            await websocket.close()
            return
        
        # Create RAG instance if repository processing is needed
        context_text = ""
        if request.repo_url and not input_too_large:
            try:
                # Initialize RAG for repository context
                rag_instance = RAG(provider=request.provider, model=request.model)
                
                # Extract custom file filter parameters if provided
                excluded_dirs = None
                excluded_files = None
                included_dirs = None
                included_files = None
                
                if request.excluded_dirs:
                    excluded_dirs = [unquote(dir_path) for dir_path in request.excluded_dirs.split('\n') if dir_path.strip()]
                    logger.info(f"Using custom excluded directories: {excluded_dirs}")
                if request.excluded_files:
                    excluded_files = [unquote(file_pattern) for file_pattern in request.excluded_files.split('\n') if file_pattern.strip()]
                    logger.info(f"Using custom excluded files: {excluded_files}")
                if request.included_dirs:
                    included_dirs = [unquote(dir_path) for dir_path in request.included_dirs.split('\n') if dir_path.strip()]
                    logger.info(f"Using custom included directories: {included_dirs}")
                if request.included_files:
                    included_files = [unquote(file_pattern) for file_pattern in request.included_files.split('\n') if file_pattern.strip()]
                    logger.info(f"Using custom included files: {included_files}")
                
                # Prepare retriever
                rag_instance.prepare_retriever(
                    request.repo_url, 
                    request.type, 
                    request.token, 
                    excluded_dirs, 
                    excluded_files, 
                    included_dirs, 
                    included_files
                )
                logger.info(f"Retriever prepared for {request.repo_url}")
                
                # Get the query from the last message
                if request.messages:
                    query = request.messages[-1].content
                    
                    # If filePath exists, modify the query for RAG to focus on the file
                    rag_query = query
                    if request.filePath:
                        rag_query = f"Contexts related to {request.filePath}"
                        logger.info(f"Modified RAG query to focus on file: {request.filePath}")
                    
                    # Perform RAG retrieval
                    retrieved_documents = rag_instance(rag_query, language=request.language)
                    
                    if retrieved_documents and retrieved_documents[0].documents:
                        documents = retrieved_documents[0].documents
                        logger.info(f"Retrieved {len(documents)} documents")
                        
                        # Group documents by file path
                        docs_by_file = {}
                        for doc in documents:
                            file_path = doc.meta_data.get('file_path', 'unknown')
                            if file_path not in docs_by_file:
                                docs_by_file[file_path] = []
                            docs_by_file[file_path].append(doc)
                        
                        # Format context text with file path grouping
                        context_parts = []
                        for file_path, docs in docs_by_file.items():
                            header = f"## File Path: {file_path}\n\n"
                            content = "\n\n".join([doc.text for doc in docs])
                            context_parts.append(f"{header}{content}")
                        
                        context_text = "\n\n" + "-" * 10 + "\n\n".join(context_parts)
                    else:
                        logger.warning("No documents retrieved from RAG")
                        
            except Exception as e:
                logger.error(f"Error in RAG setup: {str(e)}")
                context_text = ""
        
        # Validate request
        if not request.messages or len(request.messages) == 0:
            await manager.send_json(websocket, {
                "type": "error",
                "message": "No messages provided"
            })
            await websocket.close()
            return
        
        last_message = request.messages[-1]
        if last_message.role != "user":
            await manager.send_json(websocket, {
                "type": "error",
                "message": "Last message must be from the user"
            })
            await websocket.close()
            return
        
        # Get repository information
        repo_name = request.repo_url.split("/")[-1] if "/" in request.repo_url else request.repo_url
        
        # Get language information
        language_code = request.language
        supported_langs = configs.get("lang", {}).get("supported_languages", {"en": "English"})
        language_name = supported_langs.get(language_code, "English")
        
        # Create system prompt
        system_prompt = f"""<role>
You are an expert code analyst examining the {request.type} repository: {request.repo_url} ({repo_name}).
You provide direct, concise, and accurate information about code repositories.
IMPORTANT: You MUST respond in {language_name} language.
</role>

<guidelines>
- Answer the user's question directly without ANY preamble or filler phrases
- Strictly base answers ONLY on existing code or documents
- DO NOT speculate or invent citations
- Format your response with proper markdown including headings, lists, and code blocks
- Be precise and technical when discussing code
- Use concise, direct language
- When showing code, include line numbers and file paths when relevant
</guidelines>"""
        
        # Fetch file content if provided
        file_content = ""
        if request.filePath:
            try:
                file_content = get_file_content(request.repo_url, request.filePath, request.type, request.token)
                logger.info(f"Successfully retrieved content for file: {request.filePath}")
            except Exception as e:
                logger.error(f"Error retrieving file content: {str(e)}")
        
        # Create the prompt with context
        prompt_parts = [f"/no_think {system_prompt}"]
        
        # Add conversation history
        if len(request.messages) > 1:
            conversation_history = ""
            for i in range(0, len(request.messages) - 1, 2):
                if i + 1 < len(request.messages):
                    user_msg = request.messages[i]
                    assistant_msg = request.messages[i + 1]
                    if user_msg.role == "user" and assistant_msg.role == "assistant":
                        conversation_history += f"<turn>\n<user>{user_msg.content}</user>\n<assistant>{assistant_msg.content}</assistant>\n</turn>\n"
            
            if conversation_history:
                prompt_parts.append(f"<conversation_history>\n{conversation_history}</conversation_history>")
        
        # Add file content if available
        if file_content:
            prompt_parts.append(f"<currentFileContent path=\"{request.filePath}\">\n{file_content}\n</currentFileContent>")
        
        # Add context if available
        if context_text.strip():
            prompt_parts.append(f"<START_OF_CONTEXT>\n{context_text}\n<END_OF_CONTEXT>")
        else:
            prompt_parts.append("<note>Answering without retrieval augmentation.</note>")
        
        # Add the query
        prompt_parts.append(f"<query>\n{last_message.content}\n</query>\n\nAssistant: ")
        
        prompt = "\n\n".join(prompt_parts)
        
        # Generate streaming response
        try:
            response = gemini_model.generate_content(prompt, stream=True)
            
            # Stream the response
            for chunk in response:
                if hasattr(chunk, 'text') and chunk.text:
                    await manager.send_text(websocket, chunk.text)
            
            # Close the WebSocket connection after the response is complete
            await websocket.close()
            
        except Exception as e:
            logger.error(f"Error in streaming response: {str(e)}")
            error_message = str(e)
            
            # Check for token limit errors and provide fallback
            if "maximum context length" in error_message or "token limit" in error_message or "too many tokens" in error_message:
                logger.warning("Token limit exceeded, retrying with simplified prompt")
                try:
                    # Create a simplified prompt without context
                    simplified_prompt = f"/no_think {system_prompt}\n\n"
                    if request.filePath and file_content:
                        simplified_prompt += f"<currentFileContent path=\"{request.filePath}\">\n{file_content}\n</currentFileContent>\n\n"
                    simplified_prompt += "<note>Answering without retrieval augmentation due to input size constraints.</note>\n\n"
                    simplified_prompt += f"<query>\n{last_message.content}\n</query>\n\nAssistant: "
                    
                    # Generate fallback response
                    fallback_response = gemini_model.generate_content(simplified_prompt, stream=True)
                    for chunk in fallback_response:
                        if hasattr(chunk, 'text') and chunk.text:
                            await manager.send_text(websocket, chunk.text)
                    
                except Exception as e2:
                    logger.error(f"Error in fallback streaming response: {str(e2)}")
                    await manager.send_text(websocket, "\nI apologize, but your request is too large for me to process. Please try a shorter query or break it into smaller parts.")
            else:
                # For other errors, return the error message
                await manager.send_text(websocket, f"\nError: {error_message}")
            
            # Close the WebSocket connection after error handling
            await websocket.close()
    
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Error in WebSocket handler: {str(e)}")
        try:
            await manager.send_json(websocket, {
                "type": "error", 
                "message": f"Server error: {str(e)}"
            })
            await websocket.close()
        except:
            pass
        finally:
            manager.disconnect(websocket)