"""CLI Chat Mode - ChatGPT-style interactive terminal chat

Features:
- Full chat history (last 20 messages)
- All slash commands (/morning /tasks /habits /journal /meal /focus /quote /help)
- Rich terminal UI with markdown rendering
- Auto-saves chat history to journal/ at end of session
- Type 'exit' or 'quit' to leave chat
- Slash commands use LIVE data from tasks / habits / journal / reminders JSON files
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

# Always a Console instance (real or fallback) — never None
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

console = _console  # public alias kept for compatibility

SLASH_HELP = """
| Command    | What it does                            |
|------------|-----------------------------------------|
| /morning   | Personalised morning routine            |
| /tasks     | Prioritise your REAL active tasks       |
| /habits    | Analyse your REAL habit streaks         |
| /journal   | Reflect on today's journal entry        |
| /meal      | One-day Indian meal plan                |
| /weather   | Activity suggestions for your city      |
| /news      | Concise tech + health news briefing     |
| /focus     | Pomodoro focus schedule                 |
| /reminders | Show today's due reminders              |
| /quote     | Motivational quote of the day           |
| /help      | Show this table                         |
| exit/quit  | Leave chat mode                         |
"""

JOURNAL_DIR = Path("journal")


def _load_json(path: Path, default):
    """Safely load a JSON file, returning default on any error."""
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default


def _save_chat_to_journal(history: list, name: str):
    """Save full chat session to journal/YYYY-MM-DD-chat.json"""
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

    sessions.append({
        "time":     datetime.now().strftime("%H:%M:%S"),
        "messages": history
    })

    filename.write_text(
        json.dumps({"date": today, "user": name, "sessions": sessions}, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    _console.print(f"[dim]\U0001f4be Chat saved to {filename}[/dim]" if RICH else f"Chat saved to {filename}")


class CLIChat:
    def __init__(self, orchestrator, prefs: dict):
        self.orch    = orchestrator
        self.prefs   = prefs
        self.history: list = []
        self.name    = prefs.get("name", "User")
        # Resolve the project root from the orchestrator so paths stay consistent
        self.base_dir: Path = getattr(orchestrator, "base_dir", Path("."))

    # ── Live data loaders ────────────────────────────────────────
    def _tasks_context(self) -> str:
        """Return a text summary of current tasks from tasks/today_tasks.json."""
        f  = self.base_dir / "tasks" / "today_tasks.json"
        td = _load_json(f, {"tasks": [], "completed": []})
        active    = td.get("tasks", [])
        completed = td.get("completed", [])
        if not active and not completed:
            return "(No tasks recorded yet. Add tasks to tasks/today_tasks.json)"
        lines = []
        if active:
            lines.append("Active tasks:")
            for t in active:
                lines.append(f"  - {t}")
        if completed:
            lines.append("Completed tasks:")
            for t in completed:
                lines.append(f"  - [done] {t}")
        return "\n".join(lines)

    def _habits_context(self) -> str:
        """Return habit data as text from habits/current_habits.json."""
        f  = self.base_dir / "habits" / "current_habits.json"
        default_h = {"habits": [
            {"name": "Drink 8 glasses of water", "streak": 0, "target": 30},
            {"name": "Exercise 20 min",           "streak": 0, "target": 30},
            {"name": "Read 10 min",               "streak": 0, "target": 21},
            {"name": "Meditate 5 min",            "streak": 0, "target": 21},
            {"name": "Sleep by 11 PM",            "streak": 0, "target": 30},
        ]}
        hd = _load_json(f, default_h)
        habits = hd.get("habits", [])
        if not habits:
            return "(No habits tracked yet.)"
        lines = ["Current habit streaks:"]
        for h in habits:
            s = h.get("streak", 0)
            t = h.get("target", 30)
            pct = int((s / t * 100) if t else 0)
            lines.append(f"  - {h['name']}: {s}/{t} days ({pct}% to goal)")
        return "\n".join(lines)

    def _journal_context(self) -> str:
        """Return today's journal entry if it exists."""
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
        """Return today's due reminders."""
        try:
            reminders = self.orch.reminder_mgr.get_due_today()
        except Exception:
            return "(Could not load reminders.)"
        if not reminders:
            return "(No reminders due today.)"
        lines = ["Today's reminders:"]
        for r in reminders:
            lines.append(f"  - {r.get('time', '?')}: {r.get('message', '')}")
        return "\n".join(lines)

    def _meals_context(self) -> str:
        """Return today's meal plan if saved."""
        today = datetime.now().strftime("%Y-%m-%d")
        mf    = self.base_dir / "meals" / f"{today}.json"
        md    = _load_json(mf, {})
        if not md:
            return "(No meal plan saved for today yet.)"
        lines = ["Today's saved meal plan:"]
        for meal, detail in md.items():
            lines.append(f"  {meal}: {detail}")
        return "\n".join(lines)

    # ── System prompt (enriched with live context) ───────────────
    def _build_system(self) -> str:
        now = datetime.now().strftime("%A, %d %B %Y - %I:%M %p")
        p   = self.prefs
        d   = p.get("dietary", {})
        return (
            "You are a warm, intelligent personal daily assistant for " + p.get("name", "User") + ".\n"
            "Today is " + now + ".\n"
            "- Wake-up: " + p.get("wake_time", "07:00") +
            " | Fitness: " + p.get("fitness_level", "moderate") +
            " | Diet: " + d.get("type", "balanced") + "\n"
            "- Work focus: " + p.get("work_focus", "general") + "\n\n"
            "LIVE USER DATA (always reference this when asked):\n"
            + self._tasks_context() + "\n\n"
            + self._habits_context() + "\n\n"
            + self._journal_context() + "\n\n"
            + self._reminders_context() + "\n\n"
            "Personality: concise, warm, practical, motivating - like a brilliant friend who is also a life coach.\n"
            "Use markdown (bullets, bold, tables) when it helps clarity.\n"
            "Always give a useful, personalised response based on the LIVE DATA above."
        )

    # ── Slash command prompts (now with live data injected) ──────
    def _slash_prompt(self, cmd: str) -> str:
        p  = self.prefs
        wt = p.get("wake_time", "07:00")
        fl = p.get("fitness_level", "moderate")
        wf = p.get("work_focus", "general")
        dt = p.get("dietary", {}).get("type", "balanced")
        n  = self.name
        d  = str(date.today())

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
                f"3) Acknowledge the completed ones with a brief motivating note."
            ),
            "/habits": (
                f"Here are {n}'s current habit streaks:\n{self._habits_context()}\n\n"
                f"Please: 1) Highlight what's going well. "
                f"2) Identify which habit needs the most attention and why. "
                f"3) Give one science-backed tip to strengthen the weakest habit."
            ),
            "/journal": (
                f"{self._journal_context()}\n\n"
                + (
                    f"Reflect on {n}'s journal entry above. Give 2 meaningful insights and 1 encouragement."
                    if "No journal entry" not in self._journal_context()
                    else f"Give {n} 3 thoughtful journaling prompts for today based on work focus ({wf}). Reflective and personal."
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
            "/help": None,
        }
        return prompts.get(cmd.lower(), "") or ""

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

    def run(self):
        if RICH:
            _console.print(Panel.fit(
                "[bold yellow]\U0001f4ac Chat Mode[/bold yellow]  [dim]-  talking to " + self.name + "[/dim]\n"
                "[dim]Type a message, a slash command, or [bold]exit[/bold] to leave.[/dim]\n"
                "[dim]Try: /morning  /tasks  /habits  /meal  /focus  /help[/dim]",
                border_style="cyan", padding=(0, 2)
            ))
        else:
            print("\n=== CHAT MODE ===")
            print("Talking to " + self.name + ". Type 'exit' to leave.")
            print("Slash commands: /morning /tasks /habits /meal /focus /reminders /help")
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
                if RICH:
                    _console.print(Markdown(SLASH_HELP))
                else:
                    print(SLASH_HELP)
                continue

            cmd = raw.lower().split()[0]
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
