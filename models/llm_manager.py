"""LLM Manager - Handles Ollama + cloud model integration"""

import os
import requests
from typing import Optional
from config.settings import Settings

class LLMManager:
    """Manage multiple LLM providers"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.providers = {
            "ollama": self.call_ollama,
            "openai": self.call_openai,
            "anthropic": self.call_anthropic,
            "groq": self.call_groq,
            "cohere": self.call_cohere,
        }

    def call_ollama(self, prompt: str, model: str = None, **kwargs) -> Optional[str]:
        """Call Ollama local model"""
        model = model or self.settings.default_local_model
        api_url = self.settings.api_keys["ollama"]
        try:
            response = requests.post(
                f"{api_url}/api/generate",
                json={"model": model, "prompt": prompt, "stream": False, **kwargs},
                timeout=30
            )
            if response.status_code == 200:
                return response.json().get("response", "")
        except Exception as e:
            print(f"Ollama error: {e}")
        return None

    def call_openai(self, prompt: str, model: str = None, **kwargs) -> Optional[str]:
        """Call OpenAI GPT"""
        try:
            import openai
            api_key = self.settings.get_api_key("openai")
            if not api_key:
                return None
            client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=model or self.settings.default_cloud_model,
                messages=[{"role": "user", "content": prompt}], **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"OpenAI error: {e}")
        return None

    def call_anthropic(self, prompt: str, model: str = None, **kwargs) -> Optional[str]:
        """Call Anthropic Claude"""
        try:
            import anthropic
            api_key = self.settings.get_api_key("anthropic")
            if not api_key:
                return None
            client = anthropic.Anthropic(api_key=api_key)
            response = client.messages.create(
                model=model or "claude-3-sonnet-20240229",
                messages=[{"role": "user", "content": prompt}], **kwargs
            )
            return response.content[0].text
        except Exception as e:
            print(f"Anthropic error: {e}")
        return None

    def call_groq(self, prompt: str, model: str = None, **kwargs) -> Optional[str]:
        """Call Groq (fast LLM)"""
        try:
            import groq
            api_key = self.settings.get_api_key("groq")
            if not api_key:
                return None
            client = groq.Groq(api_key=api_key)
            response = client.chat.completions.create(
                model=model or "llama-3.1-70b-versatile",
                messages=[{"role": "user", "content": prompt}], **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Groq error: {e}")
        return None

    def call_cohere(self, prompt: str, model: str = None, **kwargs) -> Optional[str]:
        """Call Cohere"""
        try:
            import cohere
            api_key = self.settings.get_api_key("cohere")
            if not api_key:
                return None
            client = cohere.Client(api_key)
            response = client.chat(message=prompt, model=model or "command-r-plus", **kwargs)
            return response.text
        except Exception as e:
            print(f"Cohere error: {e}")
        return None

    def generate(self, prompt: str, provider: str = None, **kwargs) -> Optional[str]:
        """Generate response using specified or auto-selected provider"""
        if provider and provider in self.providers:
            return self.providers[provider](prompt, **kwargs)
        if self.settings.use_local_first:
            result = self.call_ollama(prompt, **kwargs)
            if result:
                return result
        for cloud in ["openai", "groq", "anthropic", "cohere"]:
            if self.settings.has_api_key(cloud):
                result = self.providers[cloud](prompt, **kwargs)
                if result:
                    return result
        print("No available LLM provider")
        return None

    def set_api_key(self, provider: str, key: str):
        self.settings.set_api_key(provider, key)
