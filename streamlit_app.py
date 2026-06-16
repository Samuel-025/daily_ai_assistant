#!/usr/bin/env python3
"""
Daily AI Assistant v3.0  —  ChatGPT-style interactive interface
Features:
  • st.chat_message bubbles + st.chat_input (always-on bottom bar)
  • Full system persona with user profile context
  • Slash commands: /morning /tasks /habits /journal /meal /weather /news /focus /quote /help
  • Suggested quick-prompt chips
  • Multi-turn conversation memory (last 20 messages)
  • Sidebar: provider config, profile, quick-tool buttons, chat stats
  • Tools Panel (expander) for tasks, habits, journal, reminders
"""

import streamlit as st
import json
import os
from pathlib import Path
from datetime import datetime, date
from dotenv import load_dotenv

load_dotenv()

# ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Daily AI Assistant",
    page_icon="🌅",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ────────────────────────────────────────────────────────────
st.markdown("""
<style>
  /* tighter top padding so chat starts higher */
  .block-container { padding-top: 0.6rem !important; padding-bottom: 0rem !important; }

  /* suggestion chip buttons */
  .chip-row { display:flex; flex-wrap:wrap; gap:8px; margin: 8px 0 14px 0; }
  .chip {
    background: #1e2130; border: 1px solid #7c6af7; color: #c4b5fd;
    border-radius: 999px; padding: 5px 14px; font-size: 13px;
    cursor: pointer; white-space: nowrap;
  }
  .chip:hover { background:#2d2a4a; }

  /* slim divider */
  hr { margin: 0.4rem 0 !important; }

  /* sidebar tool buttons full-width */
  .stButton > button { width:100%; }

  /* timer */
  .timer-box   { background:#1e2130; border-radius:14px; padding:22px; text-align:center; }
  .timer-digit { font-size:56px; font-weight:800; color:#7c6af7; letter-spacing:3px; }
</style>
""", unsafe_allow_html=True)


# ── Constants & helpers ───────────────────────────────────────────────
DATA_DIR = Path("demo_data")
DATA_DIR.mkdir(exist_ok=True)
MOODS = ["😊 Great", "😐 Okay", "😔 Low", "😤 Frustrated", "😴 Tired"]

def load_json(path, default):
    if Path(path).exists():
        try: return json.loads(Path(path).read_text())
        except: pass
    Path(path).write_text(json.dumps(default, indent=2))
    return default

def save_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2))

# ── Load / init session profile ─────────────────────────────────────────
def _ss(key, default):
    """Read from session_state, fallback to saved profile, then default."""
    if key in st.session_state:
        return st.session_state[key]
    profile_file = DATA_DIR / "profile.json"
    if profile_file.exists():
        p = load_json(profile_file, {})
        if key in p:
            st.session_state[key] = p[key]
            return p[key]
    return default

DEFAULT_PROFILE = {
    "name": "User", "wake_time": "07:00", "fitness": "moderate",
    "work_focus": "general", "diet_type": "balanced",
    "city": "Vasind", "country": "IN",
}


# ── LLM call ──────────────────────────────────────────────────────────────
def ask_ai(messages: list) -> str:
    """
    messages = [{"role":"system"|"user"|"assistant", "content":"..."}]
    Routes to configured provider via LLMManager.
    """
    provider = st.session_state.get("provider", "ollama")
    api_keys = st.session_state.get("api_keys", {})
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent))
        from config.settings import Settings
        from models.llm_manager import LLMManager
        s = Settings()
        for p, k in api_keys.items():
            if k:
                try: s.set_api_key(p, k)
                except: pass
        s.default_provider = provider
        s.use_local_first  = (provider == "ollama")
        llm = LLMManager(s)
        # Flatten messages to a single prompt for LLMManager compatibility
        flat = "\n".join(
            f"{m['role'].capitalize()}: {m['content']}" for m in messages
        ) + "\nAssistant:"
        result = llm.generate(flat, provider=provider)
        return result or "⚠️ No response. Check your provider/API key in the sidebar."
    except Exception as e:
        return (
            f"⚠️ **LLM unavailable** — `{e}`\n\n"
            "**Quick fix:**\n"
            "- Ollama: run `ollama serve` in a terminal\n"
            "- Groq/OpenAI/etc: paste API key in sidebar"
        )


