"""Background Reminder Daemon - runs in a separate thread using schedule

Usage:
  from utils.reminder_daemon import start_reminders, stop_reminders
  start_reminders()   # starts background thread
  stop_reminders()    # stops it cleanly
"""

import json
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Protocol

try:
    import schedule
    SCHEDULE = True
except ImportError:
    SCHEDULE = False

try:
    from rich.console import Console
    RICH = True
except ImportError:
    RICH = False


class _ConsoleLike(Protocol):
    """Structural type so Pylance knows console always has .print()."""
    def print(self, *args: object, **kwargs: object) -> None: ...


if RICH:
    console: _ConsoleLike = Console()  # type: ignore[assignment]
else:
    class _FallbackConsole:
        def print(self, *args: object, **kwargs: object) -> None:
            print(*args)
    console: _ConsoleLike = _FallbackConsole()  # type: ignore[assignment,misc]


_stop_flag = threading.Event()
_thread: threading.Thread | None = None

REMINDERS_FILE = Path("reminders/reminders.json")


def _load_reminders() -> list:
    if REMINDERS_FILE.exists():
        try:
            return json.loads(REMINDERS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []


def _notify(message: str):
    now = datetime.now().strftime("%H:%M")
    console.print(
        f"\n[bold yellow]\U0001f514 Reminder [{now}]:[/bold yellow] [white]{message}[/white]"
        if RICH else
        f"\n\U0001f514 Reminder [{now}]: {message}"
    )


def _schedule_all():
    if not SCHEDULE:
        return
    schedule.clear()
    reminders = _load_reminders()
    today     = datetime.now().strftime("%Y-%m-%d")
    for r in reminders:
        t    = r.get("time", "")
        msg  = r.get("message", "")
        when = r.get("date", "daily")
        if not t or not msg:
            continue
        if when == "daily" or when == today:
            schedule.every().day.at(t).do(_notify, message=msg)


def _run_loop():
    _schedule_all()
    while not _stop_flag.is_set():
        if SCHEDULE:
            schedule.run_pending()
        time.sleep(30)


def start_reminders():
    global _thread
    if not SCHEDULE:
        console.print(
            "[dim]schedule not installed — reminders disabled[/dim]"
            if RICH else
            "schedule not installed. Run: pip install schedule"
        )
        return
    _stop_flag.clear()
    _thread = threading.Thread(target=_run_loop, daemon=True, name="ReminderDaemon")
    _thread.start()
    console.print(
        "[dim]\U0001f514 Background reminders started[/dim]"
        if RICH else
        "\U0001f514 Background reminders started"
    )


def stop_reminders():
    _stop_flag.set()
    console.print(
        "[dim]\U0001f514 Reminders stopped[/dim]"
        if RICH else
        "\U0001f514 Reminders stopped"
    )


def reload_reminders():
    """Call this after adding/editing reminders to pick up changes."""
    _schedule_all()
    console.print(
        "[dim]\U0001f514 Reminders reloaded[/dim]"
        if RICH else
        "Reminders reloaded"
    )
