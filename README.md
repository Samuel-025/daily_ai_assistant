# 🌅 Daily AI Assistant v2.0

> **All-in-one personalized daily life tool** — powered by Ollama (local) or any cloud LLM (OpenAI, Anthropic, Groq, Cohere). Fully customizable. Works 100% offline with Ollama.

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![LLM](https://img.shields.io/badge/LLM-Ollama%20%7C%20OpenAI%20%7C%20Anthropic%20%7C%20Groq%20%7C%20Cohere-purple)

---

## ✨ Features

| Module | Description |
|---|---|
| 🌅 **Morning Routine** | Personalized wake-up plan based on fitness & schedule |
| 📋 **Task Manager** | AI-prioritized daily task list |
| 🎯 **Habit Tracker** | Visual streak tracker for daily habits |
| 📝 **Daily Journal** | Journal prompts + AI-powered insights over time |
| 🍽️ **Meal Planner** | Nutrition-aware meal plan for your diet type |
| 🌤️ **Weather + Activities** | Real weather data + AI activity suggestions |
| 📰 **News Briefing** | Top headlines summarized by AI |
| ⏱️ **Focus Timer** | Pomodoro-based focus schedule planner |
| 🔔 **Reminders** | Daily + date-specific reminder system |
| 💡 **Quote of the Day** | Personalized motivational quote |

---

## 🖥️ Installation Guide

### Prerequisites

- **Python 3.9+** — [Download](https://www.python.org/downloads/)
- **Git** — [Download](https://git-scm.com/)
- **Ollama** (optional, for local AI) — [Download](https://ollama.ai/)

---

### Step 1 — Clone the Repository

```bash
git clone https://github.com/Samuel-025/daily_ai_assistant.git
cd daily_ai_assistant
```

---

### Step 2 — Create a Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate it:
# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

---

### Step 3 — Install Dependencies

```bash
pip install -r requirements.txt
```

---

### Step 4 — Run the Setup Wizard

The easiest way to configure everything:

```bash
python main.py --setup
```

This will ask you for:
- Your name, wake time, city
- Fitness level and diet type
- Which LLM provider to use
- API keys (optional — you can skip any)

It automatically creates your `.env` and `preferences/user_prefs.json`.

---

### Step 5 — (Optional) Set Up Ollama for Free Local AI

Ollama lets you run AI **completely free and offline** on your machine.

```bash
# Install Ollama
# Linux / macOS:
curl -fsSL https://ollama.ai/install.sh | sh

# Windows: download installer from https://ollama.ai/download

# Pull a model (choose one):
ollama pull llama3.2        # Recommended — fast & smart (2GB)
ollama pull mistral         # Great for reasoning (4GB)
ollama pull phi3            # Lightweight (1.5GB)
ollama pull gemma2          # Google's model (5GB)

# Start Ollama server (runs in background)
ollama serve
```

> ✅ Once Ollama is running, the app will use it automatically — **no API key needed!**

---

### Step 6 — Run the Assistant

```bash
python main.py
```

---

## ⚙️ Manual Configuration

### API Keys

Copy `.env.example` to `.env` and fill in your keys:

```bash
cp .env.example .env
```

| Provider | Where to get key | Free tier? |
|---|---|---|
| **Ollama** | No key needed — runs locally | ✅ Completely free |
| **Groq** | [console.groq.com](https://console.groq.com) | ✅ Free tier |
| **OpenAI** | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) | ❌ Paid |
| **Anthropic** | [console.anthropic.com](https://console.anthropic.com) | ❌ Paid |
| **Cohere** | [dashboard.cohere.com](https://dashboard.cohere.com) | ✅ Free tier |
| **OpenWeatherMap** | [openweathermap.org/api](https://openweathermap.org/api) | ✅ Free tier |
| **NewsAPI** | [newsapi.org](https://newsapi.org) | ✅ Free tier |

---

### User Preferences

Edit `preferences/user_prefs.json` (created after first run or setup wizard):

```json
{
  "name": "Your Name",
  "wake_time": "07:00",
  "fitness_level": "moderate",
  "work_focus": "software development",
  "dietary": {
    "type": "vegetarian",
    "restrictions": ["gluten"],
    "preferences": ["Indian cuisine"]
  },
  "news_categories": ["technology", "health"],
  "preferences": {
    "morning_routine": true,
    "task_prioritization": "ai",
    "habit_tracking": true,
    "daily_journal": true,
    "meal_planning": true,
    "weather_suggestions": true,
    "news_briefing": true,
    "focus_timer": true,
    "reminders": true,
    "motivational_quote": true
  }
}
```

---

## 🚀 Usage

### Run Everything
```bash
python main.py
```

### Run a Specific Module Only
```bash
python main.py --module morning
python main.py --module tasks
python main.py --module habits
python main.py --module journal
python main.py --module meals
python main.py --module weather
python main.py --module news
python main.py --module focus
python main.py --module reminders
python main.py --module quote
```

### Force a Specific LLM Provider
```bash
python main.py --provider ollama
python main.py --provider groq
python main.py --provider openai
python main.py --provider anthropic
```

### List Available Ollama Models
```bash
python main.py --list-models
```

---

## 📁 Project Structure

```
daily_ai_assistant/
├── main.py                          # Entry point + CLI
├── requirements.txt                 # Python dependencies
├── .env.example                     # API keys template
├── .gitignore
├── LICENSE
├── README.md
│
├── config/
│   └── settings.py                  # All settings & API key management
│
├── models/
│   └── llm_manager.py               # Ollama + cloud LLM integration
│
├── utils/
│   ├── daily_orchestrator.py        # Coordinates all modules
│   ├── weather.py                   # OpenWeatherMap integration
│   ├── news.py                      # NewsAPI integration
│   ├── reminders.py                 # Reminder system
│   └── setup_wizard.py              # First-time setup CLI
│
├── preferences/
│   └── user_prefs.json              # Your saved preferences (auto-created)
│
├── tasks/
│   └── today_tasks.json             # Today's task list
│
├── habits/
│   └── current_habits.json          # Habit tracking data
│
├── journal/
│   └── YYYY-MM-DD.json              # Daily journal entries
│
├── reminders/
│   └── reminders.json               # Your reminders list
│
└── meals/                           # Meal plan history
```

---

## 💡 Adding Tasks & Habits

### Add Tasks (`tasks/today_tasks.json`):
```json
{
  "tasks": [
    "Review project proposal",
    "Reply to important emails",
    "30-minute workout"
  ],
  "completed": []
}
```

### Add Habits (`habits/current_habits.json`):
```json
{
  "habits": [
    {"name": "Drink 8 glasses of water", "streak": 5, "target": 1},
    {"name": "Exercise 20 min",           "streak": 3, "target": 1},
    {"name": "Read before sleep",         "streak": 7, "target": 1}
  ]
}
```

### Write a Journal Entry (`journal/2026-06-12.json`):
```json
{
  "entry": "Today was productive. Finished the main feature and felt energized.",
  "mood": "great"
}
```

---

## 🤝 Contributing

1. Fork this repo
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit: `git commit -m "Add my feature"`
4. Push: `git push origin feature/my-feature`
5. Open a Pull Request

---

## 📝 License

MIT License — free to use, modify, and distribute.

---

*Built with ❤️ by [Samuel-025](https://github.com/Samuel-025)*