def build_system_prompt() -> str:
    name       = _ss("name",       DEFAULT_PROFILE["name"])
    wake_time  = _ss("wake_time",  DEFAULT_PROFILE["wake_time"])
    fitness    = _ss("fitness",    DEFAULT_PROFILE["fitness"])
    work_focus = _ss("work_focus", DEFAULT_PROFILE["work_focus"])
    diet_type  = _ss("diet_type",  DEFAULT_PROFILE["diet_type"])
    city       = _ss("city",       DEFAULT_PROFILE["city"])
    country    = _ss("country",    DEFAULT_PROFILE["country"])
    now        = datetime.now().strftime("%A, %d %B %Y · %I:%M %p")

    # Pull live context snippets
    tasks      = load_json(DATA_DIR/"tasks.json",    {"tasks":[],"completed":[]})      ["tasks"]
    habits     = load_json(DATA_DIR/"habits.json",   {"habits":[]})                    ["habits"]
    journal_f  = DATA_DIR / f"journal_{date.today()}.json"
    journal    = load_json(journal_f, {"entry":"","mood":MOODS[1]})

    tasks_str  = ", ".join(tasks[:5]) if tasks else "none"
    habits_str = ", ".join(f"{h['name']}({h.get('streak',0)}d)" for h in habits[:5]) if habits else "none"
    mood_str   = journal.get("mood", "unknown")

    return f"""You are a warm, intelligent personal daily assistant for {name}.
Today is {now}. You know everything about {name}'s profile:
- Wake-up time: {wake_time} | Fitness: {fitness} | Diet: {diet_type}
- Work focus: {work_focus} | City: {city}, {country}
- Active tasks: {tasks_str}
- Habit streaks: {habits_str}
- Today's mood: {mood_str}

Your personality: concise yet warm, practical, motivating — like a brilliant friend who's also a life coach.
Format responses clearly using markdown when helpful (bullets, bold, tables).
If asked about tasks/habits/journal/meals/weather/news/focus, give rich personalised answers.
Never say you can't help. Always give a useful response.

Slash commands the user can type:
/morning — generate morning routine
/tasks   — show & manage tasks
/habits  — habit coaching
/journal — journal reflection prompt
/meal    — meal plan suggestion
/weather — activity suggestions for today
/news    — personalised news briefing
/focus   — Pomodoro schedule
/quote   — motivational quote
/help    — list all commands"""


