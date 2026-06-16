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

st.set_page_config(
    page_title="Daily AI Assistant",
    page_icon="🌅",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
  .block-container { padding-top: 0.6rem !important; padding-bottom: 0rem !important; }
  .stButton > button { width:100%; }
  .timer-box   { background:#1e2130; border-radius:14px; padding:22px; text-align:center; }
  .timer-digit { font-size:56px; font-weight:800; color:#7c6af7; letter-spacing:3px; }
</style>
""", unsafe_allow_html=True)


# ── Constants & helpers ──────────────────────────────────────────────
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

DEFAULT_PROFILE = {
    "name": "User", "wake_time": "07:00", "fitness": "moderate",
    "work_focus": "general", "diet_type": "balanced",
    "city": "Vasind", "country": "IN",
}

def _ss(key, default=None):
    """Read key from session_state; if missing, try saved profile.json; else use default."""
    if default is None:
        default = DEFAULT_PROFILE.get(key, "")
    if key in st.session_state:
        return st.session_state[key]
    profile_file = DATA_DIR / "profile.json"
    if profile_file.exists():
        p = load_json(profile_file, {})
        if key in p:
            st.session_state[key] = p[key]
            return p[key]
    return default


# ── LLM call ──────────────────────────────────────────────────────────
def ask_ai(messages: list) -> str:
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
    now = datetime.now().strftime("%A, %d %B %Y · %I:%M %p")
    tasks   = load_json(DATA_DIR / "tasks.json",  {"tasks": [], "completed": []})["tasks"]
    habits  = load_json(DATA_DIR / "habits.json", {"habits": []})["habits"]
    journal = load_json(DATA_DIR / f"journal_{date.today()}.json", {"entry": "", "mood": MOODS[1]})
    return f"""You are a warm, intelligent personal daily assistant for {_ss('name')}.
Today is {now}.
- Wake-up: {_ss('wake_time')} | Fitness: {_ss('fitness')} | Diet: {_ss('diet_type')}
- Work focus: {_ss('work_focus')} | City: {_ss('city')}, {_ss('country')}
- Active tasks: {', '.join(tasks[:5]) if tasks else 'none'}
- Habit streaks: {', '.join(f"{h['name']}({h.get('streak',0)}d)" for h in habits[:5]) if habits else 'none'}
- Today's mood: {journal.get('mood', 'unknown')}

Personality: concise, warm, practical, motivating — like a brilliant friend who is also a life coach.
Format responses with markdown (bullets, bold, tables) when it helps clarity.
Always give a useful, personalised response.

Slash commands:
/morning /tasks /habits /journal /meal /weather /news /focus /quote /help"""


# ────────────────────────────────────────────────────────────
# SIDEBAR
# ────────────────────────────────────────────────────────────

# Read profile values BEFORE sidebar so they're always in scope
# FIX: was previously inside an `else` on a `with` block (invalid Python)
name       = _ss("name")
wake_time  = _ss("wake_time")
fitness    = _ss("fitness")
work_focus = _ss("work_focus")
diet_type  = _ss("diet_type")
city       = _ss("city")
country    = _ss("country")

with st.sidebar:
    st.markdown("## 🌅 Daily AI Assistant")
    st.caption("v3.0 · ChatGPT-style · Private")
    st.divider()

    # — Provider
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
            mdl = st.text_input("Model", value=os.environ.get("OLLAMA_DEFAULT_MODEL", "llama3.2"),
                                help="ollama pull llama3.2")
            os.environ["OLLAMA_DEFAULT_MODEL"] = mdl
            st.info("💡 Local & free. [Install Ollama](https://ollama.ai)  \nRun: `ollama serve`")
        else:
            api_key = st.text_input(f"{provider.capitalize()} API Key",
                                    type="password", placeholder="Paste key…")
            if api_key:
                st.session_state.setdefault("api_keys", {})[provider] = api_key
                st.success("✅ Key saved")
            links = {
                "openai":    "https://platform.openai.com/api-keys",
                "anthropic": "https://console.anthropic.com",
                "groq":      "https://console.groq.com",
                "cohere":    "https://dashboard.cohere.com",
            }
            st.caption(f"[Get free key → {provider}]({links.get(provider, '#')})")

        model_names = {
            "ollama":    os.environ.get("OLLAMA_DEFAULT_MODEL", "llama3.2"),
            "groq":      "llama-3.3-70b-versatile",
            "openai":    "gpt-4o",
            "anthropic": "claude-3-5-sonnet",
            "cohere":    "command-a-03-2025",
        }
        st.caption(f"Model: `{model_names.get(provider, provider)}`")

    st.divider()

    # — Profile (expander — NO else block, values already read above)
    with st.expander("👤 Profile", expanded=False):
        name       = st.text_input("Name",         value=name)
        wake_time  = st.text_input("Wake-up",       value=wake_time)
        fitness    = st.selectbox("Fitness",        ["low","moderate","high"],
                                  index=["low","moderate","high"].index(fitness))
        work_focus = st.text_input("Work focus",    value=work_focus)
        diet_type  = st.selectbox("Diet",           ["balanced","vegetarian","vegan","keto"],
                                  index=["balanced","vegetarian","vegan","keto"].index(diet_type))
        city       = st.text_input("City",          value=city)
        country    = st.text_input("Country (ISO)", value=country,
                                   help="2-letter code: IN, US, GB …")
        if st.button("💾 Save Profile", use_container_width=True):
            for k, v in [("name",name),("wake_time",wake_time),("fitness",fitness),
                         ("work_focus",work_focus),("diet_type",diet_type),("city",city),("country",country)]:
                st.session_state[k] = v
            save_json(DATA_DIR / "profile.json",
                      {"name":name,"wake_time":wake_time,"fitness":fitness,
                       "work_focus":work_focus,"diet_type":diet_type,"city":city,"country":country})
            st.success("✅ Profile saved!")

    st.divider()

    # — Quick actions
    st.markdown("**⚡ Quick Actions**")
    QUICK = [
        ("🌅 Morning routine", "/morning"),
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
    msgs      = st.session_state.get("messages", [])
    user_msgs = sum(1 for m in msgs if m["role"] == "user")
    st.caption(f"💬 {user_msgs} messages this session")
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state["messages"] = []
        st.rerun()
    st.caption("🔒 Keys stored in session only.")


# ────────────────────────────────────────────────────────────
# SLASH COMMAND PROMPTS
# ────────────────────────────────────────────────────────────
SLASH_PROMPTS = {
    "/morning": (
        f"Create a personalised morning routine for {name} who wakes at {wake_time}."
        f" Fitness: {fitness}. Work focus: {work_focus}."
        " Use time blocks (e.g. 07:00–07:10) with one clear action each. Be energising."
    ),
    "/tasks": (
        f"List and prioritise {name}'s active tasks (most → least important)."
        f" Work focus: {work_focus}. Add a 1-line actionable tip per task."
    ),
    "/habits": (
        f"Analyse {name}'s habit streaks. Give:"
        " 1) What's going well, 2) Which habit to focus on next & why,"
        " 3) One science-backed consistency tip."
    ),
    "/journal": (
        f"Give {name} 3 thoughtful journaling prompts for today"
        f" based on their mood and work focus ({work_focus})."
        " Make them reflective and personal."
    ),
    "/meal": (
        f"Create a {diet_type} meal plan for {name} today."
        f" Cuisine: Indian. Fitness: {fitness}. Calorie target: ~2000 kcal."
        " 3 meals + 1 snack. For each: name, key ingredients, kcal, prep time."
    ),
    "/weather": (
        f"Suggest 4 activities for {name} in {city}, {country} today."
        f" Fitness: {fitness}. 2 outdoor, 2 indoor."
        " For each: activity name, duration, why it suits today, what to bring."
    ),
    "/news": (
        f"Give {name} a concise news briefing for {date.today()}"
        " covering: Technology, AI & ML, Health."
        " 3-5 bullet points. Factual, highlight what matters most."
    ),
    "/focus": (
        f"Create a Pomodoro focus schedule for {name} (work: {work_focus})."
        " 4 focus blocks of 25 min, 5-min short breaks, 1 long break (15 min) after block 4."
        " For each block: a specific sub-task, one energy tip, one distraction to avoid."
        " Format as a clean timetable."
    ),
    "/quote": (
        f"Give {name} one powerful quote for today (focus: {work_focus})."
        ' Format: \'"Quote" — Author\'. Then personalise it in 2 sentences for their work.'
    ),
    "/help": (
        "List all available slash commands with a short description."
        " Use a markdown table: Command | What it does."
    ),
}


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
                f"{datetime.now().strftime('%a %d %b %Y')}")
with col_badge:
    st.info(badge.get(provider, provider))

# ── Init message history ───────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# ── Welcome screen + suggestion chips (shown only when no messages yet) ─────
if not st.session_state["messages"]:
    st.markdown(
        f"""<div style='text-align:center;padding:40px 0 12px'>
        <span style='font-size:52px'>🌅</span><br>
        <h2 style='margin:10px 0 4px'>How can I help you today, {name}?</h2>
        <p style='color:#888;font-size:15px'>Type anything or pick a suggestion</p>
        </div>""",
        unsafe_allow_html=True,
    )
    CHIPS = [
        ("🌅 Morning routine",    "/morning"),
        ("📋 Prioritise tasks",   "/tasks"),
        ("🎯 Habit coaching",      "/habits"),
        ("🍽️ Meal plan",          "/meal"),
        ("📰 News briefing",       "/news"),
        ("⏱️ Focus schedule",      "/focus"),
        ("📝 Journal prompts",     "/journal"),
        ("💡 Motivate me",         "/quote"),
    ]
    cols = st.columns(4)
    for idx, (label, cmd) in enumerate(CHIPS):
        if cols[idx % 4].button(label, key=f"chip_{cmd}", use_container_width=True):
            st.session_state["pending_input"] = cmd
            st.rerun()

# ── Render chat history ─────────────────────────────────────────────────
for msg in st.session_state["messages"]:
    avatar = "🧑" if msg["role"] == "user" else "🌅"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# ── Chat input + pending input from sidebar/chips ────────────────────────
user_input = st.chat_input(f"Message your assistant… (try /help for commands)")

if "pending_input" in st.session_state and st.session_state["pending_input"]:
    user_input = st.session_state.pop("pending_input")

if user_input:
    raw = user_input.strip()

    with st.chat_message("user", avatar="🧑"):
        st.markdown(raw)
    st.session_state["messages"].append({"role": "user", "content": raw})

    # Resolve slash command → full prompt
    cmd_key = raw.lower().split()[0] if raw.startswith("/") else None
    prompt_content = SLASH_PROMPTS.get(cmd_key, raw)

    # Build LLM message list: system + last 20 history + current
    history  = st.session_state["messages"][:-1]
    recent   = history[-20:]
    llm_msgs = (
        [{"role": "system", "content": build_system_prompt()}]
        + [{"role": m["role"], "content": m["content"]} for m in recent]
        + [{"role": "user",   "content": prompt_content}]
    )

    with st.chat_message("assistant", avatar="🌅"):
        with st.spinner(""):
            response = ask_ai(llm_msgs)
        st.markdown(response)

    st.session_state["messages"].append({"role": "assistant", "content": response})


# ────────────────────────────────────────────────────────────
# TOOLS PANEL  (collapsible)
# ────────────────────────────────────────────────────────────
st.divider()
with st.expander("🛠️ Tools Panel — Tasks · Habits · Journal · Reminders · Timer", expanded=False):
    tool_tabs = st.tabs(["📋 Tasks", "🎯 Habits", "📝 Journal", "🔔 Reminders", "⏱️ Timer"])

    # ━━ TASKS
    with tool_tabs[0]:
        tasks_file = DATA_DIR / "tasks.json"
        td = load_json(tasks_file, {"tasks": [], "completed": []})
        c1, c2 = st.columns([3, 1])
        with c1:
            nt = st.text_input("New task", placeholder="Add task…", key="tp_newtask")
        with c2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Add", key="tp_addtask") and nt.strip():
                td["tasks"].append(nt.strip())
                save_json(tasks_file, td); st.rerun()
        ca, cb = st.columns(2)
        to_done, to_del = None, None
        with ca:
            st.markdown(f"**⏳ Active ({len(td['tasks'])})**")
            for i, t in enumerate(td["tasks"]):
                r = st.columns([5, 1, 1])
                with r[0]: st.markdown(f"○ {t}")
                with r[1]:
                    if st.button("✓",  key=f"tp_done_{i}"): to_done = i
                with r[2]:
                    if st.button("🗑️", key=f"tp_del_{i}"): to_del = i
        with cb:
            st.markdown(f"**✅ Done ({len(td['completed'])})**")
            for t in td["completed"]: st.markdown(f"✅ ~~{t}~~")
            if td["completed"] and st.button("🧹 Clear", key="tp_clear"):
                td["completed"] = []; save_json(tasks_file, td); st.rerun()
        if to_done is not None:
            td["completed"].append(td["tasks"].pop(to_done))
            save_json(tasks_file, td); st.rerun()
        if to_del is not None:
            td["tasks"].pop(to_del)
            save_json(tasks_file, td); st.rerun()

    # ━━ HABITS
    with tool_tabs[1]:
        habits_file = DATA_DIR / "habits.json"
        default_h = {"habits": [
            {"name": "Drink 8 glasses of water", "streak": 0, "target": 30},
            {"name": "Exercise 20 min",           "streak": 0, "target": 30},
            {"name": "Read 10 min",               "streak": 0, "target": 21},
            {"name": "Meditate 5 min",            "streak": 0, "target": 21},
            {"name": "Sleep by 11 PM",            "streak": 0, "target": 30},
        ]}
        hd = load_json(habits_file, default_h)
        do_inc, do_rst = None, None
        for i, h in enumerate(hd["habits"]):
            s, t = h.get("streak", 0), h.get("target", 30)
            row = st.columns([4, 1, 1, 1])
            with row[0]:
                st.markdown(f"**{h['name']}** — {s}/{t}")
                st.progress(min(s / t, 1.0))
            with row[1]: st.metric("", f"{s}🔥")
            with row[2]:
                if st.button("🔥", key=f"h_done_{i}", help="Done today"): do_inc = i
            with row[3]:
                if st.button("↺",  key=f"h_rst_{i}",  help="Reset"):        do_rst = i
        if do_inc is not None:
            hd["habits"][do_inc]["streak"] += 1; save_json(habits_file, hd); st.rerun()
        if do_rst is not None:
            hd["habits"][do_rst]["streak"]  = 0; save_json(habits_file, hd); st.rerun()
        nh_c1, nh_c2 = st.columns([3, 1])
        with nh_c1: nh  = st.text_input("New habit", key="tp_newhabit")
        with nh_c2: nt2 = st.number_input("Target days", 7, 365, 30, key="tp_target")
        if st.button("Add Habit", key="tp_addhabit") and nh.strip():
            hd["habits"].append({"name": nh.strip(), "streak": 0, "target": nt2})
            save_json(habits_file, hd); st.rerun()

    # ━━ JOURNAL
    with tool_tabs[2]:
        jtab1, jtab2 = st.tabs(["✍️ Today", "📚 History"])
        with jtab1:
            jf = DATA_DIR / f"journal_{date.today()}.json"
            je = load_json(jf, {"entry": "", "mood": MOODS[1], "date": str(date.today())})
            sm = je.get("mood", MOODS[1])
            mi = MOODS.index(sm) if sm in MOODS else 1
            entry = st.text_area("What's on your mind?", value=je.get("entry", ""),
                                  height=140, key="tp_journal")
            mood  = st.selectbox("Mood", MOODS, index=mi, key="tp_mood")
            if st.button("💾 Save", key="tp_savej"):
                save_json(jf, {"entry": entry, "mood": mood, "date": str(date.today())})
                st.success("Saved! ✅")
        with jtab2:
            past = sorted(DATA_DIR.glob("journal_*.json"), reverse=True)
            if not past:
                st.info("No past entries yet.")
            for pf in past[:10]:
                d2 = load_json(pf, {})
                with st.expander(f"{d2.get('date','?')} — {d2.get('mood','')}"):
                    st.markdown(d2.get("entry", "*(empty)*"))

    # ━━ REMINDERS
    with tool_tabs[3]:
        rf = DATA_DIR / "reminders.json"
        default_r = [
            {"time": "07:30", "message": "Drink water 💧",       "date": "daily"},
            {"time": "09:00", "message": "Check tasks 📋",        "date": "daily"},
            {"time": "13:00", "message": "Lunch break 🍽️",       "date": "daily"},
            {"time": "17:00", "message": "Evening stretch 🚶",   "date": "daily"},
            {"time": "22:00", "message": "Wind down 😴",           "date": "daily"},
        ]
        reminders = load_json(rf, default_r)
        now_str   = datetime.now().strftime("%H:%M")
        del_idx   = None
        for i, r in enumerate(reminders):
            row = st.columns([1, 4, 1])
            with row[0]: st.markdown(f"**⏰ {r['time']}**")
            with row[1]: st.markdown(("🔜 " if r["time"] >= now_str else "✓ ") + r["message"])
            with row[2]:
                if st.button("🗑️", key=f"tp_delr_{i}"): del_idx = i
        if del_idx is not None:
            reminders.pop(del_idx); save_json(rf, reminders); st.rerun()
        st.markdown("---")
        rc1, rc2, rc3 = st.columns([1, 3, 1])
        with rc1: rt = st.text_input("Time (HH:MM)", value="08:00", key="tp_rtime")
        with rc2: rm = st.text_input("Message", placeholder="e.g. Take medicine", key="tp_rmsg")
        with rc3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("+", key="tp_addr") and rm.strip():
                reminders.append({"time": rt, "message": rm, "date": "daily"})
                reminders.sort(key=lambda x: x["time"])
                save_json(rf, reminders); st.rerun()

    # ━━ FOCUS TIMER
    with tool_tabs[4]:
        tm = st.number_input("Minutes", 1, 120, 25, key="tp_timer")
        ts = int(tm) * 60
        st.markdown(f"""
        <div class="timer-box">
          <div class="timer-digit" id="tp-timer-display">{int(tm):02d}:00</div>
          <p style="color:#888;margin-top:6px">{tm}-minute focus session</p>
          <button onclick="tpStart({ts})"
            style="background:#7c6af7;color:#fff;border:none;padding:9px 24px;
                   border-radius:8px;font-size:15px;cursor:pointer;margin:4px">▶ Start</button>
          <button onclick="tpReset({ts})"
            style="background:#374151;color:#fff;border:none;padding:9px 20px;
                   border-radius:8px;font-size:15px;cursor:pointer;margin:4px">↺ Reset</button>
        </div>
        <script>
          var _tp = null;
          function tpStart(s) {{
            if (_tp) return;
            var r = s;
            _tp = setInterval(function() {{
              if (r <= 0) {{
                clearInterval(_tp); _tp = null;
                document.getElementById('tp-timer-display').innerText = '✅ Done!';
                document.getElementById('tp-timer-display').style.color = '#4ade80';
                return;
              }}
              r--;
              var m = Math.floor(r / 60), sc = r % 60;
              document.getElementById('tp-timer-display').innerText =
                (m < 10 ? '0' : '') + m + ':' + (sc < 10 ? '0' : '') + sc;
            }}, 1000);
          }}
          function tpReset(s) {{
            clearInterval(_tp); _tp = null;
            var m = Math.floor(s / 60);
            document.getElementById('tp-timer-display').innerText = (m < 10 ? '0' : '') + m + ':00';
            document.getElementById('tp-timer-display').style.color = '#7c6af7';
          }}
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
