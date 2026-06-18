"""Habit Progress Visualization - Rich terminal charts for habit streaks"""

from pathlib import Path
import json

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich import box
    RICH = True
except ImportError:
    RICH = False

# Always-valid console — never None
if RICH:
    from rich.console import Console as _RC
    _console = _RC()
else:
    class _FallbackConsole:  # type: ignore
        def print(self, *args, **kwargs):
            print(*args)
    _console = _FallbackConsole()  # type: ignore

console = _console

HABITS_FILE = Path("habits/current_habits.json")

BAR_FULL  = "\u2588"
BAR_EMPTY = "\u2591"
BAR_WIDTH = 30


def _load() -> list:
    if HABITS_FILE.exists():
        try:
            data = json.loads(HABITS_FILE.read_text(encoding="utf-8"))
            return data.get("habits", [])
        except Exception:
            pass
    return []


def _progress_bar(streak: int, target: int) -> tuple:
    pct    = min(streak / max(target, 1), 1.0)
    filled = int(pct * BAR_WIDTH)
    empty  = BAR_WIDTH - filled
    bar    = BAR_FULL * filled + BAR_EMPTY * empty
    color  = "green" if pct >= 0.8 else "yellow" if pct >= 0.4 else "red"
    return bar, color, int(pct * 100)


def _streak_emoji(streak: int) -> str:
    if streak >= 30: return "\U0001f3c6"
    if streak >= 21: return "\U0001f525"
    if streak >= 14: return "\U0001f4aa"
    if streak >= 7:  return "\U0001f44d"
    if streak >= 3:  return "\U0001f331"
    return "\U0001f4ab"


def show_habit_viz():
    habits = _load()
    if not habits:
        if RICH:
            _console.print(Panel(
                "[dim]No habits found. Add habits to habits/current_habits.json[/dim]",
                title="[bold cyan]\U0001f3af Habit Tracker[/bold cyan]",
                border_style="cyan"
            ))
        else:
            print("No habits found.")
        return

    if RICH:
        t = Table(
            box=box.SIMPLE,
            show_header=True,
            header_style="bold cyan",
            padding=(0, 1)
        )
        t.add_column("Habit",    min_width=22)
        t.add_column("Progress", min_width=34)
        t.add_column("Streak",   width=8,  justify="right")
        t.add_column("Target",   width=8,  justify="right")
        t.add_column("%",        width=6,  justify="right")
        t.add_column("\U0001f3c5",        width=4,  justify="center")

        for h in habits:
            name   = h.get("name", "?")
            streak = int(h.get("streak", 0))
            target = int(h.get("target", 30))
            bar, color, pct = _progress_bar(streak, target)
            emoji  = _streak_emoji(streak)

            bar_text = Text()
            bar_text.append(BAR_FULL * int(pct / 100 * BAR_WIDTH), style=color)
            bar_text.append(BAR_EMPTY * (BAR_WIDTH - int(pct / 100 * BAR_WIDTH)), style="dim")

            t.add_row(
                name,
                bar_text,
                f"[{color}]{streak}d[/{color}]",
                f"[dim]{target}d[/dim]",
                f"[{color}]{pct}%[/{color}]",
                emoji
            )

        total    = len(habits)
        on_track = sum(1 for h in habits if h.get("streak", 0) / max(h.get("target", 30), 1) >= 0.5)
        avg      = sum(h.get("streak", 0) for h in habits) // max(total, 1)
        best     = max(habits, key=lambda h: h.get("streak", 0))

        summary = (
            f"[bold]Total:[/bold] {total} habits  "
            f"[bold]On Track:[/bold] [green]{on_track}/{total}[/green]  "
            f"[bold]Avg Streak:[/bold] [yellow]{avg} days[/yellow]  "
            f"[bold]Best:[/bold] [cyan]{best.get('name','?')} ({best.get('streak',0)}d)[/cyan]"
        )

        _console.print(Panel(
            t,
            title="[bold cyan]\U0001f3af Habit Progress[/bold cyan]",
            subtitle=summary,
            border_style="cyan",
            padding=(1, 1)
        ))
    else:
        print("\n=== HABIT PROGRESS ===")
        for h in habits:
            name   = h.get("name", "?")
            streak = int(h.get("streak", 0))
            target = int(h.get("target", 30))
            bar, _, pct = _progress_bar(streak, target)
            print(f"  {name}")
            print(f"  {bar} {streak}/{target} days ({pct}%)")