# ────────────────────────────────────────────────────────────
# SIDEBAR
# ────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🌅 Daily AI Assistant")
    st.caption("v3.0 · ChatGPT-style · Private")
    st.divider()

    # — Provider config
    with st.expander("🤖 LLM Provider", expanded=True):
        provider = st.selectbox(
            "Provider",
            ["ollama", "groq", "openai", "anthropic", "cohere"],
            index=["ollama","groq","openai","anthropic","cohere"].index(
                st.session_state.get("provider", "ollama")
            ),
            label_visibility="collapsed",
        )
        st.session_state["provider"] = provider

        if provider == "ollama":
            mdl = st.text_input("Model", value=os.environ.get("OLLAMA_DEFAULT_MODEL","llama3.2"),
                                help="ollama pull llama3.2")
            os.environ["OLLAMA_DEFAULT_MODEL"] = mdl
            st.info("💡 Local & free. [Install Ollama](https://ollama.ai)\nRun: `ollama serve`")
        else:
            api_key = st.text_input(f"{provider.capitalize()} API Key",
                                    type="password", placeholder="Paste key…")
            if api_key:
                st.session_state.setdefault("api_keys", {})[provider] = api_key
                st.success("✅ Key saved")
            links = {"openai":"https://platform.openai.com/api-keys",
                     "anthropic":"https://console.anthropic.com",
                     "groq":"https://console.groq.com",
                     "cohere":"https://dashboard.cohere.com"}
            st.caption(f"[Get free key → {provider}]({links.get(provider,'#')})")

        # Current model badge
        model_names = {"ollama":os.environ.get("OLLAMA_DEFAULT_MODEL","llama3.2"),
                       "groq":"llama-3.3-70b-versatile","openai":"gpt-4o",
                       "anthropic":"claude-3-5-sonnet","cohere":"command-a-03-2025"}
        st.caption(f"Model: `{model_names.get(provider, provider)}`")

    st.divider()

    # — Profile
    with st.expander("👤 Profile", expanded=False):
        name       = st.text_input("Name",         value=_ss("name",       DEFAULT_PROFILE["name"]))
        wake_time  = st.text_input("Wake-up",       value=_ss("wake_time",  DEFAULT_PROFILE["wake_time"]))
        fitness    = st.selectbox("Fitness",        ["low","moderate","high"],
                                  index=["low","moderate","high"].index(_ss("fitness","moderate")))
        work_focus = st.text_input("Work focus",    value=_ss("work_focus", DEFAULT_PROFILE["work_focus"]))
        diet_type  = st.selectbox("Diet",           ["balanced","vegetarian","vegan","keto"],
                                  index=["balanced","vegetarian","vegan","keto"].index(_ss("diet_type","balanced")))
        city       = st.text_input("City",          value=_ss("city",       DEFAULT_PROFILE["city"]))
        country    = st.text_input("Country (ISO)", value=_ss("country",    DEFAULT_PROFILE["country"]))
        if st.button("💾 Save Profile", use_container_width=True):
            for k,v in [("name",name),("wake_time",wake_time),("fitness",fitness),
                        ("work_focus",work_focus),("diet_type",diet_type),("city",city),("country",country)]:
                st.session_state[k] = v
            save_json(DATA_DIR/"profile.json",
                      {"name":name,"wake_time":wake_time,"fitness":fitness,
                       "work_focus":work_focus,"diet_type":diet_type,"city":city,"country":country})
            st.success("✅ Saved!")
    else:
        # Reflect sidebar values into session_state even if expander closed
        name       = _ss("name",       DEFAULT_PROFILE["name"])
        wake_time  = _ss("wake_time",  DEFAULT_PROFILE["wake_time"])
        fitness    = _ss("fitness",    DEFAULT_PROFILE["fitness"])
        work_focus = _ss("work_focus", DEFAULT_PROFILE["work_focus"])
        diet_type  = _ss("diet_type",  DEFAULT_PROFILE["diet_type"])
        city       = _ss("city",       DEFAULT_PROFILE["city"])
        country    = _ss("country",    DEFAULT_PROFILE["country"])

    st.divider()

    # — Quick-action buttons (trigger chat messages)
    st.markdown("**⚡ Quick Actions**")
    QUICK = [
        ("🌅 Morning routine",  "/morning"),
        ("📋 My tasks",         "/tasks"),
        ("🎯 Habit check-in",   "/habits"),
        ("📝 Journal prompt",   "/journal"),
        ("🍽️ Meal plan",       "/meal"),
        ("🌤️ Activities",     "/weather"),
        ("📰 News briefing",   "/news"),
        ("⏱️ Focus schedule",  "/focus"),
        ("💡 Quote",            "/quote"),
    ]
    for label, cmd in QUICK:
        if st.button(label, key=f"quick_{cmd}", use_container_width=True):
            st.session_state["pending_input"] = cmd
            st.rerun()

    st.divider()

    # — Chat stats
    msgs = st.session_state.get("messages", [])
    user_msgs = sum(1 for m in msgs if m["role"] == "user")
    st.caption(f"💬 {user_msgs} messages this session")
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state["messages"] = []
        st.rerun()
    st.caption("🔒 Keys stored in session only.")


# ────────────────────────────────────────────────────────────
# MAIN CHAT AREA
# ────────────────────────────────────────────────────────────
hour     = datetime.now().hour
greeting = "morning" if hour < 12 else "afternoon" if hour < 17 else "evening"
badge    = {"ollama":"🟢 Local","openai":"🔵 OpenAI",
            "anthropic":"🟣 Anthropic","groq":"🟡 Groq","cohere":"🟠 Cohere"}

col_title, col_badge = st.columns([5, 1])
with col_title:
    st.markdown(f"### 🌅 Good {greeting}, **{name}** · "
                f"{datetime.now().strftime('%a %d %b')}")
with col_badge:
    st.info(badge.get(provider, provider), icon=None)

# ── Slash-command expanders (shown ABOVE chat) ───────────────────────────

