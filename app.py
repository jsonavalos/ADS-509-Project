# app.py
import streamlit as st
from agent import run_agent

st.set_page_config(page_title="FinOps Agent", page_icon="💸", layout="wide")

st.title("FinOps Agent")

SUGGESTED_PROMPTS = [
    "Summarize cloud spend by service for the most recent month",
    "Identify the top cost drivers and explain what changed",
    "Forecast total cloud spend for the next 30 days",
    "Find projects, services, or users with unusually high spend",
    "Create an executive FinOps summary with risks and recommendations",
    "Draft a warning email for owners of high-spend resources"
]

if "display" not in st.session_state:
    st.session_state.display = []

if "pending" not in st.session_state:
    st.session_state.pending = None

for prompt in SUGGESTED_PROMPTS:
    if st.button(prompt):
        st.session_state.pending = prompt

for msg in st.session_state.display:
    st.chat_message(msg["role"]).write(msg["content"])

user_input = st.chat_input("Ask about your cloud costs...")

if user_input or st.session_state.pending:
    user_input = user_input or st.session_state.pop("pending")

    st.session_state.display.append({"role": "user", "content": user_input})
    st.chat_message("user").write(user_input)

    response_text = run_agent(user_input, st.session_state.display)

    st.session_state.display.append({"role": "assistant", "content": response_text})
    st.chat_message("assistant").write(response_text)