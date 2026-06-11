#!/usr/bin/env python3
"""
Daily AI Assistant - All-in-one personalized daily life tool
Integrates Ollama (local) + cloud models via API keys
"""

from dotenv import load_dotenv
from config.settings import Settings
from models.llm_manager import LLMManager
from utils.daily_orchestrator import DailyOrchestrator

load_dotenv()

class DailyAIAssistant:
    def __init__(self):
        self.settings = Settings()
        self.llm_manager = LLMManager(self.settings)
        self.orchestrator = DailyOrchestrator(self.llm_manager)

    def run(self):
        print("\U0001f305 Daily AI Assistant - Personalized for You")
        print("=" * 50)
        user_prefs = self.orchestrator.load_preferences()
        self.orchestrator.run_morning_routine(user_prefs)
        self.orchestrator.run_task_manager(user_prefs)
        self.orchestrator.run_habit_tracker(user_prefs)
        self.orchestrator.run_journal(user_prefs)
        self.orchestrator.run_meal_planner(user_prefs)
        self.orchestrator.run_weather_suggestions(user_prefs)
        print("=" * 50)
        print("\u2705 Daily tasks completed! Have a great day!")

def main():
    assistant = DailyAIAssistant()
    assistant.run()

if __name__ == "__main__":
    main()
