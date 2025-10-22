"""Base AI Provider Abstraction"""
from abc import ABC, abstractmethod
from typing import Optional, Dict
from enum import Enum

class ProviderType(Enum):
    CLAUDE_CODE = "claude-code"
    ANTHROPIC = "anthropic"
    OPENROUTER = "openrouter"
    OPENAI = "openai"

class BaseAIProvider(ABC):
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        self.api_key = api_key
        self.config = kwargs
    
    @abstractmethod
    async def generate_response(self, prompt: str, **kwargs) -> str:
        pass
    
    @abstractmethod
    def validate_api_key(self) -> bool:
        pass
