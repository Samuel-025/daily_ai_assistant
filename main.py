#!/usr/bin/env python3
"""
Daily AI Assistant v3.0  -  CLI Edition
Rich terminal UI + Interactive menu + Chat mode

Usage:
  python main.py               # Interactive menu
  python main.py --chat        # Jump straight to chat
  python main.py --module morning
  python main.py --setup       # First-time setup wizard
  python main.py --list-models # List Ollama models
"""

import argparse
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# ── Rich imports ──────────────────────────────────────────────────
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    from rich.columns import Columns
    from rich import box
    RICH = True
except ImportError:
    RICH = False

console = Console() if RICH else None

def rprint(msg, style=""):
    if RICH:
        console.print(msg, style=style)
    else:
        print(msg)

def banner():
    if RICH:
        console.print(Panel.fit(
            "[bold yellow]\U0001f305  Daily AI Assistant[/bold yellow]  [dim]v3.0 CLI[/dim]\n"
            "[dim]ChatGPT-style  \u00b7  Private  \u00b7  Multi-provider[/dim]",
            border_style="yellow", padding=(0, 2)
        ))
    else:
        print("\n" + "=" * 50)
        print("  Daily AI Assistant v3.0 CLI")
        print("=" * 50)


# ── Argument parser ───────────────────────────────────────────────
def parse_args():
    parser = argparse.ArgumentParser(
        description="Daily AI Assistant - Rich CLI v3.0"
    )
    parser.add_argument("--setup",       action="store_true", help="Run first-time setup wizard")
    parser.add_argument("--chat",        action="store_true", help="Start interactive chat mode")
    parser.add_argument("--module",      type=str,            help="Run a specific module directly")
    parser.add_argument("--provider",    type=str, default=None, help="Force LLM provider (ollama/groq/openai/anthropic/cohere)")
    parser.add_argument("--list-models", action="store_true", help="List available Ollama models")
    return parser.parse_args()


# ── Interactive main menu ─────────────────────────────────────────
MENU_ITEMS = [
    ("1", "\U0001f305  Morning Routine",   "morning"),
    ("2", "\U0001f4cb  Task Manager",       "tasks"),
    ("3", "\U0001f3af  Habit Tracker",      "habits"),
    ("4", "\U0001f4dd  Journal",            "journal"),
    ("5", "\U0001f37d   Meal Planner",       "meals"),
    ("6", "\U0001f324   Weather & Activities","weather"),
    ("7", "\U0001f4f0  News Briefing",       "news"),
    ("8", "\u23f1   Focus Schedule",         "focus"),
    ("9", "\U0001f514  Reminders",           "reminders"),
    ("10","\U0001f4a1  Motivational Quote",  "quote"),
    ("A", "\U0001f31f  Run ALL modules",      "all"),
    ("C", "\U0001f4ac  Chat Mode",            "chat"),
    ("Q", "\U0001f6aa  Quit",                 "quit"),
]

def show_menu(name: str):
    if RICH:
        from rich.table import Table
        t = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
        t.add_column(style="bold cyan",  width=4)
        t.add_column(style="white")
        for key, label, _ in MENU_ITEMS:
            t.add_row(f"[{key}]", label)
        console.print(f"\n[bold]Good day, [yellow]{name}[/yellow]! What would you like to do?[/bold]")
        console.print(t)
    else:
        print(f"\nGood day, {name}! What would you like to do?")
        for key, label, _ in MENU_ITEMS:
            print(f"  [{key}] {label}")

def get_choice() -> str:
    if RICH:
        console.print("[dim]Enter choice: [/dim]", end="")
    else:
        print("Enter choice: ", end="")
    return input().strip().upper()


# ── Main entry point ──────────────────────────────────────────────
def main():
    args = parse_args()

    from config.settings import Settings
    from models.llm_manager import LLMManager
    from utils.setup_wizard import SetupWizard
    from utils.daily_orchestrator import DailyOrchestrator
    from utils.cli_chat import CLIChat

    settings = Settings()
    llm      = LLMManager(settings)

    # Override provider if passed
    if args.provider:
        settings.default_provider = args.provider

    # --setup
    if args.setup:
        wizard = SetupWizard(settings)
        wizard.run()
        return

    # --list-models
    if args.list_models:
        models = llm.list_ollama_models()
        if RICH:
            console.print("\n[bold]\U0001f4e6 Available Ollama Models:[/bold]")
            for m in models:
                console.print(f"  [cyan]\u2022[/cyan] {m}")
        else:
            print("\nAvailable Ollama Models:")
            for m in models: print(f"  - {m}")
        return

    banner()

    orch = DailyOrchestrator(llm, provider=args.provider or settings.default_provider)
    prefs = orch.load_preferences()
    name  = prefs.get("name", "User")

    # --chat  (direct jump)
    if args.chat:
        chat = CLIChat(orch, prefs)
        chat.run()
        return

    # --module  (run one module directly)
    if args.module:
        orch.run_module(args.module, prefs)
        return

    # Interactive menu loop
    module_map = {key: mod for key, _, mod in MENU_ITEMS}
    while True:
        show_menu(name)
        choice = get_choice()
        mod = module_map.get(choice)

        if mod is None:
            rprint("[red]Invalid choice, try again.[/red]" if RICH else "Invalid choice.")
        elif mod == "quit":
            rprint("\n[bold yellow]Goodbye! Have a great day! \U0001f305[/bold yellow]" if RICH else "\nGoodbye!")
            break
        elif mod == "chat":
            chat = CLIChat(orch, prefs)
            chat.run()
        elif mod == "all":
            for _, _, m in MENU_ITEMS:
                if m not in ("all", "chat", "quit"):
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
