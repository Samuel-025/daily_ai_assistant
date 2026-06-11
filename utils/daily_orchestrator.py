"""Daily Orchestrator — coordinates all daily modules"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from models.llm_manager import LLMManager
from utils.weather import get_weather
from utils.news import get_news_briefing
from utils.reminders import ReminderManager


class DailyOrchestrator:
    def __init__(self, llm_manager: LLMManager, provider: Optional[str] = None):
        self.llm      = llm_manager
        self.provider = provider
        self.base_dir = Path(__file__).parent.parent
        self.prefs_dir    = self.base_dir / "preferences"
        self.tasks_dir    = self.base_dir / "tasks"
        self.habits_dir   = self.base_dir / "habits"
        self.journal_dir  = self.base_dir / "journal"
        self.meals_dir    = self.base_dir / "meals"
        self.reminder_mgr = ReminderManager(self.base_dir / "reminders")

    def _gen(self, prompt: str) -> str:
        result = self.llm.generate(prompt, provider=self.provider)
        return result or "(No AI response — check your provider config)"

    # ── Preferences ───────────────────────────────────
    def load_preferences(self) -> Dict[str, Any]:
        f = self.prefs_dir / "user_prefs.json"
        if f.exists():
            return json.loads(f.read_text())
        defaults = {
            "name": "User",
            "wake_time": "07:00",
            "sleep_time": "23:00",
            "timezone": "Asia/Kolkata",
            "preferences": {
                "morning_routine": True,
                "task_prioritization": "ai",
                "habit_tracking": True,
                "daily_journal": True,
                "meal_planning": True,
                "weather_suggestions": True,
                "news_briefing": True,
                "focus_timer": True,
                "reminders": True,
                "motivational_quote": True,
            },
            "dietary": {"type": "balanced", "restrictions": [], "preferences": []},
            "fitness_level": "moderate",
            "work_focus": "general",
            "interests": [],
            "news_categories": ["technology", "health"],
        }
        self.prefs_dir.mkdir(exist_ok=True)
        f.write_text(json.dumps(defaults, indent=2))
        return defaults

    def save_preferences(self, prefs: Dict[str, Any]):
        f = self.prefs_dir / "user_prefs.json"
        f.write_text(json.dumps(prefs, indent=2))

    # ── Morning Routine ───────────────────────────────
    def run_morning_routine(self, prefs: Dict[str, Any]):
        if not prefs["preferences"].get("morning_routine"):
            return
        print("\n🌅 MORNING ROUTINE")
        print(self._gen(
            f"Give a concise, energizing morning routine for {prefs['name']} "
            f"who wakes at {prefs['wake_time']}. Fitness: {prefs['fitness_level']}. "
            f"Work focus: {prefs['work_focus']}. Include hydration, movement, mindfulness, breakfast."
        ))

    # ── Tasks ─────────────────────────────────────────
    def run_task_manager(self, prefs: Dict[str, Any]):
        self.tasks_dir.mkdir(exist_ok=True)
        f = self.tasks_dir / "today_tasks.json"
        tasks = json.loads(f.read_text()) if f.exists() else {"tasks": [], "completed": []}
        print(f"\n📋 TASKS  (Active: {len(tasks['tasks'])} | Done: {len(tasks['completed'])})")
        if tasks["tasks"] and prefs["preferences"].get("task_prioritization") == "ai":
            task_list = "\n- ".join(tasks["tasks"])
            print("\n✨ AI PRIORITY ORDER:")
            print(self._gen(
                f"Prioritize and add brief notes for these tasks (focus: {prefs['work_focus']}):\n- {task_list}"
            ))
        elif not tasks["tasks"]:
            print("  No tasks yet. Add tasks to tasks/today_tasks.json")

    # ── Habits ────────────────────────────────────────
    def run_habit_tracker(self, prefs: Dict[str, Any]):
        if not prefs["preferences"].get("habit_tracking"):
            return
        self.habits_dir.mkdir(exist_ok=True)
        f = self.habits_dir / "current_habits.json"
        habits = json.loads(f.read_text()) if f.exists() else {
            "habits": [
                {"name": "Drink 8 glasses of water", "streak": 0, "target": 1},
                {"name": "Exercise 20 min",           "streak": 0, "target": 1},
                {"name": "Read 10 min",               "streak": 0, "target": 1},
                {"name": "Meditate 5 min",            "streak": 0, "target": 1},
                {"name": "Sleep by 11 PM",            "streak": 0, "target": 1},
            ]
        }
        print("\n🎯 HABIT TRACKER")
        for h in habits["habits"]:
            bar   = "█" * min(h["streak"], 10) + "░" * (10 - min(h["streak"], 10))
            check = "✓" if h["streak"] >= h["target"] else "○"
            print(f"  {check} {h['name']:<30} [{bar}] streak: {h['streak']}")

    # ── Journal ───────────────────────────────────────
    def run_journal(self, prefs: Dict[str, Any]):
        if not prefs["preferences"].get("daily_journal"):
            return
        self.journal_dir.mkdir(exist_ok=True)
        print("\n📝 DAILY JOURNAL")
        entries = sorted(self.journal_dir.glob("*.json"))
        if len(entries) >= 3:
            print("\n✨ AI INSIGHTS from your recent journal entries:")
            print(self._gen(
                f"Based on consistent journaling by {prefs['name']}, provide: "
                "1) 3 positive patterns noticed, 2) 1 key area to improve, 3) an encouraging message. Be warm and concise."
            ))
        else:
            print(f"  Journal today → create a file in journal/{datetime.now().strftime('%Y-%m-%d')}.json")
            print("  Format: {\"entry\": \"your text here\", \"mood\": \"good\"}")

    # ── Meal Planner ──────────────────────────────────
    def run_meal_planner(self, prefs: Dict[str, Any]):
        if not prefs["preferences"].get("meal_planning"):
            return
        d = prefs["dietary"]
        print("\n🍽️  MEAL PLAN")
        print(self._gen(
            f"Create a healthy one-day meal plan for {prefs['name']}.\n"
            f"Diet: {d['type']}, Restrictions: {d['restrictions']}, Preferences: {d['preferences']}.\n"
            f"Fitness: {prefs['fitness_level']}. Include breakfast, lunch, dinner, 2 snacks, and water intake goal."
        ))

    # ── Weather ───────────────────────────────────────
    def run_weather_suggestions(self, prefs: Dict[str, Any]):
        if not prefs["preferences"].get("weather_suggestions"):
            return
        settings  = self.llm.settings
        city      = settings.user_city
        country   = settings.user_country
        weather   = get_weather(settings.get_api_key("weather"), city, country)
        print("\n🌤️  WEATHER & ACTIVITY SUGGESTIONS")
        if weather:
            print(f"  📍 {city}: {weather['description']}, {weather['temp']}°C | Humidity: {weather['humidity']}%")
            context = f"Weather in {city}: {weather['description']}, {weather['temp']}°C."
        else:
            context = f"Location: {city}, {country}. (No live weather data)"
        print(self._gen(
            f"{context} Suggest 3 activities for {prefs['name']} (fitness: {prefs['fitness_level']}). "
            "Include indoor & outdoor, and what to wear."
        ))

    # ── News Briefing ─────────────────────────────────
    def run_news_briefing(self, prefs: Dict[str, Any]):
        if not prefs["preferences"].get("news_briefing"):
            return
        settings  = self.llm.settings
        headlines = get_news_briefing(settings.get_api_key("news"), prefs.get("news_categories", []))
        print("\n📰 NEWS BRIEFING")
        if headlines:
            brief = "\n".join(f"• {h}" for h in headlines[:5])
            print(self._gen(
                f"Summarize these headlines in 3 short bullet points for {prefs['name']}:\n{brief}"
            ))
        else:
            print(self._gen(
                f"Give a brief 3-bullet summary of major world & tech news today for {prefs['name']} "
                f"interested in: {', '.join(prefs.get('news_categories', ['technology', 'science']))}."
            ))

    # ── Focus Timer ───────────────────────────────────
    def run_focus_timer(self, prefs: Dict[str, Any]):
        if not prefs["preferences"].get("focus_timer"):
            return
        print("\n⏱️  FOCUS PLANNER")
        print(self._gen(
            f"Create a Pomodoro-based focus schedule for {prefs['name']} (work: {prefs['work_focus']}).\n"
            "Include: 4 focus blocks of 25 min, short & long breaks, suggested tasks per block, and an energy tip."
        ))

    # ── Reminders ─────────────────────────────────────
    def run_reminders(self, prefs: Dict[str, Any]):
        if not prefs["preferences"].get("reminders"):
            return
        reminders = self.reminder_mgr.get_due_today()
        print("\n🔔 REMINDERS")
        if reminders:
            for r in reminders:
                print(f"  ⏰ {r['time']}  →  {r['message']}")
        else:
            print("  No reminders for today. Add them to reminders/reminders.json")
            print('  Format: [{"time": "09:00", "message": "Take medicine", "date": "daily"}]')

    # ── Motivational Quote ────────────────────────────
    def run_motivational_quote(self, prefs: Dict[str, Any]):
        if not prefs["preferences"].get("motivational_quote"):
            return
        print("\n💡 QUOTE OF THE DAY")
        print(self._gen(
            f"Give one powerful, original motivational quote for {prefs['name']} "
            f"whose focus is {prefs['work_focus']}. Include the author if it's a real quote."
        ))
