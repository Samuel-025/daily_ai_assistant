"""First-time setup wizard — interactive CLI configuration with Rich UI"""

import json
import os
from pathlib import Path
from config.settings import Settings

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Prompt
    RICH = True
    console = Console()
except ImportError:
    RICH = False
    console = None  # type: ignore[assignment]

VALID_PROVIDERS = ["ollama", "openai", "anthropic", "groq", "cohere"]


class SetupWizard:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.base_dir = Path(__file__).parent.parent

    def run(self):
        if RICH and console:
            console.print(Panel.fit(
                "[bold yellow]\U0001f305  Daily AI Assistant \u2014 First-Time Setup[/bold yellow]\n"
                "[dim]Press Enter to keep the default shown in brackets[/dim]",
                border_style="yellow", padding=(0, 2)
            ))
        else:
            print("\n" + "\u2550" * 55)
            print("  \U0001f305  Daily AI Assistant \u2014 First-Time Setup")
            print("\u2550" * 55 + "\n")

        def ask(label, default):
            if RICH and console:
                val = Prompt.ask(f"  [cyan]{label}[/cyan]", default=str(default))
            else:
                val = input(f"  {label} [{default}]: ").strip()
            return val.strip() if val.strip() else str(default)

        # ── User info ──
        if RICH and console:
            console.print("\n[bold]\U0001f464 About You[/bold]")
        name       = ask("Your name", "User")
        wake_time  = ask("Wake-up time (HH:MM)", "07:00")
        city       = ask("Your city", self.settings.user_city)
        country    = ask("Your country code (e.g. IN, US)", self.settings.user_country)
        fitness    = ask("Fitness level (low/moderate/high)", "moderate")
        work_focus = ask("Work focus / domain", "general")
        diet_type  = ask("Diet type (balanced/vegetarian/vegan/keto)", "balanced")

        # ── LLM Provider ──
        if RICH and console:
            console.print("\n[bold]\U0001f916 LLM Provider[/bold]")
            console.print("  [dim]ollama    \u2014 local, free, private (recommended)[/dim]")
            console.print("  [dim]groq      \u2014 cloud, fast, free tier[/dim]")
            console.print("  [dim]openai    \u2014 cloud, GPT-4o[/dim]")
            console.print("  [dim]anthropic \u2014 cloud, Claude[/dim]")
            console.print("  [dim]cohere    \u2014 cloud, free tier[/dim]")
        else:
            print("\n  LLM Providers: ollama | groq | openai | anthropic | cohere")

        # Validate provider with retry loop
        while True:
            provider = ask("Default provider (type exactly as shown above)", "groq").lower().strip()
            if provider in VALID_PROVIDERS:
                break
            if RICH and console:
                console.print(f"  [red]\u274c '{provider}' is not valid.[/red] "
                              f"Choose from: [yellow]{', '.join(VALID_PROVIDERS)}[/yellow]")
            else:
                print(f"  Invalid provider '{provider}'. Choose from: {', '.join(VALID_PROVIDERS)}")

        # ── API Keys ──
        if RICH and console:
            console.print("\n[bold]\U0001f511 API Keys[/bold] [dim](press Enter to skip any)[/dim]")
        else:
            print("\n  API Keys (press Enter to skip):")

        env_lines = [
            "OLLAMA_API_URL=http://localhost:11434",
            "OLLAMA_DEFAULT_MODEL=llama3.2",
            f"DEFAULT_PROVIDER={provider}",
            f"USE_LOCAL_FIRST={'true' if provider == 'ollama' else 'false'}",
            f"USER_CITY={city}",
            f"USER_COUNTRY={country}",
        ]

        key_prompts = [
            ("OpenAI API Key",         "OPENAI_API_KEY"),
            ("Anthropic API Key",       "ANTHROPIC_API_KEY"),
            ("Groq API Key",            "GROQ_API_KEY"),
            ("Cohere API Key",          "COHERE_API_KEY"),
            ("OpenWeatherMap API Key",  "OPENWEATHER_API_KEY"),
            ("NewsAPI Key",             "NEWS_API_KEY"),
        ]
        for label, env_var in key_prompts:
            if RICH and console:
                val = Prompt.ask(f"  [cyan]{label}[/cyan]", default="")
            else:
                val = input(f"  {label}: ").strip()
            if val.strip():
                env_lines.append(f"{env_var}={val.strip()}")

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

        if RICH and console:
            console.print(Panel(
                f"[green]\u2705 Setup complete![/green]\n"
                f"  .env written \u2192 [cyan]{env_path}[/cyan]\n\n"
                "  [bold]Run the assistant:[/bold]\n"
                "    [yellow]python main.py[/yellow]           \u2190 Interactive menu\n"
                "    [yellow]python main.py --chat[/yellow]    \u2190 Jump to chat\n"
                "    [yellow]streamlit run streamlit_app.py[/yellow]  \u2190 Web UI",
                border_style="green", padding=(0, 2)
            ))
        else:
            print("\n  \u2705 Setup complete!")
            print(f"  .env \u2192 {env_path}")
            print("  Run: python main.py")

    def _ask(self, label: str, default: str) -> str:
        val = input(f"  {label} [{default}]: ").strip()
        return val if val else default
