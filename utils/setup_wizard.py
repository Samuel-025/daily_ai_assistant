"""First-time setup wizard — interactive CLI configuration with Rich UI"""

import json
import os
from pathlib import Path
from config.settings import Settings

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm
    from rich import box
    RICH = True
except ImportError:
    RICH = False

console = Console() if RICH else None


class SetupWizard:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.base_dir = Path(__file__).parent.parent

    def run(self):
        if RICH:
            console.print(Panel.fit(
                "[bold yellow]🌅  Daily AI Assistant — First-Time Setup[/bold yellow]\n"
                "[dim]Press Enter to keep the default shown in brackets[/dim]",
                border_style="yellow", padding=(0, 2)
            ))
        else:
            print("\n" + "═" * 55)
            print("  🌅  Daily AI Assistant — First-Time Setup")
            print("═" * 55)
            print("  Press Enter to keep the default value shown in [ ]\n")

        def ask(label, default):
            if RICH:
                val = Prompt.ask(f"  [cyan]{label}[/cyan]", default=default)
            else:
                val = input(f"  {label} [{default}]: ").strip()
            return val if val else default

        # ── User info ──
        if RICH: console.print("\n[bold]👤 About You[/bold]")
        name       = ask("Your name", "User")
        wake_time  = ask("Wake-up time (HH:MM)", "07:00")
        city       = ask("Your city", self.settings.user_city)
        country    = ask("Your country code (e.g. IN, US)", self.settings.user_country)
        fitness    = ask("Fitness level (low/moderate/high)", "moderate")
        work_focus = ask("Work focus / domain", "general")
        diet_type  = ask("Diet type (balanced/vegetarian/vegan/keto)", "balanced")

        # ── LLM Provider ──
        if RICH:
            console.print("\n[bold]🤖 LLM Provider[/bold]")
            console.print("  [dim]1) ollama    — local, free, private (recommended)[/dim]")
            console.print("  [dim]2) groq      — cloud, fast, free tier[/dim]")
            console.print("  [dim]3) openai    — cloud, GPT-4o[/dim]")
            console.print("  [dim]4) anthropic — cloud, Claude[/dim]")
            console.print("  [dim]5) cohere    — cloud, free tier[/dim]")
        else:
            print("\n  LLM Provider Options:")
            print("  1) ollama  2) groq  3) openai  4) anthropic  5) cohere")
        provider = ask("Default provider", "groq")

        # ── API Keys ──
        if RICH:
            console.print("\n[bold]🔑 API Keys[/bold] [dim](press Enter to skip any)[/dim]")
        else:
            print("\n  API Keys (press Enter to skip):")

        env_lines = [
            f"OLLAMA_API_URL=http://localhost:11434",
            f"OLLAMA_DEFAULT_MODEL=llama3.2",
            f"DEFAULT_PROVIDER={provider}",
            f"USE_LOCAL_FIRST={'true' if provider == 'ollama' else 'false'}",
            f"USER_CITY={city}",
            f"USER_COUNTRY={country}",
        ]

        key_prompts = [
            ("OpenAI API Key",          "OPENAI_API_KEY"),
            ("Anthropic API Key",        "ANTHROPIC_API_KEY"),
            ("Groq API Key",             "GROQ_API_KEY"),
            ("Cohere API Key",           "COHERE_API_KEY"),
            ("OpenWeatherMap API Key",   "OPENWEATHER_API_KEY"),
            ("NewsAPI Key",              "NEWS_API_KEY"),
        ]
        for label, env_var in key_prompts:
            if RICH:
                val = Prompt.ask(f"  [cyan]{label}[/cyan]", default="", password=("KEY" in env_var or "TOKEN" in env_var))
            else:
                val = input(f"  {label}: ").strip()
            if val:
                env_lines.append(f"{env_var}={val}")

        # ── Write .env ──
        env_path = self.base_dir / ".env"
        env_path.write_text("\n".join(env_lines) + "\n", encoding="utf-8")

        # ── Write preferences ──
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
        (prefs_dir / "user_prefs.json").write_text(json.dumps(prefs, indent=2), encoding="utf-8")

        if RICH:
            console.print(Panel(
                f"[green]✅ Setup complete![/green]\n"
                f"  .env written to [cyan]{env_path}[/cyan]\n\n"
                "  [bold]Run the assistant:[/bold]\n"
                "    [yellow]python main.py[/yellow]          ← Interactive menu\n"
                "    [yellow]python main.py --chat[/yellow]   ← Jump to chat\n"
                "    [yellow]streamlit run streamlit_app.py[/yellow]  ← Web UI",
                border_style="green", padding=(0, 2)
            ))
        else:
            print("\n  ✅ Setup complete!")
            print(f"  .env → {env_path}")
            print("  Run: python main.py")

    def _ask(self, label: str, default: str) -> str:
        val = input(f"  {label} [{default}]: ").strip()
        return val if val else default
