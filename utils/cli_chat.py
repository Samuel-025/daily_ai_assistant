"""CLI Chat Mode - ChatGPT-style interactive terminal chat

Features:
- Full chat history (last 20 messages)
- Slash commands incl. full /task CRUD subcommands
- Rich terminal UI with markdown rendering
- Auto-saves chat history to journal/ at end of session
- Type 'exit' or 'quit' to leave chat
- All slash commands use LIVE data from JSON files
"""

from datetime import date, datetime
from pathlib import Path
import json

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.markdown import Markdown
    from rich.prompt import Prompt
    RICH = True
except ImportError:
    RICH = False

_console: "Console"
if RICH:
    from rich.console import Console as _RichConsole
    _console = _RichConsole()
else:
    class _FallbackConsole:  # type: ignore
        def print(self, *args, **kwargs):
            print(*args)
        def status(self, *args, **kwargs):
            import contextlib
            return contextlib.nullcontext()
    _console = _FallbackConsole()  # type: ignore

console = _console

SLASH_HELP = """
| Command                  | What it does                            |
|--------------------------|-----------------------------------------|
| /morning                 | Personalised morning routine            |
| /tasks                   | AI-prioritise your active tasks         |
| /task list               | Show all tasks (no AI)                  |
| /task add <text>         | Add a new task instantly                |
| /task done <n>           | Mark task #n complete                   |
| /task delete <n>         | Delete active task #n                   |
| /task cleardone          | Remove all completed tasks              |
| /task clearall           | Wipe every task (use carefully!)        |
| /habits                  | Analyse your habit streaks              |
| /journal                 | Reflect on today's journal entry        |
| /meal                    | One-day Indian meal plan                |
| /weather                 | Activity suggestions for your city      |
| /news                    | Concise tech + health news briefing     |
| /focus                   | Pomodoro focus schedule                 |
| /reminders               | Show today's due reminders              |
| /quote                   | Motivational quote of the day           |
| /help                    | Show this table                         |
| exit / quit              | Leave chat mode                         |
"""

JOURNAL_DIR = Path("journal")


def _load_json(path: Path, default):
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default


