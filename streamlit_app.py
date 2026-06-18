#!/usr/bin/env python3
"""
Daily AI Assistant v3.0  -  ChatGPT-style interactive interface
"""

import streamlit as st
import json
import os
import requests
from pathlib import Path
from datetime import datetime, date
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Daily AI Assistant",
    page_icon="\U0001f305",
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


# ── Constants & helpers ───────────────────────────────────────────────────
DATA_DIR = Path("demo_data")
DATA_DIR.mkdir(exist_ok=True)
MOODS = ["\U0001f60a Great", "\U0001f610 Okay", "\U0001f614 Low", "\U0001f624 Frustrated", "\U0001f634 Tired"]

def load_json(path, default):
    if Path(path).exists():
        try: return json.loads(Path(path).read_text(encoding="utf-8"))
        except: pass
    Path(path).write_text(json.dumps(default, indent=2), encoding="utf-8")
    return default

def save_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")

DEFAULT_PROFILE = {
    "name": "User", "wake_time": "07:00", "fitness": "moderate",
    "work_focus": "general", "diet_type": "balanced",
    "city": "Vasind", "country": "IN",
}

def _ss(key, default=None):
    if default is None:
        default = DEFAULT_PROFILE.get(key, "")
    if key in st.session_state:
        return st.session_state[key]
    pf = DATA_DIR / "profile.json"
    if pf.exists():
        p = load_json(pf, {})
        if key in p:
            st.session_state[key] = p[key]
            return p[key]
    return default


# ── Direct LLM callers (bypass LLMManager — use chat message format) ──
def _call_ollama(messages: list) -> str:
    """Call local Ollama with proper chat endpoint."""
    url   = os.environ.get("OLLAMA_API_URL", "http://localhost:11434")
    model = os.environ.get("OLLAMA_DEFAULT_MODEL", "llama3.2")
    try:
        r = requests.post(
            url + "/api/chat",
            json={"model": model, "messages": messages, "stream": False},
            timeout=120,
        )
        if r.ok:
            return r.json().get("message", {}).get("content", "") or ""
        return ""
    except requests.exceptions.ConnectionError:
        raise ConnectionError(
            "Ollama is not running.\n"
            "Fix: open a terminal and run `ollama serve`\n"
            "Then pull a model: `ollama pull llama3.2`"
        )

def _call_groq(messages: list, api_key: str) -> str:
    from groq import Groq
    client = Groq(api_key=api_key)
    resp = client.chat.completions.create(
        model=os.environ.get("GROQ_DEFAULT_MODEL", "llama-3.3-70b-versatile"),
        messages=messages,
    )
    return resp.choices[0].message.content or ""

def _call_openai(messages: list, api_key: str) -> str:
    import openai
    client = openai.OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model=os.environ.get("OPENAI_DEFAULT_MODEL", "gpt-4o"),
        messages=messages,
    )
    return resp.choices[0].message.content or ""

def _call_anthropic(messages: list, api_key: str) -> str:
    import anthropic
    # Anthropic separates system from messages
    sys_msg = next((m["content"] for m in messages if m["role"] == "system"), "")
    chat_msgs = [m for m in messages if m["role"] != "system"]
    client = anthropic.Anthropic(api_key=api_key)
    resp = client.messages.create(
        model=os.environ.get("ANTHROPIC_DEFAULT_MODEL", "claude-3-5-sonnet-20241022"),
        max_tokens=2048,
        system=sys_msg,
        messages=chat_msgs,
    )
    # resp.content is a list of content blocks; only TextBlock has .text
    if resp.content and hasattr(resp.content[0], "text"):
        return getattr(resp.content[0], "text") or ""
    return ""

def _call_cohere(messages: list, api_key: str) -> str:
    import cohere
    client = cohere.ClientV2(api_key)
    resp = client.chat(
        model=os.environ.get("COHERE_DEFAULT_MODEL", "command-a-03-2025"),
        messages=messages,
    )
    # resp.message.content is a list; guard against None and non-text blocks
    content = resp.message.content if resp.message else None
    if content and hasattr(content[0], "text"):
        return getattr(content[0], "text") or ""
    return ""


