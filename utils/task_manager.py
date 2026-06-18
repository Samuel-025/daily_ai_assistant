"""Task CRUD Manager

Exposes:
  TaskCRUD        — programmatic API used by chat, CLI, Streamlit
  run_task_manager — interactive Rich terminal session
"""

from datetime import date
from pathlib import Path
from typing import Protocol, Optional
import json


class _ConsoleLike(Protocol):
    def print(self, *args: object, **kwargs: object) -> None: ...


try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.prompt import Prompt, Confirm
    from rich import box
    RICH = True
    console: _ConsoleLike = Console()  # type: ignore[assignment]
except ImportError:
    RICH = False

    class _FallbackConsole:
        def print(self, *args: object, **kwargs: object) -> None:
            print(*args)

    console: _ConsoleLike = _FallbackConsole()  # type: ignore[assignment,misc]


# ──────────────────────────────────────────────────────────────────────
class TaskCRUD:
    """Programmatic task CRUD — used by chat, orchestrator, Streamlit.

    All methods return a human-readable result string so callers can
    print it or pass it straight to the AI as context.
    """

    def __init__(self, base_dir: Optional[Path] = None):
        root = base_dir or Path(".")
        self.tasks_file = root / "tasks" / "today_tasks.json"

    # ── internal helpers ─────────────────────────────────────────
    def _load(self) -> dict:
        try:
            if self.tasks_file.exists():
                return json.loads(self.tasks_file.read_text(encoding="utf-8"))
        except Exception:
            pass
        return {"tasks": [], "completed": []}

    def _save(self, data: dict) -> None:
        self.tasks_file.parent.mkdir(parents=True, exist_ok=True)
        self.tasks_file.write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    # ── public API ──────────────────────────────────────────────
    def list_tasks(self) -> str:
        """Return a formatted text snapshot of all tasks."""
        data      = self._load()
        active    = data.get("tasks", [])
        completed = data.get("completed", [])
        if not active and not completed:
            return "No tasks yet. Add one with: /task add <description>"
        lines = []
        if active:
            lines.append(f"**Active tasks ({len(active)}):**")
            for i, t in enumerate(active, 1):
                lines.append(f"  {i}. ○ {t}")
        if completed:
            lines.append(f"\n**Completed ({len(completed)}):**")
            for i, t in enumerate(completed, 1):
                lines.append(f"  {i}. ✓ {t}")
        return "\n".join(lines)

    def add(self, text: str) -> str:
        """Add a new active task. Returns confirmation string."""
        text = text.strip()
        if not text:
            return "No task text provided."
        data = self._load()
        data["tasks"].append(text)
        self._save(data)
        pos = len(data["tasks"])
        return f"✓ Added task #{pos}: **{text}**"

    def complete(self, index: int) -> str:
        """Mark active task #index (1-based) as done."""
        data  = self._load()
        tasks = data.get("tasks", [])
        if not tasks:
            return "No active tasks to complete."
        idx = index - 1
        if not (0 <= idx < len(tasks)):
            return f"Invalid task number {index}. You have {len(tasks)} active task(s)."
        done = tasks.pop(idx)
        data["completed"].append(done)
        self._save(data)
        return f"✓ Completed: **{done}**  ({len(tasks)} active tasks remaining)"

    def delete(self, index: int) -> str:
        """Delete task #index from active list (1-based)."""
        data  = self._load()
        tasks = data.get("tasks", [])
        if not tasks:
            return "No active tasks to delete."
        idx = index - 1
        if not (0 <= idx < len(tasks)):
            return f"Invalid task number {index}. You have {len(tasks)} active task(s)."
        removed = tasks.pop(idx)
        self._save(data)
        return f"✗ Deleted: **{removed}**"

    def delete_completed(self, index: int) -> str:
        """Delete completed task #index (1-based within completed list)."""
        data      = self._load()
        completed = data.get("completed", [])
        if not completed:
            return "No completed tasks to delete."
        idx = index - 1
        if not (0 <= idx < len(completed)):
            return f"Invalid number {index}. You have {len(completed)} completed task(s)."
        removed = completed.pop(idx)
        self._save(data)
        return f"✗ Deleted completed task: **{removed}**"

    def clear_completed(self) -> str:
        """Remove all completed tasks."""
        data  = self._load()
        count = len(data.get("completed", []))
        if count == 0:
            return "No completed tasks to clear."
        data["completed"] = []
        self._save(data)
        return f"✓ Cleared {count} completed task(s)."

    def clear_all(self) -> str:
        """Wipe everything — active and completed."""
        data = self._load()
        total = len(data.get("tasks", [])) + len(data.get("completed", []))
        self._save({"tasks": [], "completed": []})
        return f"✓ Cleared all {total} task(s)."

    def summary(self) -> str:
        """One-line summary: X active, Y done."""
        data = self._load()
        a = len(data.get("tasks", []))
        c = len(data.get("completed", []))
        return f"{a} active task(s), {c} completed today."


