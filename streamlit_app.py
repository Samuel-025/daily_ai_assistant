#!/usr/bin/env python3
"""
Daily AI Assistant - Streamlit Demo App
Live demo: interact with all modules in your browser
"""

import streamlit as st
import json
import os
from pathlib import Path
from datetime import datetime, date
from dotenv import load_dotenv

load_dotenv()

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="🌅 Daily AI Assistant",
    page_icon="🌅",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  .main { background-color: #0e1117; }
  .block-container { padding-top: 1.5rem; }
  .stTabs [data-baseweb="tab"] { font-size: 15px; font-weight: 600; }
  .feature-card {
    background: linear-gradient(135deg, #1e2130, #252840);
    border-radius: 12px;
    padding: 18px 20px;
    margin-bottom: 10px;
    border-left: 4px solid #7c6af7;
  }
  .metric-box {
    background: #1e2130;
    border-radius: 10px;
    padding: 14px;
    text-align: center;
  }
  .status-ok  { color: #4ade80; font-weight: bold; }
  .status-err { color: #f87171; font-weight: bold; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────
DATA_DIR = Path("demo_data")
DATA_DIR.mkdir(exist_ok=True)

def load_json(path: Path, default):
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            pass
    path.write_text(json.dumps(default, indent=2))
    return default

def save_json(path: Path, data):
    path.write_text(json.dumps(data, indent=2))

def get_llm_manager():
    """Build LLM manager from sidebar keys or env."""
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent))
        from config.settings import Settings
        from models.llm_manager import LLMManager
        s = Settings()
        # Override with sidebar keys
        for p, k in st.session_state.get("api_keys", {}).items():
            if k:
                s.set_api_key(p, k)
        prov = st.session_state.get("provider", "ollama")
        s.default_provider = prov
        s.use_local_first = (prov == "ollama")
        return LLMManager(s), prov
    except Exception as e:
        return None, str(e)

def ask_ai(prompt: str) -> str:
    """Call AI and return response string."""
    llm, prov = get_llm_manager()
    if llm is None:
        return f"⚠️ Could not initialise LLM: {prov}"
    with st.spinner("🤖 Thinking..."):
        result = llm.generate(prompt, provider=st.session_state.get("provider"))
    return result or "⚠️ No response. Check your provider/API key in the sidebar."


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/sun--v1.png", width=60)
    st.title("Daily AI Assistant")
    st.caption("v2.0 · Personalised · Private")
    st.divider()

    # Provider
    st.subheader("🤖 LLM Provider")
    provider = st.selectbox(
        "Choose provider",
        ["ollama", "groq", "openai", "anthropic", "cohere"],
        index=0,
        help="Ollama = free local model. Others need an API key."
    )
    st.session_state["provider"] = provider

    if provider == "ollama":
        ollama_model = st.text_input("Ollama model", value="llama3.2",
                                     help="Make sure Ollama is running: ollama serve")
        os.environ["OLLAMA_DEFAULT_MODEL"] = ollama_model
        st.info("💡 Ollama is free & runs locally. Install: https://ollama.ai")
    else:
        st.subheader("🔑 API Key")
        api_key = st.text_input(f"{provider.capitalize()} API Key",
                                type="password",
                                placeholder="Paste your key here")
        if api_key:
            st.session_state.setdefault("api_keys", {})[provider] = api_key
            st.success("✅ Key saved for this session")

        links = {
            "openai":    "https://platform.openai.com/api-keys",
            "anthropic": "https://console.anthropic.com",
            "groq":      "https://console.groq.com",
            "cohere":    "https://dashboard.cohere.com",
        }
        st.caption(f"Get a key → [{provider}]({links.get(provider, '#')})")

    st.divider()

    # User profile
    st.subheader("👤 Your Profile")
    name         = st.text_input("Name",         value="User")
    wake_time    = st.text_input("Wake-up time",  value="07:00")
    fitness      = st.selectbox("Fitness level",  ["low", "moderate", "high"])
    work_focus   = st.text_input("Work focus",    value="general")
    diet_type    = st.selectbox("Diet type",      ["balanced", "vegetarian", "vegan", "keto"])
    city         = st.text_input("City",          value="Vasind")

    prefs = {
        "name": name, "wake_time": wake_time, "fitness_level": fitness,
        "work_focus": work_focus, "city": city,
        "dietary": {"type": diet_type, "restrictions": [], "preferences": []},
        "news_categories": ["technology", "health"],
    }
    st.session_state["prefs"] = prefs
    st.divider()
    st.caption("🔒 API keys are only stored in your browser session.")


# ── Header ────────────────────────────────────────────────────────────────────
col1, col2 = st.columns([3, 1])
with col1:
    st.title("🌅 Daily AI Assistant")
    st.markdown(f"**Good {'morning' if datetime.now().hour < 12 else 'afternoon' if datetime.now().hour < 17 else 'evening'}, {name}!** · {datetime.now().strftime('%A, %d %B %Y')}")
with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    provider_badge = {"ollama": "🟢 Ollama (Local)", "openai": "🔵 OpenAI",
                      "anthropic": "🟣 Anthropic", "groq": "🟡 Groq", "cohere": "🟠 Cohere"}
    st.info(provider_badge.get(provider, provider))

st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tabs = st.tabs([
    "🌅 Morning", "📋 Tasks", "🎯 Habits",
    "📝 Journal", "🍽️ Meals", "🌤️ Weather",
    "📰 News", "⏱️ Focus", "🔔 Reminders", "💡 Quote"
])


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 1 — Morning Routine
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tabs[0]:
    st.header("🌅 Morning Routine")
    st.markdown("Get a personalised morning routine generated by AI based on your profile.")
    col1, col2 = st.columns(2)
    with col1:
        duration = st.slider("Available time (minutes)", 15, 90, 30, 5)
        include_exercise = st.checkbox("Include exercise", value=True)
    with col2:
        include_meditation = st.checkbox("Include meditation", value=True)
        include_meal_prep  = st.checkbox("Include breakfast prep", value=True)

    if st.button("✨ Generate My Morning Routine", type="primary", key="btn_morning"):
        prompt = (
            f"Create a {duration}-minute personalised morning routine for {name} who wakes at {wake_time}.\n"
            f"Fitness level: {fitness}. Work focus: {work_focus}.\n"
            f"Include exercise: {include_exercise}. Include meditation: {include_meditation}. Include breakfast: {include_meal_prep}.\n"
            "Format with clear time blocks (e.g. 07:00–07:05) and a one-line action for each. Be energising."
        )
        result = ask_ai(prompt)
        st.markdown("---")
        st.markdown(result)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 2 — Tasks
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tabs[1]:
    st.header("📋 Task Manager")
    tasks_file = DATA_DIR / "tasks.json"
    tasks_data = load_json(tasks_file, {"tasks": [], "completed": []})

    col1, col2 = st.columns([2, 1])
    with col1:
        new_task = st.text_input("➕ Add a new task", placeholder="e.g. Review project proposal")
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Add Task") and new_task.strip():
            tasks_data["tasks"].append(new_task.strip())
            save_json(tasks_file, tasks_data)
            st.rerun()

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader(f"Active ({len(tasks_data['tasks'])})")
        for i, t in enumerate(tasks_data["tasks"]):
            c1, c2 = st.columns([5, 1])
            with c1: st.markdown(f"○ {t}")
            with c2:
                if st.button("✓", key=f"done_{i}"):
                    tasks_data["completed"].append(tasks_data["tasks"].pop(i))
                    save_json(tasks_file, tasks_data)
                    st.rerun()
    with col_b:
        st.subheader(f"Completed ({len(tasks_data['completed'])})")
        for t in tasks_data["completed"]:
            st.markdown(f"✅ ~~{t}~~")
        if tasks_data["completed"] and st.button("Clear completed"):
            tasks_data["completed"] = []
            save_json(tasks_file, tasks_data)
            st.rerun()

    if tasks_data["tasks"] and st.button("🤖 AI Prioritise My Tasks", type="primary"):
        task_list = "\n- ".join(tasks_data["tasks"])
        prompt = (
            f"Prioritise and add a brief (1-line) tip for each task. Work focus: {work_focus}.\n"
            f"Tasks:\n- {task_list}\n"
            "Return as numbered list, most important first."
        )
        st.markdown("---")
        st.markdown(ask_ai(prompt))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 3 — Habits
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tabs[2]:
    st.header("🎯 Habit Tracker")
    habits_file = DATA_DIR / "habits.json"
    default_habits = {"habits": [
        {"name": "Drink 8 glasses of water", "streak": 0},
        {"name": "Exercise 20 min",           "streak": 0},
        {"name": "Read 10 min",               "streak": 0},
        {"name": "Meditate 5 min",            "streak": 0},
        {"name": "Sleep by 11 PM",            "streak": 0},
    ]}
    habits_data = load_json(habits_file, default_habits)

    st.markdown("Mark habits as done to grow your streak 🔥")
    cols = st.columns(len(habits_data["habits"]))
    for i, (h, col) in enumerate(zip(habits_data["habits"], cols)):
        with col:
            streak = h["streak"]
            emoji  = "🔥" if streak >= 7 else "⚡" if streak >= 3 else "○"
            st.metric(label=h["name"], value=f"{streak} days", delta="streak")
            if st.button(f"{emoji} Done today", key=f"habit_{i}"):
                habits_data["habits"][i]["streak"] += 1
                save_json(habits_file, habits_data)
                st.rerun()

    st.divider()
    new_habit = st.text_input("➕ Add a new habit")
    if st.button("Add Habit") and new_habit.strip():
        habits_data["habits"].append({"name": new_habit.strip(), "streak": 0})
        save_json(habits_file, habits_data)
        st.rerun()

    if st.button("💬 AI Habit Coaching", type="primary"):
        habits_text = ", ".join([f"{h['name']} (streak: {h['streak']})" for h in habits_data["habits"]])
        prompt = (
            f"Analyse these habits for {name}: {habits_text}.\n"
            "Give: 1) What's going well, 2) What to focus on next week, 3) One science-backed tip to improve consistency."
        )
        st.markdown(ask_ai(prompt))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 4 — Journal
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tabs[3]:
    st.header("📝 Daily Journal")
    journal_file = DATA_DIR / f"journal_{date.today()}.json"
    today_entry  = load_json(journal_file, {"entry": "", "mood": "neutral", "date": str(date.today())})

    col1, col2 = st.columns([3, 1])
    with col1:
        entry = st.text_area("What's on your mind today?",
                              value=today_entry.get("entry", ""), height=180,
                              placeholder="Write freely... reflect on your day, goals, feelings.")
    with col2:
        mood = st.selectbox("Mood", ["😊 Great", "😐 Okay", "😔 Low", "😤 Frustrated", "😴 Tired"],
                            index=["😊 Great","😐 Okay","😔 Low","😤 Frustrated","😴 Tired"].index(
                                today_entry.get("mood", "😐 Okay")) if today_entry.get("mood") in ["😊 Great","😐 Okay","😔 Low","😤 Frustrated","😴 Tired"] else 1)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("💾 Save Entry"):
            save_json(journal_file, {"entry": entry, "mood": mood, "date": str(date.today())})
            st.success("Saved!")

    if entry and st.button("🤖 Get AI Reflection", type="primary"):
        prompt = (
            f"{name}'s journal entry today (mood: {mood}):\n\"{entry}\"\n\n"
            "Respond as a warm, thoughtful coach. Give: 1) What you notice, 2) A reframe or insight, 3) One small action for tomorrow."
        )
        st.markdown("---")
        st.markdown(ask_ai(prompt))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 5 — Meal Planner
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tabs[4]:
    st.header("🍽️ Meal Planner")
    col1, col2, col3 = st.columns(3)
    with col1:
        calories = st.slider("Daily calorie goal", 1200, 3500, 2000, 100)
    with col2:
        meal_count = st.selectbox("Meals per day", [3, 4, 5], index=0)
    with col3:
        cuisine = st.text_input("Preferred cuisine", value="Indian")

    restrictions = st.multiselect("Restrictions / allergies",
        ["Gluten-free", "Dairy-free", "Nut-free", "Low-carb", "High-protein", "Low-sodium"])

    if st.button("🍳 Generate My Meal Plan", type="primary"):
        prompt = (
            f"Create a {meal_count}-meal plan for {name}.\n"
            f"Diet: {diet_type}. Cuisine: {cuisine}. Calorie goal: {calories} kcal/day.\n"
            f"Restrictions: {restrictions or 'none'}. Fitness: {fitness}.\n"
            "Include meal name, ingredients (short list), estimated calories, and prep time. Format cleanly."
        )
        st.markdown("---")
        st.markdown(ask_ai(prompt))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 6 — Weather
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tabs[5]:
    st.header("🌤️ Weather & Activity Suggestions")

    weather_key = st.text_input("OpenWeatherMap API Key (optional — free at openweathermap.org)",
                                type="password", placeholder="Leave blank for AI-only suggestions")

    weather_info = None
    if weather_key and city:
        try:
            import requests as req
            r = req.get("https://api.openweathermap.org/data/2.5/weather",
                        params={"q": f"{city},IN", "appid": weather_key, "units": "metric"}, timeout=5)
            if r.ok:
                d = r.json()
                weather_info = {
                    "temp": round(d["main"]["temp"]),
                    "feels_like": round(d["main"]["feels_like"]),
                    "humidity": d["main"]["humidity"],
                    "description": d["weather"][0]["description"].capitalize(),
                    "wind": d["wind"]["speed"],
                }
        except Exception:
            pass

    if weather_info:
        w = weather_info
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🌡️ Temp",        f"{w['temp']}°C")
        c2.metric("🤔 Feels Like",  f"{w['feels_like']}°C")
        c3.metric("💧 Humidity",    f"{w['humidity']}%")
        c4.metric("💨 Wind",        f"{w['wind']} m/s")
        st.info(f"**{w['description']}** in {city}")
        context = f"Current weather in {city}: {w['description']}, {w['temp']}°C, humidity {w['humidity']}%."
    else:
        st.info(f"📍 Location: {city}, Maharashtra, India")
        context = f"Location: {city}, Maharashtra, India. Typical June weather (monsoon season)."

    if st.button("🌈 Get Activity Suggestions", type="primary"):
        prompt = (
            f"{context}\n"
            f"Suggest 4 activities for {name} (fitness: {fitness}).\n"
            "Include 2 outdoor, 2 indoor. For each: activity name, duration, why it suits the weather, what to wear/bring."
        )
        st.markdown("---")
        st.markdown(ask_ai(prompt))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 7 — News
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tabs[6]:
    st.header("📰 News Briefing")
    interests = st.multiselect(
        "Topics you care about",
        ["Technology", "AI & ML", "Health", "Science", "Business", "Sports", "Politics", "Environment"],
        default=["Technology", "AI & ML", "Health"]
    )
    briefing_style = st.radio("Briefing style", ["Short bullets", "Detailed summary", "ELI5 (simple)"], horizontal=True)

    if st.button("📡 Generate News Briefing", type="primary"):
        style_map = {
            "Short bullets": "3-5 short bullet points",
            "Detailed summary": "a detailed 2-paragraph summary",
            "ELI5 (simple)": "a simple explanation like I'm 12 years old",
        }
        prompt = (
            f"Give {name} {style_map[briefing_style]} of the most important news today in: {', '.join(interests)}.\n"
            "Focus on what's most impactful and actionable. Be factual and concise."
        )
        st.markdown("---")
        st.markdown(ask_ai(prompt))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 8 — Focus Timer
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tabs[7]:
    st.header("⏱️ Focus Planner (Pomodoro)")
    col1, col2, col3 = st.columns(3)
    with col1:
        focus_mins   = st.slider("Focus block (min)", 15, 60, 25, 5)
    with col2:
        short_break  = st.slider("Short break (min)", 3, 15, 5, 1)
    with col3:
        num_blocks   = st.slider("Number of blocks",  2, 8, 4)

    main_goal = st.text_input("What's your main goal today?", placeholder="e.g. Complete the API integration")

    if st.button("🎯 Build My Focus Schedule", type="primary"):
        prompt = (
            f"Create a Pomodoro focus schedule for {name} (work: {work_focus}).\n"
            f"Main goal: {main_goal or 'general productivity'}.\n"
            f"{num_blocks} focus blocks of {focus_mins} min each, {short_break}-min short breaks, 1 long break after block 4.\n"
            "For each block: suggest a specific sub-task, an energy tip, and what to avoid. Format as a clear timetable."
        )
        st.markdown("---")
        st.markdown(ask_ai(prompt))

    st.divider()
    st.markdown("### ⏱️ Quick Timer")
    timer_mins = st.number_input("Set timer (minutes)", min_value=1, max_value=120, value=25)
    st.markdown(
        f"<meta http-equiv=\"refresh\" content=\"\">" +
        f"""<div style='background:#1e2130;border-radius:12px;padding:20px;text-align:center'>
        <h2 style='color:#7c6af7'>⏱️ {timer_mins}:00</h2>
        <p style='color:#aaa'>Start a {timer_mins}-min focus session. Close distractions, put on music, begin!</p>
        </div>""",
        unsafe_allow_html=True
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 9 — Reminders
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tabs[8]:
    st.header("🔔 Reminders")
    reminders_file = DATA_DIR / "reminders.json"
    default_reminders = [
        {"time": "07:30", "message": "Drink a glass of water 💧",        "date": "daily"},
        {"time": "09:00", "message": "Check your task list 📋",           "date": "daily"},
        {"time": "13:00", "message": "Lunch break 🍽️",                  "date": "daily"},
        {"time": "17:00", "message": "Evening walk or stretch 🚶",       "date": "daily"},
        {"time": "22:00", "message": "Wind down — no screens 😴",        "date": "daily"},
    ]
    reminders = load_json(reminders_file, default_reminders)

    st.markdown("### Today's Reminders")
    for i, r in enumerate(reminders):
        col1, col2, col3 = st.columns([1, 4, 1])
        with col1: st.markdown(f"**⏰ {r['time']}**")
        with col2: st.markdown(r['message'])
        with col3:
            if st.button("🗑️", key=f"del_reminder_{i}"):
                reminders.pop(i)
                save_json(reminders_file, reminders)
                st.rerun()

    st.divider()
    st.markdown("### ➕ Add Reminder")
    c1, c2, c3 = st.columns([1, 3, 1])
    with c1:
        r_time = st.text_input("Time", value="08:00", placeholder="HH:MM")
    with c2:
        r_msg  = st.text_input("Message", placeholder="e.g. Take medicine")
    with c3:
        r_date = st.text_input("Date", value="daily", placeholder="daily or YYYY-MM-DD")

    if st.button("Add Reminder") and r_msg.strip():
        reminders.append({"time": r_time, "message": r_msg, "date": r_date})
        save_json(reminders_file, reminders)
        st.success(f"✅ Added: [{r_time}] {r_msg}")
        st.rerun()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 10 — Quote
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tabs[9]:
    st.header("💡 Quote & Motivation")
    quote_type = st.radio(
        "I want something...",
        ["Motivational", "Philosophical", "Funny & Uplifting", "Stoic", "Career-focused"],
        horizontal=True
    )
    if st.button("✨ Give Me Today's Quote", type="primary"):
        prompt = (
            f"Give {name} a {quote_type.lower()} quote for today.\n"
            f"Context: {name} focuses on {work_focus}.\n"
            "Format: Quote in quotes, then author, then a 2-sentence personalised reflection connecting it to their work."
        )
        result = ask_ai(prompt)
        st.markdown("---")
        st.markdown(f"### 💬 {result}")

    st.divider()
    st.markdown("### 🧠 Ask AI Anything")
    free_q = st.text_area("Ask your daily assistant anything...",
                           placeholder="e.g. How can I improve my productivity? What should I focus on this week?")
    if st.button("🤖 Ask", type="primary") and free_q.strip():
        prompt = f"You are {name}'s personal AI assistant. Answer this thoughtfully:\n{free_q}"
        st.markdown("---")
        st.markdown(ask_ai(prompt))


# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.markdown(
    "<center><small>🌅 Daily AI Assistant v2.0 &nbsp;·&nbsp; "
    "<a href='https://github.com/Samuel-025/daily_ai_assistant'>GitHub</a> &nbsp;·&nbsp; "
    "Built with Streamlit + Ollama/OpenAI/Groq/Anthropic/Cohere</small></center>",
    unsafe_allow_html=True
)