def ask_ai(messages: list) -> str:
    """
    Call the selected LLM provider with a proper structured messages list.
    messages = [{"role": "system"|"user"|"assistant", "content": "..."}]
    Returns the assistant reply string, or a clear error message.
    """
    provider: str = str(st.session_state.get("provider", "ollama"))
    api_keys = st.session_state.get("api_keys", {})
    # Also check environment variables as fallback
    env_keys = {
        "openai":    os.environ.get("OPENAI_API_KEY", ""),
        "anthropic": os.environ.get("ANTHROPIC_API_KEY", ""),
        "groq":      os.environ.get("GROQ_API_KEY", ""),
        "cohere":    os.environ.get("COHERE_API_KEY", ""),
    }

    def get_key(p):
        return api_keys.get(p) or env_keys.get(p, "")

    try:
        if provider == "ollama":
            result = _call_ollama(messages)
            if not result:
                return (
                    "**Ollama returned an empty response.**\n\n"
                    "Make sure:\n"
                    "1. `ollama serve` is running in a terminal\n"
                    "2. You have pulled a model: `ollama pull llama3.2`\n"
                    "3. Try switching to Groq (free) in the sidebar instead."
                )
            return result

        elif provider == "groq":
            key = get_key("groq")
            if not key:
                return (
                    "**No Groq API key found.**\n\n"
                    "Paste your free key in the sidebar (Groq API Key field).\n"
                    "Get one free at https://console.groq.com"
                )
            return _call_groq(messages, key)

        elif provider == "openai":
            key = get_key("openai")
            if not key:
                return (
                    "**No OpenAI API key found.**\n\n"
                    "Paste your key in the sidebar.\n"
                    "Get one at https://platform.openai.com/api-keys"
                )
            return _call_openai(messages, key)

        elif provider == "anthropic":
            key = get_key("anthropic")
            if not key:
                return (
                    "**No Anthropic API key found.**\n\n"
                    "Paste your key in the sidebar.\n"
                    "Get one at https://console.anthropic.com"
                )
            return _call_anthropic(messages, key)

        elif provider == "cohere":
            key = get_key("cohere")
            if not key:
                return (
                    "**No Cohere API key found.**\n\n"
                    "Paste your key in the sidebar.\n"
                    "Get one free at https://dashboard.cohere.com"
                )
            return _call_cohere(messages, key)

        else:
            return f"**Unknown provider:** `{provider}`. Select one from the sidebar."

    except ConnectionError as e:
        return "**Connection Error**\n\n" + str(e)
    except Exception as e:
        return (
            "**Error calling " + provider + ":** `" + str(e) + "`\n\n"
            "Check the sidebar — make sure your API key is correct and the provider is reachable."
        )


def build_system_prompt() -> str:
    now    = datetime.now().strftime("%A, %d %B %Y - %I:%M %p")
    tasks  = load_json(DATA_DIR / "tasks.json",  {"tasks": [], "completed": []})["tasks"]
    habits = load_json(DATA_DIR / "habits.json", {"habits": []})["habits"]
    jrnl   = load_json(DATA_DIR / ("journal_" + str(date.today()) + ".json"), {"mood": MOODS[1]})

    tasks_str  = ", ".join(tasks[:5]) if tasks else "none"
    habits_str = ", ".join(h["name"] + "(" + str(h.get("streak", 0)) + "d)" for h in habits[:5]) if habits else "none"
    mood_str   = jrnl.get("mood", "unknown")

    return (
        "You are a warm, intelligent personal daily assistant for " + _ss("name") + ".\n"
        "Today is " + now + ".\n"
        "- Wake-up: " + _ss("wake_time") + " | Fitness: " + _ss("fitness") + " | Diet: " + _ss("diet_type") + "\n"
        "- Work focus: " + _ss("work_focus") + " | City: " + _ss("city") + ", " + _ss("country") + "\n"
        "- Active tasks: " + tasks_str + "\n"
        "- Habit streaks: " + habits_str + "\n"
        "- Today's mood: " + mood_str + "\n\n"
        "Personality: concise, warm, practical, motivating - like a brilliant friend who is also a life coach.\n"
        "Use markdown (bullets, bold, tables) when it helps clarity.\n"
        "Always give a useful, personalised response.\n"
        "Slash commands you can reference: /morning /tasks /habits /journal /meal /weather /news /focus /quote /help"
    )


