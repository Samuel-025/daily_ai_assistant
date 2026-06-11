# 🌅 Daily AI Assistant v2.0

> **All-in-one personalized daily life tool** — powered by Ollama (local) or any cloud LLM (OpenAI, Anthropic, Groq, Cohere). Fully customizable. Works 100% offline with Ollama.

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Streamlit](https://img.shields.io/badge/Streamlit-Live%20Demo-ff4b4b?logo=streamlit)
![LLM](https://img.shields.io/badge/LLM-Ollama%20%7C%20OpenAI%20%7C%20Anthropic%20%7C%20Groq%20%7C%20Cohere-purple)

---

## 🚀 Live Demo

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://dailyaiassistant-bfszw6tsvquoaav2acjhuo.streamlit.app/)

👉 **[https://dailyaiassistant-bfszw6tsvquoaav2acjhuo.streamlit.app/](https://dailyaiassistant-bfszw6tsvquoaav2acjhuo.streamlit.app/)**

> No installation needed — try all 10 modules directly in your browser!

---

## ✨ Features

| Module | Description |
|---|---|
| 🌅 **Morning Routine** | Personalised wake-up plan based on fitness & schedule |
| 📋 **Task Manager** | Add tasks, mark done, AI-prioritised list |
| 🎯 **Habit Tracker** | Visual streak tracker with AI coaching |
| 📝 **Daily Journal** | Write entries + AI reflection & insights |
| 🍽️ **Meal Planner** | Nutrition-aware meal plan for your diet type |
| 🌤️ **Weather + Activities** | Real weather data + AI activity suggestions |
| 📰 **News Briefing** | Top headlines summarized by AI |
| ⏱️ **Focus Timer** | Pomodoro-based focus schedule planner |
| 🔔 **Reminders** | Daily + date-specific reminder system |
| 💡 **Quote of the Day** | Personalised motivational quote + free AI chat |

---

## 🖥️ Run Locally (CLI)

```bash
git clone https://github.com/Samuel-025/daily_ai_assistant.git
cd daily_ai_assistant
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py --setup      # First-time setup wizard
python main.py              # Run everything
```

---

## 🌐 Run Streamlit Demo Locally

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Then open **http://localhost:8501** in your browser.

---

## ☁️ Deploy Your Own Live Demo (Free)

**3 steps to your own Streamlit deployment:**

### Step 1 — Sign up
Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.

### Step 2 — Deploy
Click **"New app"** and fill in:

| Field | Value |
|---|---|
| Repository | `Samuel-025/daily_ai_assistant` |
| Branch | `main` |
| Main file path | `streamlit_app.py` |

Click **"Deploy"**. That's it! 🎉

### Step 3 — Add API Keys (Optional)
In your Streamlit Cloud dashboard → **App settings → Secrets**, add:

```toml
OPENAI_API_KEY = "your_key_here"
GROQ_API_KEY = "your_key_here"
ANTHROPIC_API_KEY = "your_key_here"
OPENWEATHER_API_KEY = "your_key_here"
NEWS_API_KEY = "your_key_here"
```

> 💡 **No API key?** Use Groq (free tier) or Ollama locally. The app UI works without any keys for exploration.

---

## ⚙️ Configuration

### API Keys

| Provider | Where to get key | Free tier? |
|---|---|---|
| **Ollama** | No key — runs locally | ✅ Completely free |
| **Groq** | [console.groq.com](https://console.groq.com) | ✅ Free tier |
| **OpenAI** | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) | ❌ Paid |
| **Anthropic** | [console.anthropic.com](https://console.anthropic.com) | ❌ Paid |
| **Cohere** | [dashboard.cohere.com](https://dashboard.cohere.com) | ✅ Free tier |
| **OpenWeatherMap** | [openweathermap.org/api](https://openweathermap.org/api) | ✅ Free tier |
| **NewsAPI** | [newsapi.org](https://newsapi.org) | ✅ Free tier |

### Ollama Setup (Free Local AI)

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh     # Linux/Mac
# Windows: https://ollama.ai/download

# Pull a model
ollama pull llama3.2        # Fast & smart (2GB) — recommended
ollama pull mistral         # Great reasoning (4GB)
ollama pull phi3            # Lightweight (1.5GB)

# Start server
ollama serve
```

---

## 📁 Project Structure

```
daily_ai_assistant/
├── streamlit_app.py             # 🌐 Streamlit web demo (10 tabs)
├── main.py                      # 🖥️ CLI entry point
├── requirements.txt
├── .env.example                 # API keys template
├── .gitignore
├── .streamlit/
│   ├── config.toml              # Dark theme config
│   └── secrets.toml.example     # Streamlit Cloud secrets template
├── config/
│   └── settings.py
├── models/
│   └── llm_manager.py           # Ollama + all cloud LLMs
├── utils/
│   ├── daily_orchestrator.py
│   ├── weather.py
│   ├── news.py
│   ├── reminders.py
│   └── setup_wizard.py
├── preferences/ tasks/ habits/ journal/ meals/ reminders/
```

---

## 🚀 CLI Usage

```bash
python main.py                        # Run all modules
python main.py --setup                # First-time setup wizard
python main.py --module morning       # Single module
python main.py --provider groq        # Force a provider
python main.py --list-models          # List Ollama models
```

---

## 🤝 Contributing

1. Fork → `git checkout -b feature/my-feature`
2. Commit → `git commit -m "Add my feature"`
3. Push → `git push origin feature/my-feature`
4. Open a Pull Request

---

## 📝 License

MIT License — free to use, modify, and distribute.

---

*Built with ❤️ by [Samuel-025](https://github.com/Samuel-025)*
