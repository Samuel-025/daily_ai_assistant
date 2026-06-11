"""First-time setup wizard — interactive CLI configuration"""

import json
import os
from pathlib import Path
from config.settings import Settings


class SetupWizard:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.base_dir = Path(__file__).parent.parent

    def run(self):
        print("\n" + "═" * 55)
        print("  🌅  Daily AI Assistant — First-Time Setup Wizard")
        print("═" * 55)
        print("  Press Enter to keep the default value shown in [ ]\n")

        # User info
        name       = self._ask("Your name", "User")
        wake_time  = self._ask("Wake-up time (HH:MM)", "07:00")
        city       = self._ask("Your city", self.settings.user_city)
        country    = self._ask("Your country code (e.g. IN, US)", self.settings.user_country)
        fitness    = self._ask("Fitness level (low/moderate/high)", "moderate")
        work_focus = self._ask("Work focus / domain", "general")
        diet_type  = self._ask("Diet type (balanced/vegetarian/vegan/keto)", "balanced")

        # Provider
        print("\n  LLM Provider Options:")
        print("  1) ollama  — local (free, private, recommended)")
        print("  2) groq    — cloud (fast, has free tier)")
        print("  3) openai  — cloud (GPT-4o)")
        print("  4) anthropic — cloud (Claude)")
        print("  5) cohere  — cloud")
        provider = self._ask("Default provider", "ollama")

        # API Keys
        print("\n  API Keys (press Enter to skip any):")
        env_lines = []
        env_lines.append(f"OLLAMA_API_URL=http://localhost:11434")
        env_lines.append(f"OLLAMA_DEFAULT_MODEL=llama3.2")
        env_lines.append(f"DEFAULT_PROVIDER={provider}")
        env_lines.append(f"USE_LOCAL_FIRST={'true' if provider == 'ollama' else 'false'}")
        env_lines.append(f"USER_CITY={city}")
        env_lines.append(f"USER_COUNTRY={country}")

        key_prompts = [
            ("openai",    "OpenAI API Key",            "OPENAI_API_KEY"),
            ("anthropic", "Anthropic API Key",         "ANTHROPIC_API_KEY"),
            ("groq",      "Groq API Key",              "GROQ_API_KEY"),
            ("cohere",    "Cohere API Key",            "COHERE_API_KEY"),
            ("weather",   "OpenWeatherMap API Key",    "OPENWEATHER_API_KEY"),
            ("news",      "NewsAPI Key",               "NEWS_API_KEY"),
        ]
        for _, label, env_var in key_prompts:
            val = input(f"  {label}: ").strip()
            if val:
                env_lines.append(f"{env_var}={val}")

        # Write .env
        env_path = self.base_dir / ".env"
        env_path.write_text("\n".join(env_lines) + "\n")

        # Write preferences
        prefs = {
            "name": name, "wake_time": wake_time, "sleep_time": "23:00",
            "timezone": "Asia/Kolkata",
            "preferences": {
                "morning_routine": True, "task_prioritization": "ai",
                "habit_tracking": True, "daily_journal": True,
                "meal_planning": True, "weather_suggestions": True,
                "news_briefing": True, "focus_timer": True,
                "reminders": True, "motivational_quote": True,
            },
            "dietary": {"type": diet_type, "restrictions": [], "preferences": []},
            "fitness_level": fitness,
            "work_focus": work_focus,
            "interests": [],
            "news_categories": ["technology", "health"],
        }
        prefs_dir = self.base_dir / "preferences"
        prefs_dir.mkdir(exist_ok=True)
        (prefs_dir / "user_prefs.json").write_text(json.dumps(prefs, indent=2))

        print("\n  ✅ Setup complete!")
        print(f"  .env written to {env_path}")
        print("  Run the assistant: python main.py\n")

    def _ask(self, label: str, default: str) -> str:
        val = input(f"  {label} [{default}]: ").strip()
        return val if val else default