SLASH_PROMPTS = {
    "/morning": (
        f"Create a personalised morning routine for {name} who wakes at "
        + _ss("wake_time", "07:00")
        + f". Fitness: {_ss('fitness','moderate')}. Work: {_ss('work_focus','general')}."
        " Include time blocks (e.g. 07:00–07:10), one action each. Be energising."
    ),
    "/tasks": (
        "Show the user's current active tasks, then prioritise them (most → least important)."
        f" Work focus: {_ss('work_focus','general')}. Add a 1-line tip per task."
    ),
    "/habits": (
        "Analyse the user's habit streaks. Give: 1) What's going well,"
        " 2) Which habit to focus on, 3) One science-backed tip."
    ),
    "/journal": (
        f"Give {name} 3 thoughtful journaling prompts for today based on their mood and work focus."
        " Make them reflective and personal."
    ),
    "/meal": (
        f"Create a {_ss('diet_type','balanced')} meal plan for {name} today."
        f" Cuisine: Indian. Fitness: {_ss('fitness','moderate')}."
        " 3 meals + 1 snack. For each: name, key ingredients, kcal, prep time."
    ),
    "/weather": (
        f"Suggest 4 activities for {name} in {_ss('city','Vasind')}, {_ss('country','IN')} today."
        f" Fitness: {_ss('fitness','moderate')}. 2 outdoor, 2 indoor."
        " For each: name, duration, why it suits today, what to bring."
    ),
    "/news": (
        f"Give {name} a concise news briefing for {date.today()} covering: Technology, AI & ML, Health."
        " 3-5 bullet points. Be factual and highlight what matters most."
    ),
    "/focus": (
        f"Create a Pomodoro focus schedule for {name} (work: {_ss('work_focus','general')})."
        " 4 blocks of 25 min, 5-min breaks, 1 long break after block 4."
        " For each block: specific sub-task, energy tip, thing to avoid."
    ),
    "/quote": (
        f"Give {name} one powerful motivational quote for today."
        f" Their focus: {_ss('work_focus','general')}."
        ' Format: \'"Quote" — Author\'. Then personalise it in 2 sentences.'
    ),
    "/help": (
        "List all available slash commands with a short description of what each does."
        " Format as a clean markdown table with columns: Command | What it does."
    ),
}


# ── Initialise message history ────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# ── Suggested chips (shown when chat is empty) ───────────────────────────
if not st.session_state["messages"]:
    st.markdown(
        f"""<div style='text-align:center;padding:32px 0 8px'>
        <span style='font-size:48px'>🌅</span><br>
        <h2 style='margin:8px 0 4px'>How can I help you today, {name}?</h2>
        <p style='color:#888'>Your personal AI assistant — type anything or pick a suggestion below</p>
        </div>""", unsafe_allow_html=True
    )
    CHIPS = [
        ("🌅 Morning routine",     "/morning"),
        ("📋 Prioritise my tasks",  "/tasks"),
        ("🎯 Habit coaching",       "/habits"),
        ("🍽️ Meal plan for today",  "/meal"),
        ("📰 News briefing",        "/news"),
        ("⏱️ Focus schedule",       "/focus"),
        ("📝 Journal prompts",      "/journal"),
        ("💡 Motivate me",          "/quote"),
    ]
    cols = st.columns(4)
    for idx, (label, cmd) in enumerate(CHIPS):
        if cols[idx % 4].button(label, key=f"chip_{cmd}", use_container_width=True):
            st.session_state["pending_input"] = cmd
            st.rerun()

# ── Render existing messages ──────────────────────────────────────────────
for msg in st.session_state["messages"]:
    avatar = "🧑" if msg["role"] == "user" else "🌅"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# ── Handle input (from chat_input OR pending from sidebar/chip) ────────────
user_input = st.chat_input(f"Message {name}'s assistant… (or type /help)")

# Consume any pending_input set by sidebar buttons / chips
if "pending_input" in st.session_state and st.session_state["pending_input"]:
    user_input = st.session_state.pop("pending_input")

if user_input:
    raw = user_input.strip()

    # Display user bubble
    with st.chat_message("user", avatar="🧑"):
        st.markdown(raw)
    st.session_state["messages"].append({"role": "user", "content": raw})

    # Resolve slash command → expanded prompt
    cmd_key = raw.lower().split()[0] if raw.startswith("/") else None
    if cmd_key and cmd_key in SLASH_PROMPTS:
        prompt_content = SLASH_PROMPTS[cmd_key]
    else:
        prompt_content = raw  # plain conversation

    # Build messages list for LLM (system + last 20 turns + current)
    system_msg  = {"role": "system",    "content": build_system_prompt()}
    history     = st.session_state["messages"][:-1]  # all except the one just appended
    recent      = history[-20:] if len(history) > 20 else history
    llm_msgs    = [system_msg] + [
        {"role": m["role"], "content": m["content"]} for m in recent
    ] + [{"role": "user", "content": prompt_content}]

    # Generate & display AI response
    with st.chat_message("assistant", avatar="🌅"):
        with st.spinner(""):
            response = ask_ai(llm_msgs)
        st.markdown(response)

    st.session_state["messages"].append({"role": "assistant", "content": response})