# ── PROFILE (read before sidebar) ────────────────────────────────────────────
name       = _ss("name")
wake_time  = _ss("wake_time")
fitness    = _ss("fitness")
work_focus = _ss("work_focus")
diet_type  = _ss("diet_type")
city       = _ss("city")
country    = _ss("country")


# ── SIDEBAR ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## \U0001f305 Daily AI Assistant")
    st.caption("v3.0 - ChatGPT-style - Private")
    st.divider()

    st.markdown("**\U0001f916 LLM Provider**")
    provider = st.selectbox(
        "Provider",
        ["ollama", "groq", "openai", "anthropic", "cohere"],
        index=["ollama", "groq", "openai", "anthropic", "cohere"].index(
            st.session_state.get("provider", "ollama")
        ),
        label_visibility="collapsed",
    )
    st.session_state["provider"] = provider

    if provider == "ollama":
        mdl = st.text_input("Ollama model",
                            value=os.environ.get("OLLAMA_DEFAULT_MODEL", "llama3.2"),
                            help="Run: ollama serve")
        os.environ["OLLAMA_DEFAULT_MODEL"] = mdl
        st.info("\U0001f4a1 Free & local. [Install Ollama](https://ollama.ai)\nRun: `ollama serve`")
    else:
        key_label = provider.capitalize() + " API Key"
        existing  = (st.session_state.get("api_keys") or {}).get(provider, "")
        api_key   = st.text_input(key_label, type="password",
                                  placeholder="Paste key...",
                                  value=existing)
        if api_key:
            st.session_state.setdefault("api_keys", {})[provider] = api_key
            st.success("\u2705 Key saved for " + provider)
        links = {
            "openai":    "https://platform.openai.com/api-keys",
            "anthropic": "https://console.anthropic.com",
            "groq":      "https://console.groq.com",
            "cohere":    "https://dashboard.cohere.com",
        }
        st.caption("[Get free key -> " + provider + "](" + links.get(provider, "#") + ")")

    model_display = {
        "ollama":    os.environ.get("OLLAMA_DEFAULT_MODEL", "llama3.2"),
        "groq":      "llama-3.3-70b-versatile",
        "openai":    "gpt-4o",
        "anthropic": "claude-3-5-sonnet-20241022",
        "cohere":    "command-a-03-2025",
    }
    st.caption("Model: `" + model_display.get(provider, provider) + "`")
    st.divider()

    st.markdown("**\U0001f464 Profile**")
    name       = st.text_input("Name",          value=name)
    wake_time  = st.text_input("Wake-up",        value=wake_time)
    fitness    = st.selectbox("Fitness",         ["low", "moderate", "high"],
                              index=["low", "moderate", "high"].index(fitness))
    work_focus = st.text_input("Work focus",     value=work_focus)
    diet_type  = st.selectbox("Diet",            ["balanced", "vegetarian", "vegan", "keto"],
                              index=["balanced", "vegetarian", "vegan", "keto"].index(diet_type))
    city       = st.text_input("City",           value=city)
    country    = st.text_input("Country (ISO)",  value=country,
                               help="2-letter code: IN, US, GB ...")
    if st.button("\U0001f4be Save Profile", use_container_width=True):
        for k, v in [("name", name), ("wake_time", wake_time), ("fitness", fitness),
                     ("work_focus", work_focus), ("diet_type", diet_type),
                     ("city", city), ("country", country)]:
            st.session_state[k] = v
        save_json(DATA_DIR / "profile.json",
                  {"name": name, "wake_time": wake_time, "fitness": fitness,
                   "work_focus": work_focus, "diet_type": diet_type,
                   "city": city, "country": country})
        st.success("\u2705 Profile saved!")
    st.divider()

    st.markdown("**\u26a1 Quick Actions**")
    QUICK = [
        ("\U0001f305 Morning routine", "/morning"),
        ("\U0001f4cb My tasks",         "/tasks"),
        ("\U0001f3af Habit check-in",   "/habits"),
        ("\U0001f4dd Journal prompt",   "/journal"),
        ("\U0001f37d Meal plan",        "/meal"),
        ("\U0001f324 Activities",       "/weather"),
        ("\U0001f4f0 News briefing",    "/news"),
        ("\u23f1 Focus schedule",       "/focus"),
        ("\U0001f4a1 Quote",            "/quote"),
    ]
    for label, cmd in QUICK:
        if st.button(label, key="quick_" + cmd, use_container_width=True):
            st.session_state["pending_input"] = cmd
            st.rerun()
    st.divider()

    msgs      = st.session_state.get("messages", [])
    user_msgs = sum(1 for m in msgs if m["role"] == "user")
    st.caption("\U0001f4ac " + str(user_msgs) + " messages this session")
    if st.button("Clear Chat", use_container_width=True):
        st.session_state["messages"] = []
        st.rerun()
    st.caption("\U0001f512 Keys stored in session only.")


