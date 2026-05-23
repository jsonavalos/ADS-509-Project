# app.py
import streamlit as st
from google.genai import types
# from agent import run_agent, client, MODEL_ID

st.title("FinOps Agent")

SUGGESTED_PROMPTS = [
    "Summarize last month's billing by service",
    "Forecast GCE spend for the next 30 days",
    "Find users with spend > $10k this week",
]

if "history" not in st.session_state:
    st.session_state.history = []      # list of types.Content (fed to agent)
    st.session_state.display = []      # list of plain dicts (for rendering)

for prompt in SUGGESTED_PROMPTS:
    if st.button(prompt):
        st.session_state.pending = prompt

for msg in st.session_state.display:
    st.chat_message(msg["role"]).write(msg["content"])

user_input = st.chat_input("Ask about your cloud costs...")

"""

# Handle both typed input and suggested prompt buttons
if user_input or st.session_state.get("pending"):
    user_input = user_input or st.session_state.pop("pending")

    st.session_state.display.append({"role": "user", "content": user_input})

    response_text = run_agent(user_input, st.session_state.history)

    # Update structured history for the agent (types.Content objects)
    st.session_state.history.append(
        types.Content(role="user", parts=[types.Part(text=user_input)])
    )
    st.session_state.history.append(
        types.Content(role="model", parts=[types.Part(text=response_text)])
    )

    st.session_state.display.append({"role": "assistant", "content": response_text})
    st.rerun()

"""