#!/usr/bin/env python3
"""
Daily AI Assistant v3.1  -  CLI Edition
Rich terminal UI + Interactive menu + Chat mode

Usage:
  python main.py               # Interactive menu
  python main.py --chat        # Jump straight to chat
  python main.py --module morning
  python main.py --setup       # First-time setup wizard
  python main.py --list-models # List Ollama models
  python main.py --tasks       # Open task manager directly
  python main.py --habits      # Show habit visualization directly
"""

import argparse
import os
from dotenv import load_dotenv
from pathlib import Path
from typing import Protocol

load_dotenv()


class _ConsoleLike(Protocol):
    """Structural type so Pylance knows console always has .print()."""
    def print(self, *args: object, **kwargs: object) -> None: ...


try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    from rich.columns import Columns
    from rich import box
    RICH = True
    console: _ConsoleLike = Console()  # type: ignore[assignment]
except ImportError:
    RICH = False

    class _FallbackConsole:
        def print(self, *args: object, **kwargs: object) -> None:
            print(*args)

    console: _ConsoleLike = _FallbackConsole()  # type: ignore[assignment,misc]


def rprint(msg, style=""):
    if RICH:
        console.print(msg, style=style)
    else:
        print(msg)

def banner():
    if RICH:
        console.print(Panel.fit(
            "[bold yellow]\U0001f305  Daily AI Assistant[/bold yellow]  [dim]v3.1 CLI[/dim]\n"
            "[dim]ChatGPT-style  \u00b7  Private  \u00b7  Multi-provider[/dim]",
            border_style="yellow", padding=(0, 2)
        ))
    else:
        print("\n" + "=" * 50)
        print("  Daily AI Assistant v3.1 CLI")
        print("=" * 50)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Daily AI Assistant - Rich CLI v3.1"
    )
    parser.add_argument("--setup",       action="store_true", help="Run first-time setup wizard")
    parser.add_argument("--chat",        action="store_true", help="Start interactive chat mode")
    parser.add_argument("--tasks",       action="store_true", help="Open task manager")
    parser.add_argument("--habits",      action="store_true", help="Show habit visualization")
    parser.add_argument("--module",      type=str,            help="Run a specific module directly")
    parser.add_argument("--provider",    type=str, default=None, help="Force LLM provider")
    parser.add_argument("--list-models", action="store_true", help="List available Ollama models")
    return parser.parse_args()


MENU_ITEMS = [
    ("1",  "\U0001f305  Morning Routine",      "morning"),
    ("2",  "\U0001f4cb  Task Manager",          "tasks"),
    ("3",  "\U0001f3af  Habit Tracker",         "habits"),
    ("4",  "\U0001f4dd  Journal",               "journal"),
    ("5",  "\U0001f37d   Meal Planner",          "meals"),
    ("6",  "\U0001f324   Weather & Activities",  "weather"),
    ("7",  "\U0001f4f0  News Briefing",          "news"),
    ("8",  "\u23f1   Focus Schedule",            "focus"),
    ("9",  "\U0001f514  Reminders",              "reminders"),
    ("10", "\U0001f4a1  Motivational Quote",     "quote"),
    ("A",  "\U0001f31f  Run ALL modules",         "all"),
    ("C",  "\U0001f4ac  Chat Mode",               "chat"),
    ("Q",  "\U0001f6aa  Quit",                    "quit"),
]

def show_menu(name: str):
    if RICH:
        from rich.table import Table
        t = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
        t.add_column(style="bold cyan", width=4)
        t.add_column(style="white")
        for key, label, _ in MENU_ITEMS:
            t.add_row("[" + key + "]", label)
        console.print("\n[bold]Good day, [yellow]" + name + "[/yellow]! What would you like to do?[/bold]")
        console.print(t)
    else:
        print("\nGood day, " + name + "! What would you like to do?")
        for key, label, _ in MENU_ITEMS:
            print("  [" + key + "] " + label)

def get_choice() -> str:
    if RICH:
        console.print("[dim]Enter choice: [/dim]", end="")
    else:
        print("Enter choice: ", end="")
    return input().strip().upper()


def main():
    args = parse_args()

    from config.settings import Settings
    from models.llm_manager import LLMManager
    from utils.setup_wizard import SetupWizard
    from utils.daily_orchestrator import DailyOrchestrator
    from utils.cli_chat import CLIChat
    from utils.task_manager import run_task_manager
    from utils.habit_viz import show_habit_viz
    from utils.reminder_daemon import start_reminders, stop_reminders

    settings = Settings()
    llm      = LLMManager(settings)

    if args.provider:
        settings.default_provider = args.provider

    if args.setup:
        wizard = SetupWizard(settings)
        wizard.run()
        return

    if args.list_models:
        models = llm.list_ollama_models()
        if RICH:
            console.print("\n[bold]\U0001f4e6 Available Ollama Models:[/bold]")
            for m in models:
                console.print("  [cyan]\u2022[/cyan] " + m)
        else:
            print("\nAvailable Ollama Models:")
            for m in models:
                print("  - " + m)
        return

    # Direct flags
    if args.tasks:
        run_task_manager()
        return

    if args.habits:
        show_habit_viz()
        return

    banner()

    # Start background reminders
    start_reminders()

    orch  = DailyOrchestrator(llm, provider=args.provider or settings.default_provider)
    prefs = orch.load_preferences()
    name  = prefs.get("name", "User")

    if args.chat:
        chat = CLIChat(orch, prefs)
        chat.run()
        stop_reminders()
        return

    if args.module:
        orch.run_module(args.module, prefs)
        stop_reminders()
        return

    module_map = {key: mod for key, _, mod in MENU_ITEMS}
    while True:
        show_menu(name)
        choice = get_choice()
        mod    = module_map.get(choice)

        if mod is None:
            rprint("[red]Invalid choice, try again.[/red]" if RICH else "Invalid choice.")
        elif mod == "quit":
            rprint("\n[bold yellow]Goodbye! Have a great day! \U0001f305[/bold yellow]" if RICH else "\nGoodbye!")
            stop_reminders()
            break
        elif mod == "chat":
            chat = CLIChat(orch, prefs)
            chat.run()
        elif mod == "tasks":
            run_task_manager()
        elif mod == "habits":
            show_habit_viz()
            orch.run_module("habits", prefs)
        elif mod == "all":
            for _, _, m in MENU_ITEMS:
                if m not in ("all", "chat", "quit"):
                    if m == "tasks":
                        run_task_manager()
                    elif m == "habits":
                        show_habit_viz()
                    else:
                        orch.run_module(m, prefs)
        else:
            orch.run_module(mod, prefs)

        if RICH:
            console.print("\n[dim]Press Enter to return to menu...[/dim]", end="")
        else:
            print("\nPress Enter to return to menu...", end="")
        input()


if __name__ == "__main__":
    main()