# ── SLASH COMMAND PROMPTS ───────────────────────────────────────────────────────
SLASH_PROMPTS = {
    "/morning": (
        "Create a personalised morning routine for " + name + " who wakes at " + wake_time + "."
        " Fitness: " + fitness + ". Work focus: " + work_focus + "."
        " Use time blocks (e.g. 07:00-07:10) with one clear action each. Be energising."
    ),
    "/tasks": (
        "List and prioritise " + name + "'s active tasks (most to least important)."
        " Work focus: " + work_focus + ". Add a 1-line actionable tip per task."
    ),
    "/habits": (
        "Analyse " + name + "'s habit streaks. Give:"
        " 1) What's going well, 2) Which habit to focus on next and why,"
        " 3) One science-backed consistency tip."
    ),
    "/journal": (
        "Give " + name + " 3 thoughtful journaling prompts for today"
        " based on their mood and work focus (" + work_focus + ")."
        " Make them reflective and personal."
    ),
    "/meal": (
        "Create a " + diet_type + " meal plan for " + name + " today."
        " Cuisine: Indian. Fitness: " + fitness + ". Calorie target: ~2000 kcal."
        " 3 meals + 1 snack. For each: name, key ingredients, kcal, prep time."
    ),
    "/weather": (
        "Suggest 4 activities for " + name + " in " + city + ", " + country + " today."
        " Fitness: " + fitness + ". 2 outdoor, 2 indoor."
        " For each: activity name, duration, why it suits today, what to bring."
    ),
    "/news": (
        "Give " + name + " a concise news briefing for " + str(date.today()) +
        " covering: Technology, AI & ML, Health."
        " 3-5 bullet points. Factual, highlight what matters most."
    ),
    "/focus": (
        "Create a Pomodoro focus schedule for " + name + " (work: " + work_focus + ")."
        " 4 blocks of 25 min, 5-min breaks, 1 long break (15 min) after block 4."
        " For each block: specific sub-task, one energy tip, one distraction to avoid."
        " Format as a clean timetable."
    ),
    "/quote": (
        "Give " + name + " one powerful quote for today (focus: " + work_focus + ")."
        " Format: Quote - Author. Personalise it in 2 sentences."
    ),
    "/help": (
        "List all slash commands with a short description."
        " Use a markdown table: Command | What it does."
    ),
}