# ──────────────────────────────────────────────────────────────────────
# Legacy helpers used by run_task_manager() interactive loop
# ──────────────────────────────────────────────────────────────────────
TASKS_FILE = Path("tasks/today_tasks.json")


def _load() -> dict:
    if TASKS_FILE.exists():
        try:
            return json.loads(TASKS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"tasks": [], "completed": []}


def _save(data: dict) -> None:
    TASKS_FILE.parent.mkdir(parents=True, exist_ok=True)
    TASKS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _show(data: dict) -> None:
    tasks     = data.get("tasks", [])
    completed = data.get("completed", [])
    if RICH:
        t = Table(box=box.SIMPLE, show_header=True, header_style="bold cyan")
        t.add_column("#",      width=4)
        t.add_column("Status", width=10)
        t.add_column("Task")
        for i, task in enumerate(tasks, 1):
            t.add_row(str(i), "[yellow]\u25cb Pending[/yellow]", task)
        for i, task in enumerate(completed, len(tasks) + 1):
            t.add_row(str(i), "[green]\u2713 Done[/green]", f"[dim]{task}[/dim]")
        console.print(Panel(t, title="[bold cyan]\U0001f4cb Tasks[/bold cyan]", border_style="cyan"))
    else:
        print("\n--- PENDING ---")
        for i, t2 in enumerate(tasks, 1):
            print(f"  [{i}] {t2}")
        print("--- COMPLETED ---")
        for i, t2 in enumerate(completed, len(tasks) + 1):
            print(f"  [{i}] \u2713 {t2}")


def run_task_manager() -> None:
    """Interactive CRUD task manager (Rich terminal session)."""
    if RICH:
        console.print(Panel.fit(
            "[bold cyan]\U0001f4cb Task Manager[/bold cyan]\n"
            "[dim]a=add  c=complete  d=delete  cl=clear done  q=quit[/dim]",
            border_style="cyan"
        ))
    else:
        print("\n=== TASK MANAGER ===")
        print("Commands: a=add  c=complete  d=delete  cl=clear done  q=quit")

    crud = TaskCRUD()   # uses cwd as base_dir

    while True:
        data = crud._load()
        _show(data)

        if RICH:
            cmd = Prompt.ask("[bold cyan]Action[/bold cyan]", default="q").strip().lower()
        else:
            cmd = input("Action (a/c/d/cl/q): ").strip().lower()

        if cmd == "q":
            break

        elif cmd == "a":
            if RICH:
                task = Prompt.ask("[green]New task[/green]").strip()
            else:
                task = input("New task: ").strip()
            console.print(crud.add(task))

        elif cmd == "c":
            tasks = crud._load().get("tasks", [])
            if not tasks:
                console.print("[dim]No pending tasks.[/dim]" if RICH else "No pending tasks.")
                continue
            if RICH:
                num = Prompt.ask("[yellow]Complete task #[/yellow]").strip()
            else:
                num = input("Complete task #: ").strip()
            try:
                console.print(crud.complete(int(num)))
            except ValueError:
                console.print("[red]Enter a number.[/red]" if RICH else "Enter a number.")

        elif cmd == "d":
            tasks = crud._load().get("tasks", [])
            if not tasks:
                console.print("[dim]No tasks to delete.[/dim]" if RICH else "No tasks.")
                continue
            if RICH:
                num = Prompt.ask("[red]Delete task #[/red]").strip()
            else:
                num = input("Delete task #: ").strip()
            try:
                console.print(crud.delete(int(num)))
            except ValueError:
                console.print("[red]Enter a number.[/red]" if RICH else "Enter a number.")

        elif cmd == "cl":
            if RICH:
                ok = Confirm.ask("[yellow]Clear all completed tasks?[/yellow]")
            else:
                ok = input("Clear completed? (y/n): ").lower() == "y"
            if ok:
                console.print(crud.clear_completed())
        else:
            console.print("[dim]Unknown command. Use a/c/d/cl/q[/dim]" if RICH else "Unknown: a/c/d/cl/q")
