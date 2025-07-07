import re
import ast
from typing import Optional
from infrastructure.logging import get_logger


class AgentResponseProcessor:
    """Domain service for processing and cleaning agent responses"""
    
    def __init__(self):
        self._logger = get_logger(__name__)
    
    def clean_response(self, response: Optional[str]) -> str:
        """Clean and format response from agent."""
        
        # Handle None or empty responses
        if not response:
            return "No response received from agent."
        
        # Convert to string if it's not already
        if not isinstance(response, str):
            try:
                response = str(response)
            except Exception:
                return "Error: Could not convert response to string"
        
        # Remove thinking blocks first
        cleaned = self._remove_thinking_blocks(response)
        
        # Try to extract structured content
        structured_content = self._extract_structured_content(cleaned)
        if structured_content:
            return structured_content
        
        # Return cleaned response
        return cleaned.strip()
    
    def _remove_thinking_blocks(self, response: str) -> str:
        """Remove <thinking>...</thinking> blocks from response."""
        return re.sub(r'<thinking>.*?</thinking>', '', response, flags=re.DOTALL)
    
    def _extract_structured_content(self, response: str) -> Optional[str]:
        """Extract content from structured response format."""
        
        # Check if response is in structured format
        if not ("'role': 'assistant'" in response and "'content'" in response and "'text'" in response):
            return None
        
        try:
            # Try to parse as Python literal
            data = ast.literal_eval(response)
            if isinstance(data, dict) and 'content' in data and isinstance(data['content'], list):
                for item in data['content']:
                    if isinstance(item, dict) and 'text' in item:
                        return item['text']
        except Exception as e:
            self._logger.debug(f"Failed to parse structured response as literal: {e}")
            
            # If parsing fails, try regex as fallback
            return self._extract_with_regex(response)
        
        return None
    
    def _extract_with_regex(self, response: str) -> Optional[str]:
        """Extract text content using regex as fallback."""
        
        match = re.search(r"'text': '(.+?)(?:'}]|})", response, re.DOTALL)
        if match:
            text = match.group(1)
            # Unescape the content
            text = text.replace('\\n', '\n')
            text = text.replace('\\t', '\t')
            text = text.replace("\\'", "'")
            text = text.replace('\\"', '"')
            return text
        
        return None 