# ── MAIN CHAT AREA ──────────────────────────────────────────────────────────────
hour     = datetime.now().hour
greeting = "morning" if hour < 12 else "afternoon" if hour < 17 else "evening"
badge    = {
    "ollama":    "\U0001f7e2 Local",
    "openai":    "\U0001f535 OpenAI",
    "anthropic": "\U0001f7e3 Anthropic",
    "groq":      "\U0001f7e1 Groq",
    "cohere":    "\U0001f7e0 Cohere",
}

col_title, col_badge = st.columns([5, 1])
with col_title:
    st.markdown("### \U0001f305 Good " + greeting + ", **" + name + "** - "
                + datetime.now().strftime("%a %d %b %Y"))
with col_badge:
    st.info(badge.get(provider, provider))

if "messages" not in st.session_state:
    st.session_state["messages"] = []

if not st.session_state["messages"]:
    st.markdown(
        "<div style='text-align:center;padding:40px 0 12px'>"
        "<span style='font-size:52px'>\U0001f305</span><br>"
        "<h2 style='margin:10px 0 4px'>How can I help you today, " + name + "?</h2>"
        "<p style='color:#888;font-size:15px'>Type anything or pick a suggestion</p>"
        "</div>",
        unsafe_allow_html=True,
    )
    CHIPS = [
        ("\U0001f305 Morning routine",  "/morning"),
        ("\U0001f4cb Prioritise tasks",  "/tasks"),
        ("\U0001f3af Habit coaching",    "/habits"),
        ("\U0001f37d Meal plan",         "/meal"),
        ("\U0001f4f0 News briefing",     "/news"),
        ("\u23f1 Focus schedule",        "/focus"),
        ("\U0001f4dd Journal prompts",   "/journal"),
        ("\U0001f4a1 Motivate me",       "/quote"),
    ]
    cols = st.columns(4)
    for idx, (label, cmd) in enumerate(CHIPS):
        if cols[idx % 4].button(label, key="chip_" + cmd, use_container_width=True):
            st.session_state["pending_input"] = cmd
            st.rerun()

for msg in st.session_state["messages"]:
    avatar = "\U0001f9d1" if msg["role"] == "user" else "\U0001f305"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

user_input = st.chat_input("Message your assistant... (try /help for commands)")
if "pending_input" in st.session_state and st.session_state["pending_input"]:
    user_input = st.session_state.pop("pending_input")

if user_input:
    raw = user_input.strip()
    with st.chat_message("user", avatar="\U0001f9d1"):
        st.markdown(raw)
    st.session_state["messages"].append({"role": "user", "content": raw})

    # Resolve slash command: cmd_key is str only when input starts with '/'
    cmd_key: str | None = raw.lower().split()[0] if raw.startswith("/") else None
    prompt_content = SLASH_PROMPTS[cmd_key] if cmd_key is not None and cmd_key in SLASH_PROMPTS else raw

    # Build proper chat messages: system + last 20 history + current user message
    history  = st.session_state["messages"][:-1]
    recent   = history[-20:]
    llm_msgs = (
        [{"role": "system",    "content": build_system_prompt()}]
        + [{"role": m["role"], "content": m["content"]} for m in recent]
        + [{"role": "user",    "content": prompt_content}]
    )

    with st.chat_message("assistant", avatar="\U0001f305"):
        with st.spinner("Thinking..."):
            response = ask_ai(llm_msgs)
        st.markdown(response)
    st.session_state["messages"].append({"role": "assistant", "content": response})


