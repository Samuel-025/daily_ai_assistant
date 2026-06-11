#!/usr/bin/env python3
"""
Daily AI Assistant - Streamlit Demo App v2.1
Fixes: mood selectbox crash, meta-refresh tag, task delete, habit reset,
       journal history, JS countdown timer, habit progress bars,
       weather country selector, AI chat history, About tab.
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
  .block-container { padding-top: 1.2rem; }
  .stTabs [data-baseweb="tab"] { font-size: 14px; font-weight: 600; }
  .feature-card {
    background: linear-gradient(135deg, #1e2130, #252840);
    border-radius: 12px; padding: 18px 20px; margin-bottom: 10px;
    border-left: 4px solid #7c6af7;
  }
  .chat-user   { background:#1e2130; border-radius:10px; padding:10px 14px; margin:6px 0; }
  .chat-ai     { background:#252840; border-radius:10px; padding:10px 14px; margin:6px 0; border-left:3px solid #7c6af7; }
  .timer-box   { background:#1e2130; border-radius:14px; padding:28px; text-align:center; }
  .timer-digit { font-size:64px; font-weight:800; color:#7c6af7; letter-spacing:4px; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────
DATA_DIR = Path("demo_data")
DATA_DIR.mkdir(exist_ok=True)

MOODS = ["😊 Great", "😐 Okay", "😔 Low", "😤 Frustrated", "😴 Tired"]

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

def ask_ai(prompt: str) -> str:
    """Route prompt to the configured LLM provider."""
    provider = st.session_state.get("provider", "ollama")
    api_keys  = st.session_state.get("api_keys", {})
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent))
        from config.settings import Settings
        from models.llm_manager import LLMManager
        s = Settings()
        for p, k in api_keys.items():
            if k:
                try: s.set_api_key(p, k)
                except Exception: pass
        s.default_provider  = provider
        s.use_local_first   = (provider == "ollama")
        llm = LLMManager(s)
        with st.spinner("🤖 Thinking..."):
            result = llm.generate(prompt, provider=provider)
        return result or "⚠️ No response received. Check your provider/API key."
    except Exception as e:
        return (
            f"⚠️ **LLM not available** — `{e}`\n\n"
            "**To use AI features:**\n"
            "- Select a provider in the sidebar\n"
            "- For **Ollama**: run `ollama serve` locally\n"
            "- For **Groq/OpenAI/etc**: paste your API key in the sidebar"
        )

def add_chat(role: str, msg: str):
    st.session_state.setdefault("chat_history", []).append({"role": role, "msg": msg})


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/sun--v1.png", width=56)
    st.title("Daily AI Assistant")
    st.caption("v2.1 · Personalised · Private")
    st.divider()

    # Provider
    st.subheader("🤖 LLM Provider")
    provider = st.selectbox(
        "Choose provider",
        ["ollama", "groq", "openai", "anthropic", "cohere"],
        index=0,
        help="Ollama = free & local. Others need an API key."
    )
    st.session_state["provider"] = provider

    if provider == "ollama":
        ollama_model = st.text_input("Ollama model", value="llama3.2",
                                     help="Run: ollama serve")
        os.environ["OLLAMA_DEFAULT_MODEL"] = ollama_model
        st.info("💡 Free & offline. [Install Ollama](https://ollama.ai)")
    else:
        api_key = st.text_input(f"{provider.capitalize()} API Key",
                                type="password", placeholder="Paste your key here")
        if api_key:
            st.session_state.setdefault("api_keys", {})[provider] = api_key
            st.success("✅ Key saved for this session")
        links = {
            "openai":    "https://platform.openai.com/api-keys",
            "anthropic": "https://console.anthropic.com",
            "groq":      "https://console.groq.com",
            "cohere":    "https://dashboard.cohere.com",
        }
        st.caption(f"Get a free key → [{provider}]({links.get(provider, '#')})")

    st.divider()

    # User profile
    st.subheader("👤 Your Profile")
    name       = st.text_input("Name",        value=st.session_state.get("name", "User"))
    wake_time  = st.text_input("Wake-up time", value=st.session_state.get("wake_time", "07:00"))
    fitness    = st.selectbox("Fitness level", ["low", "moderate", "high"],
                               index=["low","moderate","high"].index(st.session_state.get("fitness","moderate")))
    work_focus = st.text_input("Work focus",   value=st.session_state.get("work_focus", "general"))
    diet_type  = st.selectbox("Diet type",     ["balanced", "vegetarian", "vegan", "keto"],
                               index=["balanced","vegetarian","vegan","keto"].index(st.session_state.get("diet_type","balanced")))
    city       = st.text_input("City",         value=st.session_state.get("city", "Vasind"))
    country    = st.text_input("Country code", value=st.session_state.get("country", "IN"),
                               help="2-letter ISO code, e.g. IN, US, GB")

    if st.button("💾 Save Profile"):
        for k, v in [("name",name),("wake_time",wake_time),("fitness",fitness),
                     ("work_focus",work_focus),("diet_type",diet_type),("city",city),("country",country)]:
            st.session_state[k] = v
        save_json(DATA_DIR / "profile.json",
                  {"name":name,"wake_time":wake_time,"fitness":fitness,
                   "work_focus":work_focus,"diet_type":diet_type,"city":city,"country":country})
        st.success("Profile saved! ✅")

    # Load saved profile on first run
    profile_file = DATA_DIR / "profile.json"
    if profile_file.exists() and "name" not in st.session_state:
        p = load_json(profile_file, {})
        for k in ["name","wake_time","fitness","work_focus","diet_type","city","country"]:
            if k in p: st.session_state[k] = p[k]

    st.divider()
    st.caption("🔒 API keys stored in browser session only.")


# ── Header ────────────────────────────────────────────────────────────────────
hour = datetime.now().hour
greeting = "morning" if hour < 12 else "afternoon" if hour < 17 else "evening"
col1, col2 = st.columns([3, 1])
with col1:
    st.title("🌅 Daily AI Assistant")
    st.markdown(f"**Good {greeting}, {name}!** · {datetime.now().strftime('%A, %d %B %Y')}")
with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    badge = {"ollama":"🟢 Ollama (Local)","openai":"🔵 OpenAI",
             "anthropic":"🟣 Anthropic","groq":"🟡 Groq","cohere":"🟠 Cohere"}
    st.info(badge.get(provider, provider))

st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tabs = st.tabs([
    "🌅 Morning", "📋 Tasks", "🎯 Habits",
    "📝 Journal", "🍽️ Meals", "🌤️ Weather",
    "📰 News", "⏱️ Focus", "🔔 Reminders",
    "💡 Quote", "💬 AI Chat", "ℹ️ About"
])


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 1 — Morning Routine
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tabs[0]:
    st.header("🌅 Morning Routine")
    st.markdown("Get a personalised AI-generated morning routine based on your profile.")
    col1, col2 = st.columns(2)
    with col1:
        duration         = st.slider("Available time (min)", 15, 90, 30, 5)
        include_exercise = st.checkbox("Include exercise", value=True)
    with col2:
        include_meditation = st.checkbox("Include meditation", value=True)
        include_meal_prep  = st.checkbox("Include breakfast prep", value=True)

    if st.button("✨ Generate My Morning Routine", type="primary", key="btn_morning"):
        prompt = (
            f"Create a {duration}-minute personalised morning routine for {name} who wakes at {wake_time}.\n"
            f"Fitness level: {fitness}. Work focus: {work_focus}.\n"
            f"Include exercise: {include_exercise}. Meditation: {include_meditation}. Breakfast prep: {include_meal_prep}.\n"
            "Format with time blocks (e.g. 07:00–07:10) and one clear action each. Be energising and specific."
        )
        result = ask_ai(prompt)
        st.session_state["morning_result"] = result

    if "morning_result" in st.session_state:
        st.markdown("---")
        st.markdown(st.session_state["morning_result"])


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 2 — Tasks  (FIX: added delete button per task)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tabs[1]:
    st.header("📋 Task Manager")
    tasks_file = DATA_DIR / "tasks.json"
    tasks_data = load_json(tasks_file, {"tasks": [], "completed": []})

    col1, col2 = st.columns([3, 1])
    with col1:
        new_task = st.text_input("➕ New task", placeholder="e.g. Review project proposal")
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Add Task", key="add_task") and new_task.strip():
            tasks_data["tasks"].append(new_task.strip())
            save_json(tasks_file, tasks_data)
            st.rerun()

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader(f"⏳ Active ({len(tasks_data['tasks'])})")
        to_complete, to_delete = None, None
        for i, t in enumerate(tasks_data["tasks"]):
            c1, c2, c3 = st.columns([5, 1, 1])
            with c1: st.markdown(f"○ {t}")
            with c2:
                if st.button("✓",  key=f"done_{i}"): to_complete = i
            with c3:
                if st.button("🗑️", key=f"del_task_{i}"): to_delete = i
        if to_complete is not None:
            tasks_data["completed"].append(tasks_data["tasks"].pop(to_complete))
            save_json(tasks_file, tasks_data); st.rerun()
        if to_delete is not None:
            tasks_data["tasks"].pop(to_delete)
            save_json(tasks_file, tasks_data); st.rerun()

    with col_b:
        st.subheader(f"✅ Done ({len(tasks_data['completed'])})")
        for t in tasks_data["completed"]:
            st.markdown(f"✅ ~~{t}~~")
        if tasks_data["completed"] and st.button("🧹 Clear completed"):
            tasks_data["completed"] = []
            save_json(tasks_file, tasks_data); st.rerun()

    st.divider()
    if tasks_data["tasks"] and st.button("🤖 AI Prioritise My Tasks", type="primary"):
        task_list = "\n- ".join(tasks_data["tasks"])
        prompt = (
            f"Prioritise these tasks for {name} (work: {work_focus}).\n"
            f"Tasks:\n- {task_list}\n"
            "Return as numbered list (most → least important). Add a 1-line actionable tip per task."
        )
        st.session_state["task_ai"] = ask_ai(prompt)
    if "task_ai" in st.session_state:
        st.markdown(st.session_state["task_ai"])


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 3 — Habits  (FIX: added reset button + progress bars)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tabs[2]:
    st.header("🎯 Habit Tracker")
    habits_file = DATA_DIR / "habits.json"
    default_habits = {"habits": [
        {"name": "Drink 8 glasses of water", "streak": 0, "target": 30},
        {"name": "Exercise 20 min",           "streak": 0, "target": 30},
        {"name": "Read 10 min",               "streak": 0, "target": 21},
        {"name": "Meditate 5 min",            "streak": 0, "target": 21},
        {"name": "Sleep by 11 PM",            "streak": 0, "target": 30},
    ]}
    habits_data = load_json(habits_file, default_habits)

    st.markdown("Mark habits done daily to grow your streak 🔥")

    do_increment, do_reset = None, None
    for i, h in enumerate(habits_data["habits"]):
        streak = h.get("streak", 0)
        target = h.get("target", 30)
        pct    = min(streak / target, 1.0)
        emoji  = "🔥" if streak >= 7 else "⚡" if streak >= 3 else "○"
        with st.container():
            c1, c2, c3, c4 = st.columns([4, 1, 1, 1])
            with c1:
                st.markdown(f"**{h['name']}** — {streak}/{target} days")
                st.progress(pct)
            with c2:
                st.metric("", f"{streak}🔥")
            with c3:
                if st.button(f"{emoji} Done", key=f"habit_done_{i}"): do_increment = i
            with c4:
                if st.button("↺", key=f"habit_reset_{i}", help="Reset streak"): do_reset = i

    if do_increment is not None:
        habits_data["habits"][do_increment]["streak"] += 1
        save_json(habits_file, habits_data); st.rerun()
    if do_reset is not None:
        habits_data["habits"][do_reset]["streak"] = 0
        save_json(habits_file, habits_data); st.rerun()

    st.divider()
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        new_habit = st.text_input("➕ New habit name")
    with col2:
        habit_target = st.number_input("Target days", min_value=7, max_value=365, value=30)
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Add Habit") and new_habit.strip():
            habits_data["habits"].append({"name": new_habit.strip(), "streak": 0, "target": habit_target})
            save_json(habits_file, habits_data); st.rerun()

    if st.button("💬 AI Habit Coach", type="primary"):
        habits_text = ", ".join([f"{h['name']} ({h['streak']}/{h.get('target',30)} days)" for h in habits_data["habits"]])
        prompt = (
            f"Analyse {name}'s habits: {habits_text}.\n"
            "Give: 1) What's going well, 2) Which habit needs most attention & why, 3) One science-backed consistency tip."
        )
        st.session_state["habit_ai"] = ask_ai(prompt)
    if "habit_ai" in st.session_state:
        st.info(st.session_state["habit_ai"])


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 4 — Journal  (FIX: mood index crash fixed + history viewer added)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tabs[3]:
    st.header("📝 Daily Journal")

    journal_tab1, journal_tab2 = st.tabs(["✍️ Today", "📚 History"])

    with journal_tab1:
        journal_file = DATA_DIR / f"journal_{date.today()}.json"
        today_entry  = load_json(journal_file, {"entry": "", "mood": MOODS[1], "date": str(date.today())})

        saved_mood = today_entry.get("mood", MOODS[1])
        mood_index = MOODS.index(saved_mood) if saved_mood in MOODS else 1  # FIX: safe index lookup

        col1, col2 = st.columns([3, 1])
        with col1:
            entry = st.text_area("What's on your mind today?",
                                  value=today_entry.get("entry", ""), height=180,
                                  placeholder="Write freely... reflect on your day, goals, feelings.")
        with col2:
            mood = st.selectbox("Mood", MOODS, index=mood_index)  # FIX: uses safe index
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("💾 Save Entry"):
                save_json(journal_file, {"entry": entry, "mood": mood, "date": str(date.today())})
                st.success("Journal saved! ✅")

        if entry and st.button("🤖 Get AI Reflection", type="primary"):
            prompt = (
                f"{name}'s journal (mood: {mood}):\n\"{entry}\"\n\n"
                "As a warm coach: 1) What you notice, 2) A helpful reframe/insight, 3) One small action for tomorrow."
            )
            st.session_state["journal_ai"] = ask_ai(prompt)
        if "journal_ai" in st.session_state:
            st.markdown("---")
            st.markdown(st.session_state["journal_ai"])

    with journal_tab2:
        st.subheader("📚 Past Journal Entries")
        entries = sorted(DATA_DIR.glob("journal_*.json"), reverse=True)
        if not entries:
            st.info("No past entries yet. Start writing today!")
        else:
            for jf in entries[:10]:  # show last 10
                data = load_json(jf, {})
                label = f"{data.get('date','?')} — {data.get('mood','')}"
                with st.expander(label):
                    st.markdown(data.get("entry", "*(empty)*"))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 5 — Meal Planner
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tabs[4]:
    st.header("🍽️ Meal Planner")
    col1, col2, col3 = st.columns(3)
    with col1:
        calories   = st.slider("Daily calorie goal", 1200, 3500, 2000, 100)
    with col2:
        meal_count = st.selectbox("Meals per day", [3, 4, 5], index=0)
    with col3:
        cuisine    = st.text_input("Preferred cuisine", value="Indian")

    restrictions = st.multiselect("Restrictions / allergies",
        ["Gluten-free", "Dairy-free", "Nut-free", "Low-carb", "High-protein", "Low-sodium"])

    if st.button("🍳 Generate My Meal Plan", type="primary"):
        prompt = (
            f"Create a {meal_count}-meal plan for {name}.\n"
            f"Diet: {diet_type}. Cuisine: {cuisine}. Calories: {calories} kcal/day.\n"
            f"Restrictions: {restrictions or 'none'}. Fitness: {fitness}.\n"
            "For each meal: name, short ingredient list, estimated kcal, prep time. Format as a clean table."
        )
        st.session_state["meal_plan"] = ask_ai(prompt)
    if "meal_plan" in st.session_state:
        st.markdown("---")
        st.markdown(st.session_state["meal_plan"])


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 6 — Weather  (FIX: country code from sidebar, better error msg)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tabs[5]:
    st.header("🌤️ Weather & Activity Suggestions")

    weather_key = st.text_input(
        "OpenWeatherMap API Key (optional — free at openweathermap.org)",
        type="password", placeholder="Leave blank to use AI-only suggestions",
        key="owm_key"
    )

    weather_info = None
    if weather_key and city:
        try:
            import requests as req
            r = req.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={"q": f"{city},{country}", "appid": weather_key, "units": "metric"},
                timeout=6
            )
            if r.ok:
                d = r.json()
                weather_info = {
                    "temp":        round(d["main"]["temp"]),
                    "feels_like":  round(d["main"]["feels_like"]),
                    "humidity":    d["main"]["humidity"],
                    "description": d["weather"][0]["description"].capitalize(),
                    "wind":        d["wind"]["speed"],
                    "icon":        d["weather"][0]["icon"],
                }
            else:
                st.warning(f"⚠️ Weather API error {r.status_code}: {r.json().get('message','unknown')}")
        except Exception as e:
            st.warning(f"⚠️ Could not fetch weather: {e}")

    if weather_info:
        w = weather_info
        icon_url = f"https://openweathermap.org/img/wn/{w['icon']}@2x.png"
        c0, c1, c2, c3, c4 = st.columns([1,2,2,2,2])
        c0.image(icon_url, width=60)
        c1.metric("🌡️ Temp",       f"{w['temp']}°C")
        c2.metric("🤔 Feels Like", f"{w['feels_like']}°C")
        c3.metric("💧 Humidity",   f"{w['humidity']}%")
        c4.metric("💨 Wind",       f"{w['wind']} m/s")
        st.info(f"**{w['description']}** · {city}, {country}")
        context = f"Current weather in {city}: {w['description']}, {w['temp']}°C, humidity {w['humidity']}%, wind {w['wind']} m/s."
    else:
        st.info(f"📍 {city}, {country} — No live weather data (add API key above).")
        context = f"Location: {city}, {country}. Season: June (likely monsoon/summer). No real-time data available."

    if st.button("🌈 Get Activity Suggestions", type="primary"):
        prompt = (
            f"{context}\n"
            f"Suggest 4 activities for {name} (fitness: {fitness}).\n"
            "Include 2 outdoor and 2 indoor. For each: name, duration, why it suits the weather, what to bring."
        )
        st.session_state["weather_ai"] = ask_ai(prompt)
    if "weather_ai" in st.session_state:
        st.markdown("---")
        st.markdown(st.session_state["weather_ai"])


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
    briefing_style = st.radio("Briefing style",
        ["Short bullets", "Detailed summary", "ELI5 (simple)"], horizontal=True)

    if st.button("📡 Generate News Briefing", type="primary"):
        style_map = {
            "Short bullets":    "3-5 short bullet points",
            "Detailed summary": "a detailed 2-paragraph summary",
            "ELI5 (simple)":    "a simple explanation as if I'm 12 years old",
        }
        prompt = (
            f"Give {name} {style_map[briefing_style]} of the most important news today in: {', '.join(interests)}.\n"
            f"Today's date: {date.today()}.\n"
            "Be factual, concise, and actionable."
        )
        st.session_state["news_ai"] = ask_ai(prompt)
    if "news_ai" in st.session_state:
        st.markdown("---")
        st.markdown(st.session_state["news_ai"])


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 8 — Focus Timer  (FIX: real JS countdown + schedule persists)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tabs[7]:
    st.header("⏱️ Focus Planner (Pomodoro)")
    col1, col2, col3 = st.columns(3)
    with col1: focus_mins  = st.slider("Focus block (min)", 15, 60, 25, 5)
    with col2: short_break = st.slider("Short break (min)", 3, 15, 5, 1)
    with col3: num_blocks  = st.slider("Number of blocks", 2, 8, 4)

    main_goal = st.text_input("Main goal today?", placeholder="e.g. Complete API integration")

    if st.button("🎯 Build My Focus Schedule", type="primary"):
        prompt = (
            f"Create a Pomodoro focus schedule for {name} (work: {work_focus}).\n"
            f"Goal: {main_goal or 'general productivity'}.\n"
            f"{num_blocks} focus blocks of {focus_mins} min, {short_break}-min short breaks, 1 long break (15 min) after block 4.\n"
            "For each block: a specific sub-task, one energy tip, one thing to avoid. Format as a clean timetable."
        )
        st.session_state["focus_ai"] = ask_ai(prompt)
    if "focus_ai" in st.session_state:
        st.markdown("---")
        st.markdown(st.session_state["focus_ai"])

    st.divider()
    st.markdown("### ⏱️ Live Countdown Timer")
    timer_mins = st.number_input("Set timer (minutes)", min_value=1, max_value=120, value=focus_mins)
    timer_secs = timer_mins * 60

    # FIX: proper JS countdown (replaces broken <meta refresh> tag)
    st.markdown(f"""
    <div class="timer-box">
      <div class="timer-digit" id="timer-display">{timer_mins:02d}:00</div>
      <p style="color:#aaa;margin-top:8px">Click <b>Start</b> to begin your {timer_mins}-min focus session</p>
      <button onclick="startTimer({timer_secs})"
        style="background:#7c6af7;color:#fff;border:none;padding:10px 28px;
               border-radius:8px;font-size:16px;cursor:pointer;margin:6px">▶ Start</button>
      <button onclick="resetTimer({timer_secs})"
        style="background:#374151;color:#fff;border:none;padding:10px 22px;
               border-radius:8px;font-size:16px;cursor:pointer;margin:6px">↺ Reset</button>
    </div>
    <script>
      var _t = null;
      function startTimer(s){{
        if(_t) return;
        var rem = s;
        _t = setInterval(function(){{
          if(rem<=0){{clearInterval(_t);_t=null;
            document.getElementById('timer-display').innerText='✅ Done!';
            document.getElementById('timer-display').style.color='#4ade80';
            return;}}
          rem--;
          var m=Math.floor(rem/60), sec=rem%60;
          document.getElementById('timer-display').innerText=
            (m<10?'0':'')+m+':'+(sec<10?'0':'')+sec;
        }},1000);
      }}
      function resetTimer(s){{
        clearInterval(_t);_t=null;
        var m=Math.floor(s/60);
        document.getElementById('timer-display').innerText=(m<10?'0':'')+m+':00';
        document.getElementById('timer-display').style.color='#7c6af7';
      }}
    </script>
    """, unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 9 — Reminders
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tabs[8]:
    st.header("🔔 Reminders")
    reminders_file = DATA_DIR / "reminders.json"
    default_reminders = [
        {"time": "07:30", "message": "Drink a glass of water 💧",   "date": "daily"},
        {"time": "09:00", "message": "Check your task list 📋",      "date": "daily"},
        {"time": "13:00", "message": "Lunch break 🍽️",             "date": "daily"},
        {"time": "17:00", "message": "Evening walk or stretch 🚶",  "date": "daily"},
        {"time": "22:00", "message": "Wind down — no screens 😴",   "date": "daily"},
    ]
    reminders = load_json(reminders_file, default_reminders)

    # Highlight upcoming reminder
    now_str = datetime.now().strftime("%H:%M")
    st.markdown("### 📅 Your Reminders")
    del_idx = None
    for i, r in enumerate(reminders):
        is_next = r["time"] >= now_str
        row = st.columns([1, 4, 1, 1])
        with row[0]: st.markdown(f"**⏰ {r['time']}**")
        with row[1]: st.markdown(("🔜 " if is_next else "") + r["message"])
        with row[2]: st.caption(r.get("date", "daily"))
        with row[3]:
            if st.button("🗑️", key=f"del_r_{i}"): del_idx = i
    if del_idx is not None:
        reminders.pop(del_idx)
        save_json(reminders_file, reminders); st.rerun()

    st.divider()
    st.markdown("### ➕ Add Reminder")
    c1, c2, c3, c4 = st.columns([1, 3, 1, 1])
    with c1: r_time = st.text_input("Time (HH:MM)", value="08:00")
    with c2: r_msg  = st.text_input("Message", placeholder="e.g. Take medicine")
    with c3: r_date = st.text_input("Date", value="daily")
    with c4:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("➕ Add") and r_msg.strip():
            reminders.append({"time": r_time, "message": r_msg, "date": r_date})
            reminders.sort(key=lambda x: x["time"])  # keep sorted by time
            save_json(reminders_file, reminders)
            st.success(f"✅ Added [{r_time}] {r_msg}"); st.rerun()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 10 — Quote
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tabs[9]:
    st.header("💡 Quote & Motivation")
    quote_type = st.radio(
        "Style",
        ["Motivational", "Philosophical", "Funny & Uplifting", "Stoic", "Career-focused"],
        horizontal=True
    )
    if st.button("✨ Give Me Today's Quote", type="primary"):
        prompt = (
            f"Give {name} one {quote_type.lower()} quote for today.\n"
            f"Their focus: {work_focus}.\n"
            "Format: \"Quote\" — Author. Then 2 sentences personalising it to their work."
        )
        st.session_state["quote"] = ask_ai(prompt)
    if "quote" in st.session_state:
        st.markdown("---")
        st.markdown(f"### 💬 {st.session_state['quote']}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 11 — AI Chat  (NEW: persistent multi-turn chat)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tabs[10]:
    st.header("💬 AI Chat")
    st.markdown("Ask your personal AI assistant anything. Chat history is kept for this session.")

    chat_history = st.session_state.get("chat_history", [])

    # Render history
    for msg in chat_history:
        if msg["role"] == "user":
            st.markdown(f'<div class="chat-user">🧑 <b>You:</b> {msg["msg"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-ai">🤖 <b>Assistant:</b> {msg["msg"]}</div>', unsafe_allow_html=True)

    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_area("Your message", placeholder="Ask anything...", height=80)
        submitted  = st.form_submit_button("Send 🚀")

    if submitted and user_input.strip():
        add_chat("user", user_input)
        # Build context-aware prompt
        history_text = "\n".join([f"{m['role'].capitalize()}: {m['msg']}" for m in chat_history[-6:]])
        prompt = (
            f"You are {name}'s personal daily assistant (focus: {work_focus}).\n"
            f"Conversation so far:\n{history_text}\n"
            f"User: {user_input}\n"
            "Respond helpfully and concisely."
        )
        response = ask_ai(prompt)
        add_chat("assistant", response)
        st.rerun()

    if chat_history and st.button("🗑️ Clear chat history"):
        st.session_state["chat_history"] = []
        st.rerun()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 12 — About  (NEW)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tabs[11]:
    st.header("ℹ️ About Daily AI Assistant")
    st.markdown("""
    **Daily AI Assistant v2.1** is a fully open-source, privacy-first personal productivity tool.

    ### 🌟 What it does
    - Generates personalised morning routines, meal plans, focus schedules
    - Tracks your habits and journal with AI coaching
    - Fetches real weather data and summarises the news
    - Works 100% offline with [Ollama](https://ollama.ai) or with any cloud LLM

    ### 🔒 Privacy
    - **No data is sent anywhere** unless you use a cloud LLM provider
    - API keys are stored only in your browser session — never on a server
    - All your tasks, habits, and journal entries are stored locally in `demo_data/`

    ### 🤖 Supported LLM Providers
    | Provider | Free? | Notes |
    |---|---|---|
    | Ollama | ✅ Free & local | Best for privacy |
    | Groq | ✅ Free tier | Fast cloud inference |
    | OpenAI | ❌ Paid | GPT-4o etc. |
    | Anthropic | ❌ Paid | Claude models |
    | Cohere | ✅ Free tier | Command-R |

    ### 📦 Install & Run Locally
    ```bash
    git clone https://github.com/Samuel-025/daily_ai_assistant.git
    cd daily_ai_assistant
    pip install -r requirements.txt
    streamlit run streamlit_app.py
    ```

    ### 🔗 Links
    - [GitHub Repository](https://github.com/Samuel-025/daily_ai_assistant)
    - [Live Demo](https://dailyaiassistant-bfszw6tsvquoaav2acjhuo.streamlit.app/)
    - [Report a Bug](https://github.com/Samuel-025/daily_ai_assistant/issues)
    - [Ollama Install Guide](https://ollama.ai)
    """)

    st.divider()
    st.markdown("**Built with ❤️ by [Samuel-025](https://github.com/Samuel-025)**")


# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.markdown(
    "<center><small>🌅 Daily AI Assistant v2.1 &nbsp;·&nbsp; "
    "<a href='https://github.com/Samuel-025/daily_ai_assistant'>GitHub</a> &nbsp;·&nbsp; "
    "<a href='https://dailyaiassistant-bfszw6tsvquoaav2acjhuo.streamlit.app/'>Live Demo</a> &nbsp;·&nbsp; "
    "Built with Streamlit + Ollama / OpenAI / Groq / Anthropic / Cohere"
    "</small></center>",
    unsafe_allow_html=True
)
