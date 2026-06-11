"""Settings and configuration management"""

import os
from pathlib import Path
from typing import Optional

class Settings:
    """Application settings"""

    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.config_dir = self.base_dir / "config"
        self.preferences_dir = self.base_dir / "preferences"

        # API Keys (from environment variables)
        self.api_keys = {
            "ollama": os.getenv("OLLAMA_API_URL", "http://localhost:11434"),
            "openai": os.getenv("OPENAI_API_KEY", ""),
            "anthropic": os.getenv("ANTHROPIC_API_KEY", ""),
            "groq": os.getenv("GROQ_API_KEY", ""),
            "cohere": os.getenv("COHERE_API_KEY", ""),
        }

        # Model settings
        self.default_local_model = "llama3.2"
        self.default_cloud_model = "gpt-4o"
        self.use_local_first = True  # Prefer Ollama unless disabled

    def get_api_key(self, provider: str) -> Optional[str]:
        return self.api_keys.get(provider)

    def has_api_key(self, provider: str) -> bool:
        key = self.api_keys.get(provider)
        return bool(key and len(key) > 10)

    def set_api_key(self, provider: str, key: str):
        self.api_keys[provider] = key
        os.environ[provider.upper() + "_API_KEY"] = key
