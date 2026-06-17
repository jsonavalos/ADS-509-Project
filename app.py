import streamlit as st
from agent import run_agent
import re

st.set_page_config(page_title="FinOps Agent", page_icon="💸", layout="wide")

st.title("FinOps Agent")

SUGGESTED_PROMPTS = [
    "Summarize cloud spend by service for the most recent month",
    "Identify the top cost drivers and explain what changed",
    "Forecast total cloud spend for the next 30 days in a line chart",
    "Find projects, services, or users with unusually high spend and list them in a bar chart",
    "Create an executive FinOps summary with risks and recommendations",
    "Draft a warning email for owners of high-spend resources"
]

# Escape markdown for normal text
def safe_markdown(text: str) -> None:
    escaped = text.replace("$", r"\$")
    st.markdown(escaped)

# Detect if content is HTML
def is_html(text: str) -> bool:
    return bool(re.search(r"<[a-z][\s\S]*>", text, re.I))

# Session state
if "display" not in st.session_state:
    st.session_state.display = []

if "pending" not in st.session_state:
    st.session_state.pending = None

# Suggested prompt buttons
for prompt in SUGGESTED_PROMPTS:
    if st.button(prompt):
        st.session_state.pending = prompt

# Display chat history
for msg in st.session_state.display:
    with st.chat_message(msg["role"]):
        if is_html(msg["content"]):
            st.markdown(msg["content"], unsafe_allow_html=True)
        else:
            safe_markdown(msg["content"])

# Chat input
user_input = st.chat_input("Ask about your cloud costs...")

if user_input or st.session_state.pending:
    user_input = user_input or st.session_state.pop("pending")

    # Show user message
    st.session_state.display.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        safe_markdown(user_input)

    # Run agent
    response_text = run_agent(user_input, st.session_state.display)

    # Store assistant message
    st.session_state.display.append({"role": "assistant", "content": response_text})

    # Render assistant message
    with st.chat_message("assistant"):
        if "<" in response_text and ">" in response_text:
            st.markdown(response_text, unsafe_allow_html=True)
        else:
            safe_markdown(response_text)

