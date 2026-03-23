import streamlit as st
import requests
from dotenv import load_dotenv
import os
load_dotenv()
HF_TOKEN_DEFAULT = os.getenv("HF_TOKEN", "")


import re as _re

STUDY_KEYWORDS = _re.compile(
    r'\b(exam|test|quiz|study|studie|studying|assignment|project|deadline|'
    r'cgpa|gpa|grade|mark|result|score|percentage|attendance|bunk|backlog|arrear|'
    r'college|university|semester|syllabus|subject|lecture|professor|teacher|'
    r'stress|anxious|overwhelm|burnout|sleep|motivation|focus|productiv|'
    r'internship|placement|job|career|resume|interview|linkedin|'
    r'learn|revision|revise|note|flashcard|pomodoro|feynman|'
    r'time management|schedule|planner|distract|procrastinat)\b',
    _re.IGNORECASE
)

OFF_TOPIC_KEYWORDS = _re.compile(
    r'\b(weather|poem|song|lyric|recipe|cook|movie|film|sport|cricket|football|'
    r'news|politic|stock|crypto|bitcoin|joke|story|novel|draw|paint|'
    r'translat|capital of|president of|prime minister|bank|banking|loan|'
    r'insurance|invest|mutual fund|tax|passport|visa|travel|hotel|restaurant|'
    r'celebrity|actor|actress|singer|game|minecraft|fortnite|pubg)\b',
    _re.IGNORECASE
)

def is_study_related(text: str):
    if OFF_TOPIC_KEYWORDS.search(text):
        return False
    if STUDY_KEYWORDS.search(text):
        return True
    return None

OFF_TOPIC_REPLY = (
    "Sorry, I'm StudyBot AI — I can only help with college and "
    "study-related topics like exams, assignments, stress, CGPA, "
    "internships, and time management. Try asking me something like that! 🎓"
)

st.set_page_config(page_title="StudyBot AI", page_icon="✨", layout="centered")

st.markdown("""
<style>
    .stApp, .stApp > div, [data-testid="stAppViewContainer"],
    [data-testid="stHeader"], [data-testid="stToolbar"],
    [data-testid="stBottom"], section.main, .main .block-container {
        background-color: #000000 !important;
    }
    .chat-title {
        text-align: center; font-size: 2rem; font-weight: 700;
        background: linear-gradient(90deg, #a78bfa, #7c3aed);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .chat-subtitle { text-align: center; color: #9ca3af; margin-top: 0; font-size: 0.95rem; }
    .info-box {
        background: #1a1a2e; border-radius: 12px; padding: 14px 18px;
        border-left: 4px solid #7c3aed; margin-bottom: 1rem;
        color: #e2e8f0 !important; font-weight: 500;
    }
    .info-box strong { color: #a78bfa !important; }
    [data-testid="stSidebar"] { background-color: #0d0d1a !important; }
    [data-testid="stSidebar"] * { color: #e2e8f0 !important; }
</style>
""", unsafe_allow_html=True)

SYSTEM_PROMPT = """You are StudyBot AI, a friendly and knowledgeable college student assistant.
You help students with exam prep, assignments, time management, study techniques,
stress management, internships, CGPA improvement, and motivation.
Be warm, encouraging, concise, and practical. Only answer college/student-related questions."""

st.markdown('<p class="chat-title">✨ StudyBot AI</p>', unsafe_allow_html=True)
st.markdown('<p class="chat-subtitle">Powered by Hugging Face · Your Intelligent College Assistant</p>',
            unsafe_allow_html=True)
st.divider()

