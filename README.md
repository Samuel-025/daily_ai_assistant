# 🌅 Daily AI Assistant v3.2

> **All-in-one personalized daily life tool** — powered by Ollama (local) or any cloud LLM (OpenAI, Anthropic, Groq, Cohere).  
> Two interfaces: **Rich CLI** with interactive menu + chat mode, and a **Streamlit web demo**.

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Streamlit](https://img.shields.io/badge/Streamlit-Live%20Demo-ff4b4b?logo=streamlit)
![LLM](https://img.shields.io/badge/LLM-Ollama%20%7C%20OpenAI%20%7C%20Anthropic%20%7C%20Groq%20%7C%20Cohere-purple)

---

## 🚀 Live Demo

[👉 Open in Streamlit](https://dailyaiassistant-bfszw6tsvquoaav2acjhuo.streamlit.app/)

> No installation needed — try all 10 modules directly in your browser!

---

## ✨ Features

| Module | Description |
|---|---|
| 🌅 **Morning Routine** | Personalised time-block wake-up plan |
| 📋 **Task Manager** | Add / complete / delete tasks interactively (CRUD) |
| 🎯 **Habit Tracker** | Rich progress bars + streak visualization in terminal |
| ✅ **Habit Check-in** | Interactive TUI to log today's habits + manage streaks |
| 📝 **Daily Journal** | Write entries + AI reflection & insights |
| 🍽️ **Meal Planner** | Nutrition-aware meal plan for your diet type |
| 🌤️ **Weather + Activities** | Real weather data + AI activity suggestions |
| 📰 **News Briefing** | Top headlines summarized by AI |
| ⏱️ **Focus Timer** | Pomodoro-based focus schedule planner |
| 🔔 **Reminders** | Background daemon — fires reminders automatically while you use the app |
| 💡 **Quote of the Day** | Personalised motivational quote |
| 💬 **Chat Mode** | Multi-turn ChatGPT-style chat with slash commands + auto-saves to journal |

---

## 🖥️ CLI Quick Start

```bash
git clone https://github.com/Samuel-025/daily_ai_assistant.git
cd daily_ai_assistant

# Create venv (use Python 3.11–3.13)
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

python main.py --setup          # First-time setup wizard
python main.py                  # Interactive menu
```

### CLI Commands

```bash
python main.py                        # Interactive menu (default)
python main.py --chat                 # Jump straight to chat mode
python main.py --tasks                # Open task manager directly
python main.py --habits               # Show habit visualization directly
python main.py --module morning       # Run a single module
python main.py --provider groq        # Force a specific LLM provider
python main.py --list-models          # List available Ollama models
python main.py --setup                # Re-run setup wizard
```

### Chat Mode Slash Commands

| Command | What it does |
|---|---|
| `/morning` | Personalised morning routine |
| `/tasks` | Prioritised task list |
| `/habits` | Habit streak analysis |
| `/checkin` | Interactive habit check-in |
| `/journal` | 3 journaling prompts for today |
| `/meal` | One-day meal plan |
| `/weather` | Activity suggestions |
| `/news` | Tech + health news briefing |
| `/focus` | Pomodoro focus schedule |
| `/quote` | Quote of the day |
| `/help` | Show all commands |
| `exit` | Leave chat mode (auto-saves session to `journal/`) |

---

## 🆕 What's New in v3.2

### ✅ TaskCRUD — Fully Tested & Verified
- Add, complete, delete tasks interactively from the CLI — **locally tested end-to-end**
- Persistent storage in `tasks/today_tasks.json` confirmed across sessions
- Rich table with ✓ Done / ○ Pending status per task
- `clear_completed`, `clear_all`, and `list_tasks` all working correctly
- Commands: `a` add · `c` complete · `d` delete · `cl` clear done · `q` quit

### ✅ HabitCheckIn — Fully Tested & Verified
- Interactive TUI to log today's habits — **locally tested end-to-end**
- Streak increment confirmed correct; same-day re-check is idempotent (no double-increment)
- Add / remove habits persist correctly across sessions
- Strict mode resets skipped habit streaks; non-strict mode preserves them
- `summary_line()` correctly shows done fraction and best streak

### 🔧 Type Safety Fixes (`daily_orchestrator.py`)
- Pylance `reportAttributeAccessIssue` resolved for all Anthropic/Cohere content block types
- `None`-subscript guard added before Cohere content access
- `console` always instantiated — no more `reportOptionalMemberAccess` errors

---

## 🆕 What's New in v3.1

### 📊 Habit Progress Visualization
- Rich `█░` progress bars per habit in the terminal
- Color-coded by progress: 🟢 green (>80%) · 🟡 yellow (>40%) · 🔴 red (<40%)
- Streak emoji badges: 🏆 🔥 💪 👍 🌱
- Summary row: total habits, on-track count, avg streak, best habit

### 🔔 Background Reminder Daemon
- Runs in a **background thread** — never blocks the app
- Checks every 30 seconds using the `schedule` library
- Fires `🔔 Reminder [HH:MM]: message` in the terminal automatically
- Auto-starts on `python main.py`, stops cleanly on quit

### 💾 Chat History → Journal
- Every chat session is **auto-saved** to `journal/YYYY-MM-DD-chat.json` on exit
- Multiple sessions per day append (not overwrite)

---

## 🌐 Run Streamlit Demo Locally

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Then open **http://localhost:8501** in your browser.

---

## ☁️ Deploy Your Own (Free)

1. Fork this repo
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**
3. Set main file: `streamlit_app.py`
4. Add secrets in **App settings → Secrets**:

```toml
GROQ_API_KEY = "your_key_here"
OPENWEATHER_API_KEY = "your_key_here"
NEWS_API_KEY = "your_key_here"
```

---

## ⚙️ API Keys Reference

| Provider | Where to get | Free? |
|---|---|---|
| **Ollama** | No key — runs locally | ✅ Free |
| **Groq** | [console.groq.com](https://console.groq.com) | ✅ Free tier |
| **OpenAI** | [platform.openai.com](https://platform.openai.com/api-keys) | ❌ Paid |
| **Anthropic** | [console.anthropic.com](https://console.anthropic.com) | ❌ Paid |
| **Cohere** | [dashboard.cohere.com](https://dashboard.cohere.com) | ✅ Free tier |
| **OpenWeatherMap** | [openweathermap.org/api](https://openweathermap.org/api) | ✅ Free tier |
| **NewsAPI** | [newsapi.org](https://newsapi.org) | ✅ Free tier |

---

## 📁 Project Structure

```
daily_ai_assistant/
├── main.py                    # 🖥️  CLI v3.2 — menu + chat + task + habits
├── streamlit_app.py           # 🌐  Streamlit web demo
├── requirements.txt
├── .env.example               # API keys template → copy to .env
├── config/
│   └── settings.py            # Settings & API key loader
├── models/
│   └── llm_manager.py         # Multi-provider LLM manager
├── utils/
│   ├── daily_orchestrator.py  # All 10 modules logic
│   ├── cli_chat.py            # ChatGPT-style chat + auto-saves to journal/
│   ├── task_manager.py        # 📋 Interactive CRUD task manager ✅ tested
│   ├── habit_checkin.py       # ✅ Interactive habit check-in TUI ✅ tested
│   ├── habit_viz.py           # 📊 Terminal habit progress visualization
│   ├── reminder_daemon.py     # 🔔 Background reminder thread
│   ├── setup_wizard.py        # First-time setup (Rich UI)
│   ├── weather.py
│   ├── news.py
│   └── reminders.py
├── demo_data/                 # Shared data (CLI + Streamlit)
├── preferences/               # user_prefs.json
├── tasks/                     # today_tasks.json
├── habits/                    # current_habits.json
├── journal/                   # YYYY-MM-DD.json + YYYY-MM-DD-chat.json
└── reminders/                 # reminders.json
```

---

## 🤝 Contributing

1. Fork → `git checkout -b feature/my-feature`
2. Commit → `git commit -m "feat: my feature"`
3. Push → `git push origin feature/my-feature`
4. Open a Pull Request

---

## 📝 License

MIT — free to use, modify, and distribute.

---

*Built with ❤️ by [Samuel-025](https://github.com/Samuel-025)*
