"""Daily Orchestrator - coordinates all daily modules

Fix (v3.0): _ask_ai() now calls providers directly with proper
chat-message format instead of the flat-string LLMManager.generate().
"""

import json
import os
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from models.llm_manager import LLMManager
from utils.weather import get_weather
from utils.news import get_news_briefing
from utils.reminders import ReminderManager

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.markdown import Markdown
    from rich.rule import Rule
    from rich import box
    RICH = True
except ImportError:
    RICH = False

console = Console()


class DailyOrchestrator:
    def __init__(self, llm_manager: LLMManager, provider: Optional[str] = None):
        self.llm      = llm_manager
        self.provider = provider or llm_manager.settings.default_provider
        self.base_dir = Path(__file__).parent.parent
        self.data_dir = self.base_dir / "demo_data"   # shared with Streamlit
        self.data_dir.mkdir(exist_ok=True)
        self.prefs_dir    = self.base_dir / "preferences"
        self.tasks_dir    = self.base_dir / "tasks"
        self.habits_dir   = self.base_dir / "habits"
        self.journal_dir  = self.base_dir / "journal"
        self.meals_dir    = self.base_dir / "meals"
        self.reminder_mgr = ReminderManager(self.base_dir / "reminders")

    # ── Direct provider calls (same pattern as streamlit_app.py) ──
    def _ask_ai(self, messages: list) -> str:
        """Call the selected provider with a proper messages list."""
        provider = self.provider
        settings = self.llm.settings

        def get_key(p):
            return settings.get_api_key(p) or os.environ.get(p.upper() + "_API_KEY", "")

        try:
            if provider == "ollama":
                url   = str(settings.api_keys.get("ollama") or "http://localhost:11434")
                model = str(settings.default_models.get("ollama") or "llama3.2")
                r = requests.post(
                    url + "/api/chat",
                    json={"model": model, "messages": messages, "stream": False},
                    timeout=120,
                )
                if r.ok:
                    return r.json().get("message", {}).get("content", "") or "(empty response)"
                return "(Ollama error: " + str(r.status_code) + ")"

            elif provider == "groq":
                from groq import Groq
                key = get_key("groq")
                if not key: return "(No Groq API key. Run python main.py --setup)"
                client = Groq(api_key=key)
                resp = client.chat.completions.create(
                    model=str(settings.default_models.get("groq") or "llama-3.3-70b-versatile"),
                    messages=messages,
                )
                return resp.choices[0].message.content or ""

            elif provider == "openai":
                import openai
                key = get_key("openai")
                if not key: return "(No OpenAI API key. Run python main.py --setup)"
                client = openai.OpenAI(api_key=key)
                resp = client.chat.completions.create(
                    model=str(settings.default_models.get("openai") or "gpt-4o"),
                    messages=messages,
                )
                return resp.choices[0].message.content or ""

            elif provider == "anthropic":
                import anthropic
                key = get_key("anthropic")
                if not key: return "(No Anthropic API key. Run python main.py --setup)"
                sys_msg   = next((m["content"] for m in messages if m["role"] == "system"), "")
                chat_msgs = [m for m in messages if m["role"] != "system"]
                client = anthropic.Anthropic(api_key=key)
                resp = client.messages.create(
                    model=str(settings.default_models.get("anthropic") or "claude-3-5-sonnet-20241022"),
                    max_tokens=2048, system=sys_msg, messages=chat_msgs,
                )
                # Only TextBlock has .text; guard against ThinkingBlock / ToolUseBlock etc.
                text = getattr(resp.content[0], "text", None) if resp.content else None
                return str(text) if isinstance(text, str) else "(empty response)"

            elif provider == "cohere":
                import cohere
                key = get_key("cohere")
                if not key: return "(No Cohere API key. Run python main.py --setup)"
                client = cohere.ClientV2(key)
                resp = client.chat(
                    model=str(settings.default_models.get("cohere") or "command-a-03-2025"),
                    messages=messages,
                )
                # Guard against None content and ThinkingAssistantMessageResponseContentItem
                content = resp.message.content if resp.message else None
                if content:
                    text = getattr(content[0], "text", None)
                    if isinstance(text, str):
                        return text
                return "(empty response)"

            else:
                return f"(Unknown provider: {provider})"

        except requests.exceptions.ConnectionError:
            return "(Ollama not running. Start it: ollama serve)"
        except Exception as e:
            return f"(Error [{provider}]: {e})"

    def _gen(self, prompt: str, system: Optional[str] = None) -> str:
        """Convenience: build messages list and call _ask_ai."""
        sys_content: str = system or (
            "You are a warm, practical daily AI assistant. "
            "Be concise, use markdown formatting."
        )
        messages = [
            {"role": "system", "content": sys_content},
            {"role": "user",   "content": prompt},
        ]
        return self._ask_ai(messages)

    def _header(self, title: str):
        if RICH:
            console.print(Rule(f"[bold yellow]{title}[/bold yellow]", style="yellow"))
        else:
            print(f"\n{'='*50}\n  {title}\n{'='*50}")

    def _print(self, text: str):
        if RICH:
            try:
                console.print(Markdown(text))
            except Exception:
                console.print(text)
        else:
            print(text)

    # ── Preferences ─────────────────────────────────────────────
    def load_preferences(self) -> Dict[str, Any]:
        f = self.prefs_dir / "user_prefs.json"
        if f.exists():
            try: return json.loads(f.read_text(encoding="utf-8"))
            except: pass
        defaults = {
            "name": "User", "wake_time": "07:00", "sleep_time": "23:00",
            "timezone": "Asia/Kolkata",
            "preferences": {
                "morning_routine": True, "task_prioritization": "ai",
                "habit_tracking": True, "daily_journal": True,
                "meal_planning": True, "weather_suggestions": True,
                "news_briefing": True, "focus_timer": True,
                "reminders": True, "motivational_quote": True,
            },
            "dietary": {"type": "balanced", "restrictions": [], "preferences": []},
            "fitness_level": "moderate",
            "work_focus": "general",
            "interests": [],
            "news_categories": ["technology", "health"],
        }
        self.prefs_dir.mkdir(exist_ok=True)
        f.write_text(json.dumps(defaults, indent=2), encoding="utf-8")
        return defaults

    def save_preferences(self, prefs: Dict[str, Any]):
        f = self.prefs_dir / "user_prefs.json"
        f.write_text(json.dumps(prefs, indent=2), encoding="utf-8")

    # ── Module dispatcher ──────────────────────────────────────────
    def run_module(self, module: str, prefs: Dict[str, Any]):
        modules = {
            "morning":   self.run_morning_routine,
            "tasks":     self.run_task_manager,
            "habits":    self.run_habit_tracker,
            "journal":   self.run_journal,
            "meals":     self.run_meal_planner,
            "weather":   self.run_weather_suggestions,
            "news":      self.run_news_briefing,
            "focus":     self.run_focus_timer,
            "reminders": self.run_reminders,
            "quote":     self.run_motivational_quote,
        }
        fn = modules.get(module)
        if fn:
            fn(prefs)
        else:
            print(f"Unknown module: {module}. Available: {', '.join(modules.keys())}")

    # ── Morning Routine ─────────────────────────────────────────
    def run_morning_routine(self, prefs: Dict[str, Any]):
        self._header("\U0001f305  MORNING ROUTINE")
        self._print(self._gen(
            f"Create a personalised morning routine for {prefs['name']} who wakes at {prefs['wake_time']}."
            f" Fitness: {prefs['fitness_level']}. Work focus: {prefs['work_focus']}."
            " Use time blocks (07:00-07:10 format). Include hydration, movement, mindfulness, breakfast."
        ))

    # ── Tasks ───────────────────────────────────────────────────
    def run_task_manager(self, prefs: Dict[str, Any]):
        self.tasks_dir.mkdir(exist_ok=True)
        f = self.tasks_dir / "today_tasks.json"
        td = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {"tasks": [], "completed": []}
        self._header(f"\U0001f4cb  TASKS  (Active: {len(td['tasks'])} | Done: {len(td['completed'])})")
        if td["tasks"]:
            task_list = "\n- ".join(td["tasks"])
            self._print(self._gen(
                f"Prioritise these tasks and add a 1-line action tip each (focus: {prefs['work_focus']}):\n- {task_list}"
            ))
        else:
            self._print("No tasks yet. Add tasks to `tasks/today_tasks.json`")

    # ── Habits ────────────────────────────────────────────────────
    def run_habit_tracker(self, prefs: Dict[str, Any]):
        self.habits_dir.mkdir(exist_ok=True)
        f = self.habits_dir / "current_habits.json"
        default_h = {"habits": [
            {"name": "Drink 8 glasses of water", "streak": 0, "target": 30},
            {"name": "Exercise 20 min",           "streak": 0, "target": 30},
            {"name": "Read 10 min",               "streak": 0, "target": 21},
            {"name": "Meditate 5 min",            "streak": 0, "target": 21},
            {"name": "Sleep by 11 PM",            "streak": 0, "target": 30},
        ]}
        hd = json.loads(f.read_text(encoding="utf-8")) if f.exists() else default_h
        self._header("\U0001f3af  HABIT TRACKER")
        for h in hd["habits"]:
            s = h.get("streak", 0)
            t = h.get("target", 30)
            pct = min(s / t, 1.0) if t else 0
            if RICH:
                from rich.progress import BarColumn, Progress, TextColumn
                bar = "\u2588" * int(pct * 20) + "\u2591" * (20 - int(pct * 20))
                check = "[green]\u2713[/green]" if s >= t else "[dim]\u25cb[/dim]"
                console.print(f"  {check} [white]{h['name']:<32}[/white] [{bar}] [cyan]{s}[/cyan]/[dim]{t}[/dim] days")
            else:
                bar = "#" * int(pct * 20) + "-" * (20 - int(pct * 20))
                print(f"  {'v' if s >= t else 'o'} {h['name']:<32} [{bar}] {s}/{t}")

    # ── Journal ──────────────────────────────────────────────────
    def run_journal(self, prefs: Dict[str, Any]):
        self.journal_dir.mkdir(exist_ok=True)
        today = datetime.now().strftime("%Y-%m-%d")
        jf    = self.journal_dir / f"{today}.json"
        self._header("\U0001f4dd  DAILY JOURNAL")
        if jf.exists():
            entry = json.loads(jf.read_text(encoding="utf-8")).get("entry", "")
            self._print(self._gen(
                f"Reflect on this journal entry by {prefs['name']} and give 2 insights + 1 encouragement:\n{entry}"
            ))
        else:
            print(f"  No journal entry for today yet.")
            print(f"  Create: journal/{today}.json")
            print('  Format: {"entry": "your text", "mood": "good"}')
            # Offer prompts
            self._print("\n**Journaling prompts for today:**")
            self._print(self._gen(
                f"Give {prefs['name']} 3 short, thoughtful journaling prompts for today. Work focus: {prefs['work_focus']}."
            ))

    # ── Meal Planner ────────────────────────────────────────────
    def run_meal_planner(self, prefs: Dict[str, Any]):
        d = prefs["dietary"]
        self._header("\U0001f37d   MEAL PLAN")
        self._print(self._gen(
            f"Create a healthy one-day meal plan for {prefs['name']}."
            f" Diet: {d['type']}, Restrictions: {d.get('restrictions', [])}, Preferences: {d.get('preferences', [])}."
            f" Fitness: {prefs['fitness_level']}. Include breakfast, lunch, dinner, 1 snack. Cuisine: Indian."
            " For each: name, key ingredients, kcal, prep time."
        ))

    # ── Weather & Activities ────────────────────────────────────
    def run_weather_suggestions(self, prefs: Dict[str, Any]):
        settings = self.llm.settings
        city     = settings.user_city
        country  = settings.user_country
        weather  = get_weather(settings.get_api_key("weather"), city, country)
        self._header("\U0001f324   WEATHER & ACTIVITIES")
        if weather:
            if RICH:
                console.print(f"  [bold]\U0001f4cd {city}:[/bold] {weather['description']}, "
                              f"[yellow]{weather['temp']}\u00b0C[/yellow] | Humidity: {weather['humidity']}%")
            else:
                print(f"  {city}: {weather['description']}, {weather['temp']}C | Humidity: {weather['humidity']}%")
            context = f"Weather in {city}: {weather['description']}, {weather['temp']}C."
        else:
            context = f"Location: {city}, {country}. (No live weather data available)"
        self._print(self._gen(
            f"{context} Suggest 3 activities for {prefs['name']} (fitness: {prefs['fitness_level']}). "
            "Mix indoor & outdoor. Include what to bring and duration."
        ))

    # ── News ──────────────────────────────────────────────────────
    def run_news_briefing(self, prefs: Dict[str, Any]):
        settings  = self.llm.settings
        headlines = get_news_briefing(settings.get_api_key("news"), prefs.get("news_categories", []))
        self._header("\U0001f4f0  NEWS BRIEFING")
        if headlines:
            brief = "\n".join(f"- {h}" for h in headlines[:5])
            self._print(self._gen(f"Summarise these headlines in 3 bullets for {prefs['name']}:\n{brief}"))
        else:
            self._print(self._gen(
                f"Give a concise 5-bullet news briefing for today covering: Technology, AI, Health. "
                f"For {prefs['name']} interested in: {', '.join(prefs.get('news_categories', ['technology']))}"
            ))

    # ── Focus Timer ────────────────────────────────────────────
    def run_focus_timer(self, prefs: Dict[str, Any]):
        self._header("\u23f1   FOCUS SCHEDULE")
        self._print(self._gen(
            f"Create a Pomodoro focus schedule for {prefs['name']} (work: {prefs['work_focus']})."
            " 4 blocks of 25 min with 5-min breaks + 1 long break (15 min) after block 4."
            " For each block: task, energy tip, distraction to avoid. Format as a clean timetable."
        ))

    # ── Reminders ───────────────────────────────────────────────
    def run_reminders(self, prefs: Dict[str, Any]):
        reminders = self.reminder_mgr.get_due_today()
        self._header("\U0001f514  REMINDERS")
        if reminders:
            for r in reminders:
                if RICH:
                    console.print(f"  [cyan]\u23f0 {r['time']}[/cyan]  \u2192  {r['message']}")
                else:
                    print(f"  {r['time']}  ->  {r['message']}")
        else:
            self._print("No reminders for today. Add them to `reminders/reminders.json`")
            self._print('Format: `[{"time": "09:00", "message": "Take medicine", "date": "daily"}]`')

    # ── Motivational Quote ─────────────────────────────────────────
    def run_motivational_quote(self, prefs: Dict[str, Any]):
        self._header("\U0001f4a1  QUOTE OF THE DAY")
        self._print(self._gen(
            f"Give one powerful quote for {prefs['name']} whose focus is {prefs['work_focus']}."
            " Format: 'Quote' - Author. Then personalise it in 2 warm sentences."
        ))
