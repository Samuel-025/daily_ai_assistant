#!/usr/bin/env python3
"""
Daily AI Assistant v2.0
All-in-one personalized daily life tool
Supports: Ollama (local) + OpenAI + Anthropic + Groq + Cohere
"""

import argparse
from dotenv import load_dotenv
from config.settings import Settings
from models.llm_manager import LLMManager
from utils.daily_orchestrator import DailyOrchestrator
from utils.setup_wizard import SetupWizard

load_dotenv()

def parse_args():
    parser = argparse.ArgumentParser(
        description="🌅 Daily AI Assistant - Your personalized AI-powered daily companion"
    )
    parser.add_argument("--setup", action="store_true", help="Run first-time setup wizard")
    parser.add_argument("--module", type=str, help="Run a specific module only (morning/tasks/habits/journal/meals/weather/news/focus/reminders)")
    parser.add_argument("--provider", type=str, default=None, help="Force a specific LLM provider (ollama/openai/anthropic/groq/cohere)")
    parser.add_argument("--list-models", action="store_true", help="List available Ollama models")
    return parser.parse_args()


class DailyAIAssistant:
    def __init__(self, provider: str = None):
        self.settings = Settings()
        self.llm_manager = LLMManager(self.settings)
        self.orchestrator = DailyOrchestrator(self.llm_manager, provider=provider)

    def run(self, module: str = None):
        print("\n🌅 Daily AI Assistant v2.0")
        print("━" * 50)
        user_prefs = self.orchestrator.load_preferences()
        print(f"  Welcome back, {user_prefs.get('name', 'User')}! 👋")
        print("━" * 50)

        modules = {
            "morning":   self.orchestrator.run_morning_routine,
            "tasks":     self.orchestrator.run_task_manager,
            "habits":    self.orchestrator.run_habit_tracker,
            "journal":   self.orchestrator.run_journal,
            "meals":     self.orchestrator.run_meal_planner,
            "weather":   self.orchestrator.run_weather_suggestions,
            "news":      self.orchestrator.run_news_briefing,
            "focus":     self.orchestrator.run_focus_timer,
            "reminders": self.orchestrator.run_reminders,
            "quote":     self.orchestrator.run_motivational_quote,
        }

        if module:
            fn = modules.get(module)
            if fn:
                fn(user_prefs)
            else:
                print(f"Unknown module: {module}. Available: {', '.join(modules.keys())}")
        else:
            for fn in modules.values():
                fn(user_prefs)

        print("\n" + "━" * 50)
        print("✅ Done! Have a productive day!")
        print("━" * 50 + "\n")


def main():
    args = parse_args()
    settings = Settings()
    llm = LLMManager(settings)

    if args.setup:
        wizard = SetupWizard(settings)
        wizard.run()
        return

    if args.list_models:
        models = llm.list_ollama_models()
        print("\n📦 Available Ollama Models:")
        for m in models:
            print(f"  • {m}")
        return

    assistant = DailyAIAssistant(provider=args.provider)
    assistant.run(module=args.module)


if __name__ == "__main__":
    main()
