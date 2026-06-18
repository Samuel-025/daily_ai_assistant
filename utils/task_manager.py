"""Task CRUD Manager - Interactive terminal task management with Rich UI"""

from datetime import date
from pathlib import Path
from typing import Protocol
import json


class _ConsoleLike(Protocol):
    """Structural type so Pylance knows console always has .print()."""
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

TASKS_FILE = Path("tasks/today_tasks.json")


def _load() -> dict:
    if TASKS_FILE.exists():
        try:
            return json.loads(TASKS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"tasks": [], "completed": []}


def _save(data: dict):
    TASKS_FILE.parent.mkdir(parents=True, exist_ok=True)
    TASKS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _show(data: dict):
    tasks     = data.get("tasks", [])
    completed = data.get("completed", [])
    if RICH:
        t = Table(box=box.SIMPLE, show_header=True, header_style="bold cyan")
        t.add_column("#",         width=4)
        t.add_column("Status",    width=10)
        t.add_column("Task")
        for i, task in enumerate(tasks, 1):
            t.add_row(str(i), "[yellow]\u25cb Pending[/yellow]", task)
        for i, task in enumerate(completed, len(tasks) + 1):
            t.add_row(str(i), "[green]\u2713 Done[/green]",    f"[dim]{task}[/dim]")
        console.print(Panel(t, title="[bold cyan]\U0001f4cb Tasks[/bold cyan]", border_style="cyan"))
    else:
        print("\n--- PENDING ---")
        for i, t in enumerate(tasks, 1):
            print(f"  [{i}] {t}")
        print("--- COMPLETED ---")
        for i, t in enumerate(completed, len(tasks) + 1):
            print(f"  [{i}] \u2713 {t}")


def run_task_manager():
    """Interactive CRUD task manager."""
    if RICH:
        console.print(Panel.fit(
            "[bold cyan]\U0001f4cb Task Manager[/bold cyan]\n"
            "[dim]a=add  c=complete  d=delete  cl=clear done  q=quit[/dim]",
            border_style="cyan"
        ))
    else:
        print("\n=== TASK MANAGER ===")
        print("Commands: a=add  c=complete  d=delete  cl=clear done  q=quit")

    while True:
        data = _load()
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
            if task:
                data["tasks"].append(task)
                _save(data)
                if RICH:
                    console.print(f"[green]\u2713 Added:[/green] {task}")
                else:
                    print(f"Added: {task}")

        elif cmd == "c":
            tasks = data.get("tasks", [])
            if not tasks:
                if RICH:
                    console.print("[dim]No pending tasks.[/dim]")
                else:
                    print("No pending tasks.")
                continue
            if RICH:
                num = Prompt.ask("[yellow]Complete task #[/yellow]").strip()
            else:
                num = input("Complete task #: ").strip()
            try:
                idx = int(num) - 1
                if 0 <= idx < len(tasks):
                    done = tasks.pop(idx)
                    data["completed"].append(done)
                    _save(data)
                    if RICH:
                        console.print(f"[green]\u2713 Completed:[/green] {done}")
                    else:
                        print(f"Completed: {done}")
                else:
                    if RICH:
                        console.print("[red]Invalid number.[/red]")
                    else:
                        print("Invalid number.")
            except ValueError:
                if RICH:
                    console.print("[red]Enter a number.[/red]")
                else:
                    print("Enter a number.")

        elif cmd == "d":
            all_tasks = data.get("tasks", []) + data.get("completed", [])
            if not all_tasks:
                if RICH:
                    console.print("[dim]No tasks to delete.[/dim]")
                else:
                    print("No tasks.")
                continue
            if RICH:
                num = Prompt.ask("[red]Delete task #[/red]").strip()
            else:
                num = input("Delete task #: ").strip()
            try:
                idx  = int(num) - 1
                plen = len(data["tasks"])
                if 0 <= idx < plen:
                    removed = data["tasks"].pop(idx)
                elif plen <= idx < plen + len(data["completed"]):
                    removed = data["completed"].pop(idx - plen)
                else:
                    if RICH:
                        console.print("[red]Invalid number.[/red]")
                    else:
                        print("Invalid number.")
                    continue
                _save(data)
                if RICH:
                    console.print(f"[red]\u2717 Deleted:[/red] {removed}")
                else:
                    print(f"Deleted: {removed}")
            except ValueError:
                if RICH:
                    console.print("[red]Enter a number.[/red]")
                else:
                    print("Enter a number.")

        elif cmd == "cl":
            if RICH:
                ok = Confirm.ask("[yellow]Clear all completed tasks?[/yellow]")
            else:
                ok = input("Clear completed? (y/n): ").lower() == "y"
            if ok:
                count = len(data.get("completed", []))
                data["completed"] = []
                _save(data)
                if RICH:
                    console.print(f"[green]Cleared {count} completed tasks.[/green]")
                else:
                    print(f"Cleared {count} tasks.")
        else:
            if RICH:
                console.print("[dim]Unknown command. Use a/c/d/cl/q[/dim]")
            else:
                print("Unknown: a/c/d/cl/q")
