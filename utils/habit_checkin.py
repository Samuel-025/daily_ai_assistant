"""Habit Check-in - Daily habit logging with streak auto-increment.

Flow:
  1. Load habits/current_habits.json
  2. Show each habit with today's check-in status
  3. Let user mark done / skip each one
  4. Increment streak for done habits, reset for missed ones if --strict
  5. Save last_checked date to prevent double check-in
  6. Return summary string for display
"""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Optional

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.prompt import Prompt
    from rich import box
    RICH = True
except ImportError:
    RICH = False


HABITS_FILE = Path("habits/current_habits.json")

DEFAULT_HABITS: dict = {
    "habits": [
        {"name": "Drink 8 glasses of water", "streak": 0, "target": 30},
        {"name": "Exercise 20 min",           "streak": 0, "target": 30},
        {"name": "Read 10 min",               "streak": 0, "target": 21},
        {"name": "Meditate 5 min",            "streak": 0, "target": 21},
        {"name": "Sleep by 11 PM",            "streak": 0, "target": 30},
    ]
}


class HabitCheckIn:
    """Manages daily habit check-in and streak persistence."""

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir  = base_dir or Path(".")
        self.file      = self.base_dir / "habits" / "current_habits.json"
        self.today_str = date.today().isoformat()   # e.g. "2026-06-18"

    # ── Persistence ──────────────────────────────────────────────
    def _load(self) -> dict:
        if self.file.exists():
            try:
                return json.loads(self.file.read_text(encoding="utf-8"))
            except Exception:
                pass
        return dict(DEFAULT_HABITS)

    def _save(self, data: dict) -> None:
        self.file.parent.mkdir(parents=True, exist_ok=True)
        self.file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    # ── State ────────────────────────────────────────────────────
    def already_checked_in(self) -> bool:
        """Return True if every habit already has last_checked == today."""
        data   = self._load()
        habits = data.get("habits", [])
        if not habits:
            return False
        return all(h.get("last_checked") == self.today_str for h in habits)

    def today_status(self) -> list[dict]:
        """Return list of {name, streak, target, done_today} for display."""
        data = self._load()
        out  = []
        for h in data.get("habits", []):
            out.append({
                "name":    h.get("name", "?"),
                "streak":  int(h.get("streak", 0)),
                "target":  int(h.get("target", 30)),
                "done":    h.get("last_checked") == self.today_str,
            })
        return out

    # ── Core check-in ────────────────────────────────────────────
    def check_in(self, done_indices: list[int], strict: bool = False) -> str:
        """
        Mark the habits at `done_indices` (0-based) as done today.
        - Increments streak for done habits.
        - If strict=True, resets streak for skipped habits.
        Returns a summary string.
        """
        data   = self._load()
        habits = data.get("habits", [])
        done_count   = 0
        skipped      = []
        results      = []

        for i, h in enumerate(habits):
            name = h.get("name", "?")
            if i in done_indices:
                # Only increment if not already checked in today
                if h.get("last_checked") != self.today_str:
                    h["streak"]       = int(h.get("streak", 0)) + 1
                    h["last_checked"] = self.today_str
                done_count += 1
                results.append(f"✓ {name} — streak: **{h['streak']}d**")
            else:
                if strict:
                    h["streak"] = 0
                skipped.append(name)
                results.append(f"– {name} (skipped)")

        self._save(data)

        lines = ["**Habit Check-in Complete!**", ""]
        lines += results
        lines += ["",
                  f"✅ Done: {done_count}/{len(habits)}  "
                  f"⏭ Skipped: {len(skipped)}"]
        return "\n".join(lines)

    def add_habit(self, name: str, target: int = 30) -> str:
        """Add a new habit to the list."""
        data   = self._load()
        habits = data.setdefault("habits", [])
        if any(h["name"].lower() == name.lower() for h in habits):
            return f"Habit **{name}** already exists."
        habits.append({"name": name, "streak": 0, "target": target})
        self._save(data)
        return f"✓ Added habit: **{name}** (target: {target} days)"

    def remove_habit(self, index: int) -> str:
        """Remove habit by 1-based index."""
        data   = self._load()
        habits = data.get("habits", [])
        if not (1 <= index <= len(habits)):
            return f"No habit #{index}. There are {len(habits)} habits."
        removed = habits.pop(index - 1)["name"]
        self._save(data)
        return f"✗ Removed habit: **{removed}**"

    def reset_streak(self, index: int) -> str:
        """Reset streak for a specific habit by 1-based index."""
        data   = self._load()
        habits = data.get("habits", [])
        if not (1 <= index <= len(habits)):
            return f"No habit #{index}."
        habits[index - 1]["streak"] = 0
        habits[index - 1].pop("last_checked", None)
        self._save(data)
        return f"↺ Reset streak for **{habits[index - 1]['name']}"

    def summary_line(self) -> str:
        """One-liner for system prompt context."""
        status = self.today_status()
        if not status:
            return "(No habits tracked.)"
        done  = sum(1 for h in status if h["done"])
        total = len(status)
        best  = max(status, key=lambda h: h["streak"])
        return (f"{done}/{total} habits checked in today | "
                f"Best streak: {best['name']} ({best['streak']}d)")


