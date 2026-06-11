"""Daily Orchestrator - Coordinates all daily modules"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
from models.llm_manager import LLMManager

class DailyOrchestrator:
    """Orchestrate daily life modules"""

    def __init__(self, llm_manager: LLMManager):
        self.llm = llm_manager
        self.base_dir = Path(__file__).parent.parent
        self.preferences_dir = self.base_dir / "preferences"
        self.tasks_dir = self.base_dir / "tasks"
        self.habits_dir = self.base_dir / "habits"
        self.journal_dir = self.base_dir / "journal"
        self.meals_dir = self.base_dir / "meals"
        for d in [self.preferences_dir, self.tasks_dir, self.habits_dir, self.journal_dir, self.meals_dir]:
            d.mkdir(exist_ok=True)

    def load_preferences(self) -> Dict[str, Any]:
        prefs_file = self.preferences_dir / "user_prefs.json"
        if prefs_file.exists():
            with open(prefs_file) as f:
                return json.load(f)
        defaults = {
            "name": "User",
            "wake_time": "07:00",
            "sleep_time": "23:00",
            "preferences": {
                "morning_routine": True,
                "task_prioritization": "ai",
                "habit_tracking": True,
                "daily_journal": True,
                "meal_planning": True,
                "weather_suggestions": True,
            },
            "dietary": {"type": "balanced", "restrictions": [], "preferences": []},
            "fitness_level": "moderate",
            "work_focus": "general",
        }
        with open(prefs_file, "w") as f:
            json.dump(defaults, f, indent=2)
        return defaults

    def save_preferences(self, prefs: Dict[str, Any]):
        prefs_file = self.preferences_dir / "user_prefs.json"
        with open(prefs_file, "w") as f:
            json.dump(prefs, f, indent=2)

    def run_morning_routine(self, prefs: Dict[str, Any]):
        if not prefs["preferences"]["morning_routine"]:
            return
        prompt = f"""Create a personalized morning routine for {prefs['name']} who wakes at {prefs['wake_time']}.
Fitness level: {prefs['fitness_level']}. Work focus: {prefs['work_focus']}.
Include: hydration, exercise, mindfulness, breakfast, work prep. Be concise and actionable."""
        result = self.llm.generate(prompt)
        print("\n\U0001f305 MORNING ROUTINE:")
        print(result or "Start with hydration, light stretching, and a healthy breakfast!")

    def run_task_manager(self, prefs: Dict[str, Any]):
        tasks_file = self.tasks_dir / "today_tasks.json"
        tasks = json.loads(tasks_file.read_text()) if tasks_file.exists() else {"tasks": [], "completed": []}
        print("\n\U0001f4cb TODAY'S TASKS:")
        print(f"Active: {len(tasks['tasks'])} | Completed: {len(tasks['completed'])}")
        if prefs["preferences"]["task_prioritization"] == "ai" and tasks["tasks"]:
            prompt = f"Prioritize these tasks for {prefs['name']} (focus: {prefs['work_focus']}):\n- " + "\n- ".join(tasks["tasks"])
            result = self.llm.generate(prompt)
            print("\n\u2728 AI PRIORITY ORDER:")
            print(result or "Complete in order of urgency and importance.")

    def run_habit_tracker(self, prefs: Dict[str, Any]):
        if not prefs["preferences"]["habit_tracking"]:
            return
        habits_file = self.habits_dir / "current_habits.json"
        habits = json.loads(habits_file.read_text()) if habits_file.exists() else {
            "habits": [
                {"name": "Drink water", "streak": 0, "target": 1},
                {"name": "Exercise 20min", "streak": 0, "target": 1},
                {"name": "Read 10min", "streak": 0, "target": 1},
            ]
        }
        print("\n\U0001f3af HABITS TODAY:")
        for h in habits["habits"]:
            status = "\u2713" if h["streak"] >= h["target"] else "\u25cb"
            print(f"{status} {h['name']} (Streak: {h['streak']})")

    def run_journal(self, prefs: Dict[str, Any]):
        if not prefs["preferences"]["daily_journal"]:
            return
        print("\n\U0001f4dd DAILY JOURNAL:")
        print("What went well today? What would you improve?")
        entries = list(self.journal_dir.glob("*.json"))
        if len(entries) > 1:
            prompt = f"Analyze journal entries for {prefs['name']} and give: patterns, improvements, highlights. Be encouraging."
            result = self.llm.generate(prompt)
            print("\n\u2728 AI INSIGHTS:")
            print(result or "Keep journaling consistently for better self-awareness!")

    def run_meal_planner(self, prefs: Dict[str, Any]):
        if not prefs["preferences"]["meal_planning"]:
            return
        d = prefs["dietary"]
        prompt = f"""Create a meal plan for {prefs['name']}.
Diet: {d['type']}, Restrictions: {d['restrictions']}, Preferences: {d['preferences']}.
Fitness: {prefs['fitness_level']}. Include breakfast, lunch, dinner, snacks."""
        result = self.llm.generate(prompt)
        print("\n\U0001f37d\ufe0f MEAL PLAN:")
        print(result or "Eat balanced meals with protein, veggies, and whole grains!")

    def run_weather_suggestions(self, prefs: Dict[str, Any]):
        if not prefs["preferences"]["weather_suggestions"]:
            return
        prompt = f"""Suggest today's activities for {prefs['name']} in Vasind, Maharashtra, India.
Fitness: {prefs['fitness_level']}. Include outdoor/indoor options and timing."""
        result = self.llm.generate(prompt)
        print("\n\U0001f324\ufe0f ACTIVITY SUGGESTIONS:")
        print(result or "Check weather and plan outdoor activities accordingly!")

    def update_api_keys(self, keys: Dict[str, str]):
        for provider, key in keys.items():
            if key:
                self.llm.set_api_key(provider, key)