def _save_chat_to_journal(history: list, name: str):
    if not history:
        return
    today    = date.today().isoformat()
    filename = JOURNAL_DIR / (today + "-chat.json")
    JOURNAL_DIR.mkdir(parents=True, exist_ok=True)
    sessions = []
    if filename.exists():
        try:
            sessions = json.loads(filename.read_text(encoding="utf-8")).get("sessions", [])
        except Exception:
            sessions = []
    sessions.append({"time": datetime.now().strftime("%H:%M:%S"), "messages": history})
    filename.write_text(
        json.dumps({"date": today, "user": name, "sessions": sessions}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    _console.print(f"[dim]\U0001f4be Chat saved to {filename}[/dim]" if RICH else f"Chat saved to {filename}")


class CLIChat:
    def __init__(self, orchestrator, prefs: dict):
        self.orch     = orchestrator
        self.prefs    = prefs
        self.history: list = []
        self.name     = prefs.get("name", "User")
        self.base_dir: Path = getattr(orchestrator, "base_dir", Path("."))

        # TaskCRUD instance scoped to the correct base_dir
        from utils.task_manager import TaskCRUD
        self.tasks = TaskCRUD(self.base_dir)

    # ── Live data loaders ──────────────────────────────────────
    def _tasks_context(self) -> str:
        return self.tasks.list_tasks()

    def _habits_context(self) -> str:
        f  = self.base_dir / "habits" / "current_habits.json"
        default_h = {"habits": [
            {"name": "Drink 8 glasses of water", "streak": 0, "target": 30},
            {"name": "Exercise 20 min",           "streak": 0, "target": 30},
            {"name": "Read 10 min",               "streak": 0, "target": 21},
            {"name": "Meditate 5 min",            "streak": 0, "target": 21},
            {"name": "Sleep by 11 PM",            "streak": 0, "target": 30},
        ]}
        hd     = _load_json(f, default_h)
        habits = hd.get("habits", [])
        if not habits:
            return "(No habits tracked yet.)"
        lines = ["Current habit streaks:"]
        for h in habits:
            s   = h.get("streak", 0)
            t   = h.get("target", 30)
            pct = int((s / t * 100) if t else 0)
            lines.append(f"  - {h['name']}: {s}/{t} days ({pct}%)")
        return "\n".join(lines)

    def _journal_context(self) -> str:
        today = datetime.now().strftime("%Y-%m-%d")
        jf    = self.base_dir / "journal" / f"{today}.json"
        jd    = _load_json(jf, {})
        entry = jd.get("entry", "")
        mood  = jd.get("mood", "")
        if not entry:
            return f"(No journal entry for {today} yet.)"
        mood_str = f" (mood: {mood})" if mood else ""
        return f"Today's journal entry{mood_str}:\n\"\"\"{entry}\"\"\""

    def _reminders_context(self) -> str:
        try:
            reminders = self.orch.reminder_mgr.get_due_today()
        except Exception:
            return "(Could not load reminders.)"
        if not reminders:
            return "(No reminders due today.)"
        lines = ["Today's reminders:"]
        for r in reminders:
            lines.append(f"  - {r.get('time','?')}: {r.get('message','')}")
        return "\n".join(lines)

    def _meals_context(self) -> str:
        today = datetime.now().strftime("%Y-%m-%d")
        mf    = self.base_dir / "meals" / f"{today}.json"
        md    = _load_json(mf, {})
        if not md:
            return "(No meal plan saved for today yet.)"
        lines = ["Today's saved meal plan:"]
        for meal, detail in md.items():
            lines.append(f"  {meal}: {detail}")
        return "\n".join(lines)

    # ── System prompt ──────────────────────────────────────────
    def _build_system(self) -> str:
        now = datetime.now().strftime("%A, %d %B %Y - %I:%M %p")
        p   = self.prefs
        d   = p.get("dietary", {})
        return (
            "You are a warm, intelligent personal daily assistant for " + p.get("name", "User") + ".\n"
            "Today is " + now + ".\n"
            "- Wake-up: " + p.get("wake_time", "07:00")
            + " | Fitness: " + p.get("fitness_level", "moderate")
            + " | Diet: " + d.get("type", "balanced") + "\n"
            "- Work focus: " + p.get("work_focus", "general") + "\n\n"
            "LIVE USER DATA (always reference this when asked):\n"
            + self._tasks_context() + "\n\n"
            + self._habits_context() + "\n\n"
            + self._journal_context() + "\n\n"
            + self._reminders_context() + "\n\n"
            "Personality: concise, warm, practical, motivating.\n"
            "Use markdown (bullets, bold, tables) for clarity.\n"
            "Always give a useful, personalised response based on the LIVE DATA above."
        )

    # ── /task subcommand handler (instant, no AI call) ───────────
    def _handle_task_cmd(self, parts: list) -> Optional[str]:  # type: ignore[name-defined]
        """
        Handles: /task list|add|done|delete|cleardone|clearall
        Returns result string to display, or None if subcommand unknown.
        """
        sub = parts[1].lower() if len(parts) > 1 else "list"

        if sub == "list":
            return self._tasks_context()

        elif sub == "add":
            text = " ".join(parts[2:]).strip()
            if not text:
                return "Usage: /task add <task description>"
            return self.tasks.add(text)

        elif sub in ("done", "complete"):
            if len(parts) < 3:
                return "Usage: /task done <number>"
            try:
                return self.tasks.complete(int(parts[2]))
            except ValueError:
                return f"'{parts[2]}' is not a number. Usage: /task done <number>"

        elif sub in ("delete", "del", "remove"):
            if len(parts) < 3:
                return "Usage: /task delete <number>"
            try:
                return self.tasks.delete(int(parts[2]))
            except ValueError:
                return f"'{parts[2]}' is not a number. Usage: /task delete <number>"

        elif sub in ("cleardone", "clear"):
            return self.tasks.clear_completed()

        elif sub == "clearall":
            return self.tasks.clear_all()

        return None

    # ── AI slash prompts ─────────────────────────────────────────
    def _slash_prompt(self, cmd: str) -> str:
        p  = self.prefs
        wt = p.get("wake_time", "07:00")
        fl = p.get("fitness_level", "moderate")
        wf = p.get("work_focus", "general")
        dt = p.get("dietary", {}).get("type", "balanced")
        n  = self.name
        d  = str(date.today())

        journal_ctx = self._journal_context()
        prompts = {
            "/morning": (
                f"Create a personalised morning routine for {n} who wakes at {wt}."
                f" Fitness: {fl}. Work: {wf}. Time blocks, one action each. Be energising.\n\n"
                f"Also factor in these active tasks for the day:\n{self._tasks_context()}"
            ),
            "/tasks": (
                f"Here are {n}'s current tasks:\n{self._tasks_context()}\n\n"
                f"Please: 1) Prioritise the active tasks from most to least important (work focus: {wf}). "
                f"2) Add a concrete 1-line action tip for each active task. "
                f"3) Acknowledge completed ones with a brief motivating note."
            ),
            "/habits": (
                f"Here are {n}'s current habit streaks:\n{self._habits_context()}\n\n"
                f"Please: 1) Highlight what's going well. "
                f"2) Identify which habit needs the most attention and why. "
                f"3) Give one science-backed tip to strengthen the weakest habit."
            ),
            "/journal": (
                journal_ctx + "\n\n"
                + (
                    f"Reflect on {n}'s journal entry above. Give 2 meaningful insights and 1 encouragement."
                    if "No journal entry" not in journal_ctx
                    else f"Give {n} 3 thoughtful journaling prompts for today based on work focus ({wf})."
                )
            ),
            "/meal": (
                f"{self._meals_context()}\n\n"
                f"Create a {dt} meal plan for {n} today. Indian cuisine. Fitness: {fl}. ~2000 kcal."
                f" 3 meals + 1 snack. For each: name, key ingredients, kcal, prep time."
            ),
            "/weather": (
                f"Suggest 4 activities for {n} today. Fitness: {fl}. 2 outdoor, 2 indoor. Duration + what to bring."
            ),
            "/news": (
                f"Give {n} a 5-bullet news briefing for {d} covering: Technology, AI & ML, Health. Factual."
            ),
            "/focus": (
                f"Create a Pomodoro focus schedule for {n} (work: {wf}). "
                f"4 x 25-min blocks, 5-min breaks, 15-min break after block 4. Clean timetable format.\n\n"
                f"Factor in these active tasks:\n{self._tasks_context()}"
            ),
            "/reminders": (
                f"Here are {n}'s reminders for today:\n{self._reminders_context()}\n\n"
                f"Present them clearly and add a brief motivating note to help {n} stay on track."
            ),
            "/quote": (
                f"Give {n} one powerful quote for today (focus: {wf}). Format: 'Quote' - Author. Personalise in 2 sentences."
            ),
        }
        return prompts.get(cmd.lower(), "")

    def _call(self, user_content: str) -> str:
        messages = (
            [{"role": "system", "content": self._build_system()}]
            + self.history[-20:]
            + [{"role": "user", "content": user_content}]
        )
        return self.orch._ask_ai(messages)

    def _show_response(self, text: str):
        if RICH:
            _console.print(Panel(
                Markdown(text),
                border_style="yellow",
                title="[bold yellow]\U0001f305 Assistant[/bold yellow]",
                title_align="left",
                padding=(1, 2),
            ))
        else:
            print("\n[Assistant]")
            print(text)
            print()

    def _show_instant(self, text: str):
        """Show a non-AI result (task CRUD feedback) with a distinct style."""
        if RICH:
            _console.print(Panel(
                Markdown(text),
                border_style="cyan",
                title="[bold cyan]\U0001f4cb Tasks[/bold cyan]",
                title_align="left",
                padding=(0, 2),
            ))
        else:
            print("\n" + text)

    def run(self):
        if RICH:
            _console.print(Panel.fit(
                "[bold yellow]\U0001f4ac Chat Mode[/bold yellow]  [dim]—  talking to " + self.name + "[/dim]\n"
                "[dim]Type a message, a slash command, or [bold]exit[/bold] to leave.[/dim]\n"
                "[dim]Try: /task add Buy milk  |  /task done 1  |  /tasks  |  /habits  |  /help[/dim]",
                border_style="cyan", padding=(0, 2)
            ))
        else:
            print("\n=== CHAT MODE ===")
            print("Talking to " + self.name + ". Type 'exit' to leave.")
            print("Slash commands: /task add|done|delete|list  /tasks  /habits  /help")
            print()

        while True:
            try:
                if RICH:
                    user_input = Prompt.ask("[bold cyan]You[/bold cyan]")
                else:
                    user_input = input("You: ")
            except (KeyboardInterrupt, EOFError):
                break

            raw = user_input.strip()
            if not raw:
                continue
            if raw.lower() in ("exit", "quit", "q"):
                _console.print("[dim]Leaving chat mode...[/dim]" if RICH else "Leaving chat mode...")
                break

            if raw.lower() == "/help":
                _console.print(Markdown(SLASH_HELP) if RICH else SLASH_HELP)
                continue

            parts = raw.split()
            cmd   = parts[0].lower()

            # ── /task subcommands: instant, no AI ───────────────────
            if cmd == "/task":
                result = self._handle_task_cmd(parts)
                if result is None:
                    _console.print(
                        "[red]Unknown /task subcommand.[/red] Use: list, add, done, delete, cleardone, clearall"
                        if RICH else "Unknown /task subcommand."
                    )
                else:
                    self._show_instant(result)
                # Don't add raw /task commands to AI history
                continue

            # ── other slash commands: go to AI ──────────────────────
            if cmd.startswith("/"):
                prompt = self._slash_prompt(cmd)
                if not prompt:
                    _console.print(
                        ("[red]Unknown command:[/red] " + cmd + ". Type /help for the list.") if RICH
                        else ("Unknown command: " + cmd + ". Type /help.")
                    )
                    continue
            else:
                prompt = raw

            self.history.append({"role": "user", "content": raw})

            if RICH:
                with _console.status("[dim]Thinking...[/dim]", spinner="dots"):
                    response = self._call(prompt)
            else:
                print("Thinking...")
                response = self._call(prompt)

            self._show_response(response)
            self.history.append({"role": "assistant", "content": response})

        _save_chat_to_journal(self.history, self.name)
