# Changelog

All notable changes to Daily AI Assistant are documented here.

---

## [3.2.0] — 2026-06-18

### Tested & Verified
- **`utils/task_manager.py`** — `TaskCRUD` interactive task manager ✅ locally tested
  - Add, complete, delete tasks confirmed working end-to-end
  - Persistent JSON storage in `tasks/today_tasks.json` verified
  - Rich table rendering with ✓ Done / ○ Pending status confirmed
  - `clear_completed`, `clear_all`, and `list_tasks` all functioning correctly
- **`utils/habit_checkin.py`** — `HabitCheckIn` interactive TUI ✅ locally tested
  - Today's status display confirmed correct
  - Check-in streak increment verified (idempotent same-day re-check)
  - Add / remove habit persistence confirmed across sessions
  - Strict vs non-strict streak reset verified
  - `summary_line()` fraction and best-streak output confirmed

### Fixed
- `daily_orchestrator.py` — Pylance type errors resolved across all content block types
  - `.text` access on `ThinkingBlock`, `ToolUseBlock`, and related types replaced with `getattr(..., "text", None)`
  - `None`-subscript guard added before Cohere content access
  - `reportOptionalMemberAccess` on `console.print` eliminated by always instantiating `Console()`
  - `reportArgumentType` for `None → str` fixed on all 5 model lookups

---

## [3.1.0] — 2026-06-17

### Added
- **`utils/task_manager.py`** — interactive CRUD task manager
  - Add, complete, delete tasks from the terminal interactively
  - Persistent storage in `tasks/today_tasks.json`
  - Rich table with ✓ Done / ○ Pending status per task
  - Commands: `a` add · `c` complete · `d` delete · `cl` clear done · `q` quit
- **`utils/habit_viz.py`** — terminal habit progress visualization
  - Rich `█░` progress bars per habit
  - Color-coded by progress: green (>80%) · yellow (>40%) · red (<40%)
  - Streak emoji badges: 🏆 🔥 💪 👍 🌱 💫
  - Summary row: total habits, on-track count, avg streak, best habit
- **`utils/reminder_daemon.py`** — background reminder daemon
  - Runs in a daemon thread — never blocks the app
  - Checks every 30 seconds using `schedule`
  - Fires `🔔 Reminder [HH:MM]: message` in terminal automatically
  - Auto-starts on `python main.py`, stops cleanly on quit
  - `reload_reminders()` to pick up live changes
- **`utils/cli_chat.py`** — auto-saves chat history to journal
  - Every chat session saved to `journal/YYYY-MM-DD-chat.json` on exit
  - Multiple sessions per day append (not overwrite)
  - Shows `💾 Chat saved to journal/<date>-chat.json` confirmation
- **`main.py`** — new CLI flags
  - `--tasks` — open task manager directly
  - `--habits` — show habit visualization directly
  - Version bumped to v3.1

---

## [3.0.0] — 2026-06-16

### Added
- **CLI v3.0** — full rewrite of `main.py` with Rich terminal UI
  - Interactive numbered menu to pick any module
  - `--chat` flag to jump straight into chat mode
  - `--module <name>` to run a single module directly
  - `--provider <name>` to force a specific LLM provider
  - `--list-models` to list available Ollama models
  - `--setup` to re-run the setup wizard
- **`utils/cli_chat.py`** — new ChatGPT-style interactive terminal chat
  - Full multi-turn conversation history (last 20 messages)
  - Slash commands: `/morning` `/tasks` `/habits` `/journal` `/meal` `/weather` `/news` `/focus` `/quote` `/help`
  - Rich panels with markdown rendering
  - Spinner animation while waiting for AI response
- **`utils/setup_wizard.py`** — upgraded to Rich UI
  - Coloured prompts and panels
  - Provider validation loop (prevents typing API key as provider name)

### Fixed
- `_ask_ai()` in `daily_orchestrator.py` now calls providers directly with proper chat-messages format (was using broken flat-string `/api/generate`)
- Groq model updated: `llama-3.1-70b-versatile` → `llama-3.3-70b-versatile` (decommissioned June 2026)
- Cohere updated to `ClientV2` + `command-a-03-2025` (`command-r-plus` removed Sept 2025)
- `news.py` now returns specific error messages for 401, 429, timeout, and connection errors
- `.env.example` updated with correct model names and clear `DEFAULT_PROVIDER` warning
- `.gitignore` now covers `demo_data/*.json` and `reminders/reminders.json`

### Changed
- `daily_orchestrator.py` uses Rich `Rule` headers and `Markdown` rendering throughout
- `setup_wizard.py` default provider changed from `ollama` to `groq` (better out-of-box experience)

---

## [2.0.0] — 2026-06-11

### Added
- Streamlit web demo with 10 module tabs
- Live deployment on Streamlit Cloud
- Multi-provider LLM support: Ollama, OpenAI, Anthropic, Groq, Cohere
- All 10 daily modules: Morning Routine, Tasks, Habits, Journal, Meals, Weather, News, Focus, Reminders, Quote
- `LLMManager` with auto-fallback across providers
- `SetupWizard` for first-time configuration
- `.streamlit/config.toml` dark theme
- Codespaces / devcontainer support

---

## [1.0.0] — Initial Release

### Added
- Basic CLI with `main.py`
- Core module structure
- Ollama local LLM support