# ── TOOLS PANEL ──────────────────────────────────────────────────────────────────
st.divider()
with st.expander("Tools Panel - Tasks / Habits / Journal / Reminders / Timer", expanded=False):

    tool_tabs = st.tabs(["\U0001f4cb Tasks", "\U0001f3af Habits", "\U0001f4dd Journal",
                         "\U0001f514 Reminders", "\u23f1 Timer"])

    # ── TASKS
    with tool_tabs[0]:
        tasks_file = DATA_DIR / "tasks.json"
        td = load_json(tasks_file, {"tasks": [], "completed": []})
        c1, c2 = st.columns([3, 1])
        with c1:
            nt = st.text_input("New task", placeholder="Add task...", key="tp_newtask")
        with c2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Add", key="tp_addtask") and nt.strip():
                td["tasks"].append(nt.strip())
                save_json(tasks_file, td)
                st.rerun()
        ca, cb = st.columns(2)
        to_done, to_del = None, None
        with ca:
            st.markdown("**Active (" + str(len(td["tasks"])) + ")**")
            for i, t in enumerate(td["tasks"]):
                r = st.columns([5, 1, 1])
                with r[0]: st.markdown("- " + t)
                with r[1]:
                    if st.button("Done", key="tp_done_" + str(i)): to_done = i
                with r[2]:
                    if st.button("Del", key="tp_del_" + str(i)): to_del = i
        with cb:
            st.markdown("**Done (" + str(len(td["completed"])) + ")**")
            for t in td["completed"]:
                st.markdown("\u2705 ~~" + t + "~~")
            if td["completed"] and st.button("Clear done", key="tp_clear"):
                td["completed"] = []
                save_json(tasks_file, td)
                st.rerun()
        if to_done is not None:
            td["completed"].append(td["tasks"].pop(to_done))
            save_json(tasks_file, td); st.rerun()
        if to_del is not None:
            td["tasks"].pop(to_del)
            save_json(tasks_file, td); st.rerun()

    # ── HABITS
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
            s = h.get("streak", 0)
            t = h.get("target", 30)
            row = st.columns([4, 1, 1, 1])
            with row[0]:
                st.markdown("**" + h["name"] + "** - " + str(s) + "/" + str(t))
                st.progress(min(s / t, 1.0))
            with row[1]:
                st.metric("", str(s) + " streak")
            with row[2]:
                if st.button("+1", key="h_done_" + str(i), help="Mark done today"): do_inc = i
            with row[3]:
                if st.button("Reset", key="h_rst_" + str(i), help="Reset streak"): do_rst = i
        if do_inc is not None:
            hd["habits"][do_inc]["streak"] += 1
            save_json(habits_file, hd); st.rerun()
        if do_rst is not None:
            hd["habits"][do_rst]["streak"] = 0
            save_json(habits_file, hd); st.rerun()
        nh_c1, nh_c2 = st.columns([3, 1])
        with nh_c1:
            nh = st.text_input("New habit name", key="tp_newhabit")
        with nh_c2:
            nt2 = st.number_input("Target days", 7, 365, 30, key="tp_target")
        if st.button("Add Habit", key="tp_addhabit") and nh.strip():
            hd["habits"].append({"name": nh.strip(), "streak": 0, "target": nt2})
            save_json(habits_file, hd); st.rerun()

    # ── JOURNAL
    with tool_tabs[2]:
        jview = st.radio("View", ["Today", "History"],
                         horizontal=True, label_visibility="collapsed", key="jrnl_view")
        if jview == "Today":
            jf = DATA_DIR / ("journal_" + str(date.today()) + ".json")
            je = load_json(jf, {"entry": "", "mood": MOODS[1], "date": str(date.today())})
            sm = je.get("mood", MOODS[1])
            mi = MOODS.index(sm) if sm in MOODS else 1
            entry = st.text_area("What's on your mind?", value=je.get("entry", ""),
                                  height=140, key="tp_journal")
            mood  = st.selectbox("Mood", MOODS, index=mi, key="tp_mood")
            if st.button("Save Entry", key="tp_savej"):
                save_json(jf, {"entry": entry, "mood": mood, "date": str(date.today())})
                st.success("Saved! \u2705")
        else:
            past = sorted(DATA_DIR.glob("journal_*.json"), reverse=True)
            if not past:
                st.info("No past entries yet. Start writing today!")
            for pf in past[:10]:
                d2 = load_json(pf, {})
                with st.container():
                    st.markdown("**" + str(d2.get("date", "?")) + "** - " + str(d2.get("mood", "")))
                    etxt = str(d2.get("entry", "")).strip()
                    st.markdown(etxt if etxt else "*No content written.*")
                    st.divider()

    # ── REMINDERS
    with tool_tabs[3]:
        rf = DATA_DIR / "reminders.json"
        default_r = [
            {"time": "07:30", "message": "Drink water",    "date": "daily"},
            {"time": "09:00", "message": "Check tasks",     "date": "daily"},
            {"time": "13:00", "message": "Lunch break",     "date": "daily"},
            {"time": "17:00", "message": "Evening stretch", "date": "daily"},
            {"time": "22:00", "message": "Wind down",       "date": "daily"},
        ]
        reminders = load_json(rf, default_r)
        now_str   = datetime.now().strftime("%H:%M")
        del_idx   = None
        for i, r in enumerate(reminders):
            row = st.columns([1, 4, 1])
            with row[0]: st.markdown("**" + r["time"] + "**")
            with row[1]:
                prefix = ">> " if r["time"] >= now_str else "ok "
                st.markdown(prefix + r["message"])
            with row[2]:
                if st.button("Del", key="tp_delr_" + str(i)): del_idx = i
        if del_idx is not None:
            reminders.pop(del_idx)
            save_json(rf, reminders); st.rerun()
        st.markdown("---")
        rc1, rc2, rc3 = st.columns([1, 3, 1])
        with rc1: rt = st.text_input("Time (HH:MM)", value="08:00", key="tp_rtime")
        with rc2: rm = st.text_input("Message", placeholder="e.g. Take medicine", key="tp_rmsg")
        with rc3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Add", key="tp_addr") and rm.strip():
                reminders.append({"time": rt, "message": rm, "date": "daily"})
                reminders.sort(key=lambda x: x["time"])
                save_json(rf, reminders); st.rerun()

    # ── FOCUS TIMER
    with tool_tabs[4]:
        tm = st.number_input("Minutes", 1, 120, 25, key="tp_timer")
        ts = int(tm) * 60
        tm_display = str(int(tm)).zfill(2) + ":00"
        st.markdown(
            "<div class=\"timer-box\">"
            "<div class=\"timer-digit\" id=\"tp-timer-display\">" + tm_display + "</div>"
            "<p style=\"color:#888;margin-top:6px\">" + str(int(tm)) + "-minute focus session</p>"
            "<button onclick=\"tpStart(" + str(ts) + ")\""
            " style=\"background:#7c6af7;color:#fff;border:none;padding:9px 24px;"
            "border-radius:8px;font-size:15px;cursor:pointer;margin:4px\">Start</button>"
            "<button onclick=\"tpReset(" + str(ts) + ")\""
            " style=\"background:#374151;color:#fff;border:none;padding:9px 20px;"
            "border-radius:8px;font-size:15px;cursor:pointer;margin:4px\">Reset</button>"
            "</div>"
            "<script>"
            "var _tp=null;"
            "function tpStart(s){if(_tp)return;var r=s;"
            "_tp=setInterval(function(){"
            "if(r<=0){clearInterval(_tp);_tp=null;"
            "document.getElementById('tp-timer-display').innerText='Done!';"
            "document.getElementById('tp-timer-display').style.color='#4ade80';return;}"
            "r--;var m=Math.floor(r/60),sc=r%60;"
            "document.getElementById('tp-timer-display').innerText="
            "(m<10?'0':'')+m+':'+(sc<10?'0':'')+sc;"
            "},1000);}"
            "function tpReset(s){clearInterval(_tp);_tp=null;"
            "var m=Math.floor(s/60);"
            "document.getElementById('tp-timer-display').innerText=(m<10?'0':'')+m+':00';"
            "document.getElementById('tp-timer-display').style.color='#7c6af7';}"
            "</script>",
            unsafe_allow_html=True,
        )


# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(
    "<center><small>Daily AI Assistant v3.0 - "
    "<a href='https://github.com/Samuel-025/daily_ai_assistant'>GitHub</a> - "
    "<a href='https://dailyaiassistant-bfszw6tsvquoaav2acjhuo.streamlit.app/'>Live Demo</a>"
    "</small></center>",
    unsafe_allow_html=True,
)
