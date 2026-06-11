# 🌅 Daily AI Assistant

All-in-one personalized daily life tool that integrates with **Ollama (local LLM)** + any cloud model via API keys.

## Features

✅ **Personalized Morning Routine** - AI-generated based on your fitness level & work focus  
✅ **AI Task Prioritization** - Smart task management with AI ranking  
✅ **Habit Tracker** - Track streaks and build consistency  
✅ **Daily Journal with AI Insights** - Reflect + get AI analysis  
✅ **Meal Planner** - Personalized nutrition based on dietary preferences  
✅ **Weather Activity Suggestions** - Location-aware activity recommendations  

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/Samuel-025/daily_ai_assistant.git
cd daily_ai_assistant
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up API Keys

```bash
cp .env.example .env
# Edit .env and add your API keys
```

### 4. Install Ollama (Optional but Recommended)

```bash
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull llama3.2
```

### 5. Run the Assistant

```bash
python main.py
```

## 🔧 Configuration

### User Preferences

Edit `preferences/user_prefs.json`:

```json
{
  "name": "Your Name",
  "wake_time": "07:00",
  "sleep_time": "23:00",
  "preferences": {
    "morning_routine": true,
    "task_prioritization": "ai",
    "habit_tracking": true,
    "daily_journal": true,
    "meal_planning": true,
    "weather_suggestions": true
  },
  "dietary": {
    "type": "balanced",
    "restrictions": [],
    "preferences": []
  },
  "fitness_level": "moderate",
  "work_focus": "general"
}
```

### API Keys

| Provider | Type | Default Model |
|----------|------|---------------|
| Ollama | Local | llama3.2 |
| OpenAI | Cloud | gpt-4o |
| Anthropic | Cloud | claude-3-sonnet |
| Groq | Cloud (Fast) | llama-3.1-70b |
| Cohere | Cloud | command-r-plus |

## 📁 Project Structure

```
daily_ai_assistant/
├── main.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── LICENSE
├── config/
│   ├── __init__.py
│   └── settings.py
├── models/
│   ├── __init__.py
│   └── llm_manager.py
├── utils/
│   ├── __init__.py
│   └── daily_orchestrator.py
├── preferences/
├── tasks/
├── habits/
├── journal/
└── meals/
```

## 📝 License

MIT License - Free to use and modify

---
Built with ❤️ for personalized daily productivity
