"""CLI Chat Mode - ChatGPT-style interactive terminal chat

Features:
- Full chat history (last 20 messages)
- All slash commands (/morning /tasks /habits /journal /meal /focus /quote /help)
- Rich terminal UI with markdown rendering
- Type 'exit' or 'quit' to leave chat
"""

from datetime import date, datetime
from pathlib import Path
import json

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.markdown import Markdown
    from rich.rule import Rule
    from rich.prompt import Prompt
    RICH = True
except ImportError:
    RICH = False

console = Console() if RICH else None


SLASH_HELP = """
| Command   | What it does                        |
|-----------|-------------------------------------|
| /morning  | Personalised morning routine        |
| /tasks    | Prioritise your active tasks        |
| /habits   | Analyse your habit streaks          |
| /journal  | 3 journaling prompts for today      |
| /meal     | One-day Indian meal plan            |
| /weather  | Activity suggestions for your city  |
| /news     | Concise tech + health news briefing |
| /focus    | Pomodoro focus schedule             |
| /quote    | Motivational quote of the day       |
| /help     | Show this table                     |
| exit/quit | Leave chat mode                     |
"""


class CLIChat:
    def __init__(self, orchestrator, prefs: dict):
        self.orch    = orchestrator
        self.prefs   = prefs
        self.history = []   # [{"role": ..., "content": ...}]
        self.name    = prefs.get("name", "User")

    def _build_system(self) -> str:
        now    = datetime.now().strftime("%A, %d %B %Y - %I:%M %p")
        p      = self.prefs
        d      = p.get("dietary", {})
        return (
            f"You are a warm, intelligent personal daily assistant for {p.get('name', 'User')}.\n"
            f"Today is {now}.\n"
            f"- Wake-up: {p.get('wake_time', '07:00')} | Fitness: {p.get('fitness_level', 'moderate')} | Diet: {d.get('type', 'balanced')}\n"
            f"- Work focus: {p.get('work_focus', 'general')}\n"
            "Personality: concise, warm, practical, motivating - like a brilliant friend who is also a life coach.\n"
            "Use markdown (bullets, bold, tables) when it helps clarity.\n"
            "Always give a useful, personalised response."
        )

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
                f" Fitness: {fl}. Work: {wf}. Time blocks, one action each. Be energising."
            ),
            "/tasks": (
                f"List and prioritise {n}'s active tasks (most to least important). Work: {wf}. Add a 1-line tip each."
            ),
            "/habits": (
                f"Analyse {n}'s habits. Give: 1) What's going well 2) Which to focus on next 3) Science-backed tip."
            ),
            "/journal": (
                f"Give {n} 3 thoughtful journaling prompts for today based on work focus ({wf}). Reflective and personal."
            ),
            "/meal": (
                f"Create a {dt} meal plan for {n} today. Indian cuisine. Fitness: {fl}. ~2000 kcal."
                " 3 meals + 1 snack. For each: name, ingredients, kcal, prep time."
            ),
            "/weather": (
                f"Suggest 4 activities for {n} today. Fitness: {fl}. 2 outdoor, 2 indoor. Duration + what to bring."
            ),
            "/news": (
                f"Give {n} a 5-bullet news briefing for {d} covering: Technology, AI & ML, Health. Factual."
            ),
            "/focus": (
                f"Create a Pomodoro focus schedule for {n} (work: {wf}). "
                "4 x 25-min blocks, 5-min breaks, 15-min break after block 4. Clean timetable format."
            ),
            "/quote": (
                f"Give {n} one powerful quote for today (focus: {wf}). Format: 'Quote' - Author. Personalise in 2 sentences."
            ),
            "/help": None,  # handled separately
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
            console.print(Panel(
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
            console.print(Panel.fit(
                f"[bold yellow]\U0001f4ac Chat Mode[/bold yellow]  [dim]-  talking to {self.name}[/dim]\n"
                "[dim]Type a message, a slash command, or [bold]exit[/bold] to leave.[/dim]\n"
                "[dim]Try: /morning  /tasks  /habits  /meal  /focus  /help[/dim]",
                border_style="cyan", padding=(0, 2)
            ))
        else:
            print("\n=== CHAT MODE ===")
            print(f"Talking to {self.name}. Type 'exit' to leave.")
            print("Slash commands: /morning /tasks /habits /meal /focus /help")
            print()

        while True:
            # Get input
            try:
                if RICH:
                    user_input = Prompt.ask(f"[bold cyan]You[/bold cyan]")
                else:
                    user_input = input("You: ")
            except (KeyboardInterrupt, EOFError):
                break

            raw = user_input.strip()
            if not raw:
                continue
            if raw.lower() in ("exit", "quit", "q"):
                if RICH:
                    console.print("[dim]Leaving chat mode...[/dim]")
                else:
                    print("Leaving chat mode...")
                break

            # Slash: /help
            if raw.lower() == "/help":
                if RICH:
                    console.print(Markdown(SLASH_HELP))
                else:
                    print(SLASH_HELP)
                continue

            # Slash command — build prompt
            cmd = raw.lower().split()[0]
            if cmd.startswith("/"):
                prompt = self._slash_prompt(cmd)
                if not prompt:
                    if RICH:
                        console.print(f"[red]Unknown command:[/red] {cmd}. Type /help for the list.")
                    else:
                        print(f"Unknown command: {cmd}. Type /help.")
                    continue
                display = raw   # show what user typed
            else:
                prompt  = raw
                display = raw

            # Add to history
            self.history.append({"role": "user", "content": display})

            # Call AI
            if RICH:
                with console.status("[dim]Thinking...[/dim]", spinner="dots"):
                    response = self._call(prompt)
            else:
                print("Thinking...")
                response = self._call(prompt)

            # Show response
            self._show_response(response)

            # Save assistant turn to history
            self.history.append({"role": "assistant", "content": response})