# ── Interactive TUI check-in ──────────────────────────────────────────────────

def run_habit_checkin(base_dir: Optional[Path] = None) -> str:
    """
    Full interactive check-in session.
    Returns the summary string (also prints it).
    """
    ci     = HabitCheckIn(base_dir)
    status = ci.today_status()

    if not status:
        msg = "No habits found. Add habits to habits/current_habits.json"
        if RICH:
            console = Console()
            console.print(Panel(msg, title="[bold cyan]🎯 Habit Check-in[/bold cyan]", border_style="cyan"))
        else:
            print(msg)
        return msg

    if RICH:
        console = Console()
        # ── Show current state ──────────────────────────────────
        t = Table(box=box.SIMPLE, show_header=True, header_style="bold cyan", padding=(0, 1))
        t.add_column("#",       width=4,  justify="right")
        t.add_column("Habit",   min_width=26)
        t.add_column("Streak",  width=10, justify="right")
        t.add_column("Target",  width=8,  justify="right")
        t.add_column("Today",   width=8,  justify="center")

        for i, h in enumerate(status, 1):
            pct   = min(h["streak"] / max(h["target"], 1), 1.0)
            color = "green" if pct >= 0.8 else "yellow" if pct >= 0.4 else "cyan"
            done_mark = "[green]✓ Done[/green]" if h["done"] else "[dim]○ Pending[/dim]"
            t.add_row(
                str(i),
                h["name"],
                f"[{color}]{h['streak']}d[/{color}]",
                f"[dim]{h['target']}d[/dim]",
                done_mark,
            )

        console.print(Panel(
            t,
            title="[bold cyan]🎯 Habit Check-in[/bold cyan]",
            subtitle="[dim]Enter habit numbers you completed today[/dim]",
            border_style="cyan",
            padding=(1, 1),
        ))

        already_done = [i + 1 for i, h in enumerate(status) if h["done"]]
        if already_done:
            console.print(f"[dim]  Already checked in: {', '.join('#'+str(n) for n in already_done)}[/dim]")

        raw = Prompt.ask(
            "[bold cyan]Which habits did you complete today?[/bold cyan] "
            "[dim](comma-separated numbers, e.g. 1,3,4  |  'all'  |  'skip'  |  'none')[/dim]",
            default="",
        ).strip().lower()

    else:
        print("\n=== HABIT CHECK-IN ===")
        for i, h in enumerate(status, 1):
            done_str = "[Done]" if h["done"] else "[Pending]"
            print(f"  {i}. {h['name']:<32} {h['streak']}/{h['target']}d  {done_str}")
        print()
        raw = input("Which habits did you complete today? (numbers / 'all' / 'none'): ").strip().lower()
        console = None  # type: ignore[assignment]

    # ── Parse input ──────────────────────────────────────────────
    if raw in ("", "skip", "s"):
        msg = "Check-in skipped."
        if RICH:
            console.print(f"[dim]{msg}[/dim]")
        else:
            print(msg)
        return msg

    if raw in ("all", "a"):
        done_indices = list(range(len(status)))
    elif raw in ("none", "0", "n"):
        done_indices = []
    else:
        done_indices = []
        for part in raw.replace(" ", "").split(","):
            try:
                n = int(part)
                if 1 <= n <= len(status):
                    done_indices.append(n - 1)
            except ValueError:
                pass

    summary = ci.check_in(done_indices)

    if RICH:
        from rich.markdown import Markdown
        console.print(Panel(
            Markdown(summary),
            title="[bold green]✅ Check-in Saved[/bold green]",
            border_style="green",
            padding=(1, 2),
        ))
    else:
        print("\n" + summary)

    return summary