# ────────────────────────────────────────────────────────────
# TOOLS PANEL  (collapsible — tasks, habits, journal, reminders, focus timer)
# ────────────────────────────────────────────────────────────
st.divider()
with st.expander("🛠️ Tools Panel — Tasks · Habits · Journal · Reminders · Focus Timer",
                 expanded=False):

    tool_tabs = st.tabs(["📋 Tasks", "🎯 Habits", "📝 Journal", "🔔 Reminders", "⏱️ Timer"])

    # ━━ TASKS
    with tool_tabs[0]:
        tasks_file = DATA_DIR / "tasks.json"
        td         = load_json(tasks_file, {"tasks":[], "completed":[]})
        c1, c2 = st.columns([3,1])
        with c1: nt = st.text_input("New task", placeholder="Add task…", key="tp_newtask")
        with c2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Add", key="tp_addtask") and nt.strip():
                td["tasks"].append(nt.strip()); save_json(tasks_file, td); st.rerun()

        ca, cb = st.columns(2)
        to_done, to_del = None, None
        with ca:
            st.markdown(f"**⏳ Active ({len(td['tasks'])})**")
            for i, t in enumerate(td["tasks"]):
                r = st.columns([5,1,1])
                with r[0]: st.markdown(f"○ {t}")
                with r[1]:
                    if st.button("✓", key=f"tp_done_{i}"): to_done = i
                with r[2]:
                    if st.button("🗑️", key=f"tp_del_{i}"): to_del = i
        with cb:
            st.markdown(f"**✅ Done ({len(td['completed'])})**")
            for t in td["completed"]: st.markdown(f"✅ ~~{t}~~")
            if td["completed"] and st.button("🧹 Clear", key="tp_clear"):
                td["completed"] = []; save_json(tasks_file, td); st.rerun()
        if to_done is not None:
            td["completed"].append(td["tasks"].pop(to_done)); save_json(tasks_file, td); st.rerun()
        if to_del is not None:
            td["tasks"].pop(to_del); save_json(tasks_file, td); st.rerun()

    # ━━ HABITS
    with tool_tabs[1]:
        habits_file  = DATA_DIR / "habits.json"
        default_h    = {"habits":[
            {"name":"Drink 8 glasses of water","streak":0,"target":30},
            {"name":"Exercise 20 min",          "streak":0,"target":30},
            {"name":"Read 10 min",              "streak":0,"target":21},
            {"name":"Meditate 5 min",           "streak":0,"target":21},
            {"name":"Sleep by 11 PM",           "streak":0,"target":30},
        ]}
        hd           = load_json(habits_file, default_h)
        do_inc, do_rst = None, None
        for i, h in enumerate(hd["habits"]):
            s, t = h.get("streak",0), h.get("target",30)
            row  = st.columns([4,1,1,1])
            with row[0]:
                st.markdown(f"**{h['name']}** — {s}/{t}")
                st.progress(min(s/t,1.0))
            with row[1]: st.metric("",f"{s}🔥")
            with row[2]:
                if st.button("🔥", key=f"h_done_{i}", help="Done today"): do_inc = i
            with row[3]:
                if st.button("↺",  key=f"h_rst_{i}",  help="Reset streak"): do_rst = i
        if do_inc is not None:
            hd["habits"][do_inc]["streak"] += 1; save_json(habits_file, hd); st.rerun()
        if do_rst is not None:
            hd["habits"][do_rst]["streak"]  = 0; save_json(habits_file, hd); st.rerun()
        nh_col1, nh_col2 = st.columns([3,1])
        with nh_col1: nh = st.text_input("New habit", key="tp_newhabit")
        with nh_col2: nt2 = st.number_input("Target", 7, 365, 30, key="tp_target")
        if st.button("Add Habit", key="tp_addhabit") and nh.strip():
            hd["habits"].append({"name":nh.strip(),"streak":0,"target":nt2})
            save_json(habits_file, hd); st.rerun()

    # ━━ JOURNAL
    with tool_tabs[2]:
        jtab1, jtab2 = st.tabs(["✍️ Today", "📚 History"])
        with jtab1:
            jf = DATA_DIR / f"journal_{date.today()}.json"
            je = load_json(jf, {"entry":"","mood":MOODS[1],"date":str(date.today())})
            sm = je.get("mood", MOODS[1])
            mi = MOODS.index(sm) if sm in MOODS else 1
            entry = st.text_area("What's on your mind?", value=je.get("entry",""),
                                  height=140, key="tp_journal")
            mood  = st.selectbox("Mood", MOODS, index=mi, key="tp_mood")
            if st.button("💾 Save", key="tp_savej"):
                save_json(jf, {"entry":entry,"mood":mood,"date":str(date.today())})
                st.success("Saved! ✅")
        with jtab2:
            past = sorted(DATA_DIR.glob("journal_*.json"), reverse=True)
            if not past: st.info("No past entries yet.")
            for pf in past[:10]:
                d2 = load_json(pf, {})
                with st.expander(f"{d2.get('date','?')} — {d2.get('mood','')}"):
                    st.markdown(d2.get("entry","*(empty)*"))

    # ━━ REMINDERS
    with tool_tabs[3]:
        rf      = DATA_DIR / "reminders.json"
        default_r = [
            {"time":"07:30","message":"Drink water 💧","date":"daily"},
            {"time":"09:00","message":"Check tasks 📋","date":"daily"},
            {"time":"13:00","message":"Lunch break 🍽️","date":"daily"},
            {"time":"17:00","message":"Evening stretch 🚶","date":"daily"},
            {"time":"22:00","message":"Wind down 😴","date":"daily"},
        ]
        reminders = load_json(rf, default_r)
        now_str   = datetime.now().strftime("%H:%M")
        del_idx   = None
        for i, r in enumerate(reminders):
            row = st.columns([1,4,1])
            with row[0]: st.markdown(f"**⏰ {r['time']}**")
            with row[1]: st.markdown(("🔜 " if r["time"] >= now_str else "✓ ") + r["message"])
            with row[2]:
                if st.button("🗑️", key=f"tp_delr_{i}"): del_idx = i
        if del_idx is not None:
            reminders.pop(del_idx); save_json(rf, reminders); st.rerun()
        st.markdown("---")
        rc1, rc2, rc3 = st.columns([1,3,1])
        with rc1: rt = st.text_input("Time", value="08:00", key="tp_rtime")
        with rc2: rm = st.text_input("Message", key="tp_rmsg")
        with rc3:
            st.markdown("<br>",unsafe_allow_html=True)
            if st.button("+", key="tp_addr") and rm.strip():
                reminders.append({"time":rt,"message":rm,"date":"daily"})
                reminders.sort(key=lambda x: x["time"])
                save_json(rf, reminders); st.rerun()

    # ━━ FOCUS TIMER
    with tool_tabs[4]:
        tm = st.number_input("Minutes", 1, 120, 25, key="tp_timer")
        ts = tm * 60
        st.markdown(f"""
        <div class="timer-box">
          <div class="timer-digit" id="tp-timer-display">{tm:02d}:00</div>
          <p style="color:#888;margin-top:6px">{tm}-min focus session</p>
          <button onclick="tpStart({ts})"
            style="background:#7c6af7;color:#fff;border:none;padding:9px 24px;
                   border-radius:8px;font-size:15px;cursor:pointer;margin:4px">▶ Start</button>
          <button onclick="tpReset({ts})"
            style="background:#374151;color:#fff;border:none;padding:9px 20px;
                   border-radius:8px;font-size:15px;cursor:pointer;margin:4px">↺ Reset</button>
        </div>
        <script>
          var _tp=null;
          function tpStart(s){{if(_tp)return;var r=s;
            _tp=setInterval(function(){{if(r<=0){{clearInterval(_tp);_tp=null;
              document.getElementById('tp-timer-display').innerText='✅ Done!';
              document.getElementById('tp-timer-display').style.color='#4ade80';return;}}
              r--;var m=Math.floor(r/60),sc=r%60;
              document.getElementById('tp-timer-display').innerText=
                (m<10?'0':'')+m+':'+(sc<10?'0':'')+sc;}},1000);}}
          function tpReset(s){{clearInterval(_tp);_tp=null;
            var m=Math.floor(s/60);
            document.getElementById('tp-timer-display').innerText=(m<10?'0':'')+m+':00';
            document.getElementById('tp-timer-display').style.color='#7c6af7';}}
        </script>
        """, unsafe_allow_html=True)


# ── Footer ────────────────────────────────────────────────────────────
st.markdown(
    "<center><small>🌅 Daily AI Assistant v3.0 · "
    "<a href='https://github.com/Samuel-025/daily_ai_assistant'>GitHub</a> · "
    "<a href='https://dailyaiassistant-bfszw6tsvquoaav2acjhuo.streamlit.app/'>Live Demo</a>"
    "</small></center>",
    unsafe_allow_html=True,
)
