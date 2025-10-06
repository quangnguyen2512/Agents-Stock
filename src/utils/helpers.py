"""
Utility functions for Agents Stock 2.0.
"""
import functools
import asyncio
from typing import Callable, Any
from tenacity import retry, stop_after_attempt, wait_exponential


def retry_api_call(max_attempts: int = 3):
    """
    Decorator để retry API calls với exponential backoff.
    
    Args:
        max_attempts: Số lần thử tối đa
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=1, min=1, max=8)
        )
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator


def safe_json_parse(text: str) -> dict:
    """
    Parse JSON từ text response một cách an toàn.
    
    Args:
        text: Raw text response từ AI
        
    Returns:
        dict: Parsed JSON hoặc error dict
    """
    import json
    
    try:
        # Tìm JSON block trong response
        start_idx = text.find('{')
        end_idx = text.rfind('}') + 1
        
        if start_idx == -1 or end_idx == 0:
            raise ValueError("No JSON found in response")
            
        json_text = text[start_idx:end_idx]
        return json.loads(json_text)
        
    except Exception as e:
        return {
            "error": f"JSON parse failed: {str(e)}",
            "raw_response": text,
            "recommendation": "PARSE_ERROR",
            "confidence": 0.0
        }
