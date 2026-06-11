"""Settings and configuration management"""

import os
from pathlib import Path
from typing import Optional

class Settings:
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.config_dir    = self.base_dir / "config"
        self.data_dirs = {
            "preferences": self.base_dir / "preferences",
            "tasks":       self.base_dir / "tasks",
            "habits":      self.base_dir / "habits",
            "journal":     self.base_dir / "journal",
            "meals":       self.base_dir / "meals",
            "reminders":   self.base_dir / "reminders",
        }
        for d in self.data_dirs.values():
            d.mkdir(exist_ok=True)

        # API Keys
        self.api_keys = {
            "ollama":    os.getenv("OLLAMA_API_URL", "http://localhost:11434"),
            "openai":    os.getenv("OPENAI_API_KEY", ""),
            "anthropic": os.getenv("ANTHROPIC_API_KEY", ""),
            "groq":      os.getenv("GROQ_API_KEY", ""),
            "cohere":    os.getenv("COHERE_API_KEY", ""),
            "weather":   os.getenv("OPENWEATHER_API_KEY", ""),
            "news":      os.getenv("NEWS_API_KEY", ""),
        }

        # Model defaults
        self.default_models = {
            "ollama":    os.getenv("OLLAMA_DEFAULT_MODEL", "llama3.2"),
            "openai":    os.getenv("OPENAI_DEFAULT_MODEL", "gpt-4o"),
            "anthropic": os.getenv("ANTHROPIC_DEFAULT_MODEL", "claude-3-5-sonnet-20241022"),
            "groq":      os.getenv("GROQ_DEFAULT_MODEL", "llama-3.1-70b-versatile"),
            "cohere":    os.getenv("COHERE_DEFAULT_MODEL", "command-r-plus"),
        }

        self.default_provider = os.getenv("DEFAULT_PROVIDER", "ollama")
        self.use_local_first  = os.getenv("USE_LOCAL_FIRST", "true").lower() == "true"
        self.user_city        = os.getenv("USER_CITY", "Vasind")
        self.user_country     = os.getenv("USER_COUNTRY", "IN")

    def get_api_key(self, provider: str) -> Optional[str]:
        return self.api_keys.get(provider)

    def has_api_key(self, provider: str) -> bool:
        key = self.api_keys.get(provider, "")
        return bool(key and len(key) > 10)

    def set_api_key(self, provider: str, key: str):
        self.api_keys[provider] = key
        env_map = {
            "openai": "OPENAI_API_KEY", "anthropic": "ANTHROPIC_API_KEY",
            "groq": "GROQ_API_KEY", "cohere": "COHERE_API_KEY",
            "weather": "OPENWEATHER_API_KEY", "news": "NEWS_API_KEY",
        }
        if provider in env_map:
            os.environ[env_map[provider]] = key
