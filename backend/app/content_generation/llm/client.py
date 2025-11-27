"""
Universal LLM client supporting multiple providers.
Provides a unified interface for Gemini, Claude, and OpenAI.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
from enum import Enum

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    GEMINI = "gemini"
    ANTHROPIC = "anthropic"
    OPENAI = "openai"


class LLMClient:
    """
    Universal LLM client with support for multiple providers.
    Provides a consistent interface regardless of the underlying provider.
    """
    
    def __init__(
        self,
        provider: str,
        model: str,
        api_key: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ):
        """
        Initialize LLM client.
        
        Args:
            provider: Provider name (gemini, anthropic, openai)
            model: Model identifier
            api_key: API key for the provider
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
        """
        self.provider = LLMProvider(provider.lower())
        self.model = model
        self.api_key = api_key
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Initialize provider-specific client
        self._init_client()
    
    def _init_client(self):
        """Initialize the provider-specific client."""
        if self.provider == LLMProvider.GEMINI:
            self._init_gemini()
        elif self.provider == LLMProvider.ANTHROPIC:
            self._init_anthropic()
        elif self.provider == LLMProvider.OPENAI:
            self._init_openai()
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    def _init_gemini(self):
        """Initialize Gemini client."""
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            
            generation_config = {
                "temperature": self.temperature,
                "top_p": 0.95,
                "top_k": 40,
            }
            
            if self.max_tokens:
                generation_config["max_output_tokens"] = self.max_tokens
            
            self.client = genai.GenerativeModel(
                model_name=self.model,
                generation_config=generation_config
            )
            logger.info(f"Initialized Gemini client with model: {self.model}")
        except ImportError:
            raise ImportError("Please install google-generativeai: pip install google-generativeai")
    
    def _init_anthropic(self):
        """Initialize Anthropic (Claude) client."""
        try:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=self.api_key)
            logger.info(f"Initialized Anthropic client with model: {self.model}")
        except ImportError:
            raise ImportError("Please install anthropic: pip install anthropic")
    
    def _init_openai(self):
        """Initialize OpenAI client."""
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
            logger.info(f"Initialized OpenAI client with model: {self.model}")
        except ImportError:
            raise ImportError("Please install openai: pip install openai")
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Generate text using the configured LLM.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Generated text
        """
        if self.provider == LLMProvider.GEMINI:
            return self._generate_gemini(prompt, system_prompt, **kwargs)
        elif self.provider == LLMProvider.ANTHROPIC:
            return self._generate_anthropic(prompt, system_prompt, **kwargs)
        elif self.provider == LLMProvider.OPENAI:
            return self._generate_openai(prompt, system_prompt, **kwargs)
    
    def _generate_gemini(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate using Gemini."""
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        response = self.client.generate_content(full_prompt)
        return response.text
    
    def _generate_anthropic(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate using Claude with streaming to avoid timeouts on long requests."""
        messages = [{"role": "user", "content": prompt}]
        
        params = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens or 4096
        }
        
        if system_prompt:
            params["system"] = system_prompt
        
        # Use streaming to avoid timeout on long-running requests
        # See: https://github.com/anthropics/anthropic-sdk-python#long-requests
        try:
            with self.client.messages.stream(**params) as stream:
                response_text = "".join(text for text in stream.text_stream)
            return response_text
        except Exception as e:
            logger.error(f"Anthropic streaming generation failed: {str(e)}")
            raise
    
    def _generate_openai(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate using OpenAI."""
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        params = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature
        }
        
        if self.max_tokens:
            params["max_tokens"] = self.max_tokens
        
        response = self.client.chat.completions.create(**params)
        return response.choices[0].message.content
    
    def generate_with_images(
        self,
        prompt: str,
        images: List[bytes],
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate text with image inputs (for vision models).
        
        Args:
            prompt: Text prompt
            images: List of image bytes
            system_prompt: Optional system prompt
            
        Returns:
            Generated text
        """
        if self.provider == LLMProvider.GEMINI:
            return self._generate_gemini_with_images(prompt, images, system_prompt)
        else:
            raise NotImplementedError(f"Image generation not implemented for {self.provider}")
    
    def _generate_gemini_with_images(
        self,
        prompt: str,
        images: List[bytes],
        system_prompt: Optional[str] = None
    ) -> str:
        """Generate using Gemini with images."""
        import google.generativeai as genai
        
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        # Prepare content parts
        content_parts = [full_prompt]
        
        for image_bytes in images:
            content_parts.append({
                "mime_type": "image/png",
                "data": image_bytes
            })
        
        response = self.client.generate_content(content_parts)
        return response.text
    
    async def generate_with_images_async(
        self,
        prompt: str,
        images: List[bytes],
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Async wrapper for generate_with_images.
        Runs the synchronous call in a thread pool to avoid blocking.
        
        Args:
            prompt: Text prompt
            images: List of image bytes
            system_prompt: Optional system prompt
            
        Returns:
            Generated text
        """
        return await asyncio.to_thread(
            self.generate_with_images, prompt, images, system_prompt
        )


def create_llm_client(
    provider: str,
    model: str,
    api_key: str,
    **kwargs
) -> LLMClient:
    """
    Factory function to create LLM client.
    
    Args:
        provider: Provider name
        model: Model identifier
        api_key: API key
        **kwargs: Additional parameters
        
    Returns:
        LLMClient instance
    """
    return LLMClient(
        provider=provider,
        model=model,
        api_key=api_key,
        **kwargs
    )