with st.sidebar:
    st.header("⚙️ Configuration")
    hf_token = st.text_input(
        "Hugging Face API Token",
        value=HF_TOKEN_DEFAULT,
        type="password",
        placeholder="hf_xxxxxxxxxxxxxxxxxxxx",
        help="Get your free token at https://huggingface.co/settings/tokens"
    )
    st.markdown("""
**How to get a free token:**
1. Go to [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
2. Sign up / Log in (free)
3. Click **New token** → select **Read** role
4. Paste it above ☝️
""")
    st.divider()

    # Model IDs with :auto suffix so HF picks best available provider
    MODEL_OPTIONS = {
        "Llama 3.1 8B (Cerebras)": "meta-llama/Llama-3.1-8B-Instruct:cerebras",
        "Llama 3.3 70B (Sambanova)": "meta-llama/Llama-3.3-70B-Instruct:sambanova",
        "DeepSeek R1 (Together)": "deepseek-ai/DeepSeek-R1:together",
    }
    model_label = st.selectbox("Model", list(MODEL_OPTIONS.keys()), index=0)
    model_id = MODEL_OPTIONS[model_label]

    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.caption("StudyBot AI — LLM Chatbot\nBuilt with Streamlit + Hugging Face")

if "messages" not in st.session_state:
    st.session_state.messages = []

if not hf_token:
    st.markdown("""
    <div class="info-box">
    🔑 <strong>Enter your Hugging Face API token in the sidebar to get started.</strong><br>
    It's completely free — no credit card needed!
    </div>
    """, unsafe_allow_html=True)
    cols = st.columns(2)
    features = [
        ("📝", "Exam Preparation", "Personalised revision strategies & tips"),
        ("📋", "Assignments", "Breaking down complex tasks step by step"),
        ("🕐", "Time Management", "Schedules, planners, and productivity hacks"),
        ("📚", "Study Techniques", "Pomodoro, Feynman, spaced repetition & more"),
        ("😌", "Stress Support", "Coping strategies and mental health tips"),
        ("💼", "Career Advice", "Internships, resumes, and interview prep"),
    ]
    for i, (icon, title, desc) in enumerate(features):
        cols[i % 2].info(f"{icon} **{title}**\n{desc}")
    st.stop()

def query_hf(user_message: str, history: list) -> str:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in history[-8:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})

    url = "https://router.huggingface.co/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {hf_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model_id,
        "messages": messages,
        "max_tokens": 512,
        "temperature": 0.7,
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"].strip()
        elif response.status_code == 401:
            return "❌ Invalid token. Please check your Hugging Face API token in the sidebar."
        elif response.status_code == 503:
            return "⏳ Model is loading, please try again in ~20 seconds!"
        else:
            return f"❌ Error {response.status_code}: {response.text[:300]}"
    except requests.exceptions.Timeout:
        return "⏳ Request timed out — please try again!"
    except Exception as e:
        return f"❌ Unexpected error: {str(e)}"

if not st.session_state.messages:
    st.session_state.messages.append({
        "role": "assistant",
        "content": ("👋 Hey! I'm **StudyBot AI**, powered by Hugging Face.\n\n"
                    "I'm here to help with anything college-related — exams, assignments, "
                    "time management, stress, career advice, and more.\n\n"
                    "What's on your mind today? 🎓")
    })

for msg in st.session_state.messages:
    avatar = "✨" if msg["role"] == "assistant" else "🧑‍🎓"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

if len(st.session_state.messages) <= 1:
    st.markdown("**Try asking:**")
    suggestions = [
        "How do I prepare for exams in 1 week?",
        "I'm feeling overwhelmed with assignments",
        "Give me the best study techniques",
        "How can I improve my CGPA?",
    ]
    cols = st.columns(2)
    for i, s in enumerate(suggestions):
        if cols[i % 2].button(s, key=f"sug_{i}", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": s})
            with st.spinner("Thinking..."):
                reply = query_hf(s, st.session_state.messages[:-1])
            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.rerun()

if prompt := st.chat_input("Ask me anything about college life..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑‍🎓"):
        st.markdown(prompt)
    with st.chat_message("assistant", avatar="✨"):
        check = is_study_related(prompt)
        if check == False:
            reply = OFF_TOPIC_REPLY
        else:
            with st.spinner("Thinking..."):
                reply = query_hf(prompt, st.session_state.messages[:-1])
        st.markdown(reply)
    st.session_state.messages.append({"role": "assistant", "content": reply})