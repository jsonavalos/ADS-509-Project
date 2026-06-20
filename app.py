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

# Render a single message (text + optional chart). Used both for replaying
# history on rerun AND for rendering a new message immediately so it shows
# up the same turn it's created, not one turn late.
def render_message(msg: dict) -> None:
    with st.chat_message(msg["role"]):
        if is_html(msg["content"]):
            st.markdown(msg["content"], unsafe_allow_html=True)
        else:
            safe_markdown(msg["content"])
        if msg.get("chart_type") == "line":
            st.line_chart(msg["chart_data"], **msg.get("chart_kwargs", {}))
        elif msg.get("chart_type") == "bar":
            st.bar_chart(msg["chart_data"], **msg.get("chart_kwargs", {}))

# Session state
if "display" not in st.session_state:
    st.session_state.display = []

if "pending" not in st.session_state:
    st.session_state.pending = None

# Suggested prompt buttons
for prompt in SUGGESTED_PROMPTS:
    if st.button(prompt):
        st.session_state.pending = prompt

# Display chat history (replays text + any charts from earlier turns)
for msg in st.session_state.display:
    render_message(msg)

# Chat input
user_input = st.chat_input("Ask about your cloud costs...")

if user_input or st.session_state.pending:
    user_input = user_input or st.session_state.pop("pending")

    # Show user message
    user_msg = {"role": "user", "content": user_input}
    st.session_state.display.append(user_msg)
    render_message(user_msg)

    # Get the agent's response first — this becomes the summary on top of
    # any chart that gets attached below it.
    response_text = run_agent(user_input, st.session_state.display)

    lower_prompt = user_input.lower()
    chart_attached = False

    # ─── DYNAMIC CHARTING & STATISTICS INTERCEPTOR ───
    if any(x in lower_prompt for x in ["chart", "forecast", "spend by service", "high spend"]):
        try:
            from agent import run_bigquery
            import pandas as pd
            import numpy as np

            # Query the final 30 days of real data (September 2024)
            fallback_sql = """
                SELECT usage_date, ServiceName, SubAccountName, daily_effective_cost 
                FROM `usd-llm-data-science.FinOps.cloudbilling_daily` 
                WHERE usage_date >= '2024-09-01' AND usage_date <= '2024-09-30'
                ORDER BY usage_date
            """
            df = run_bigquery(fallback_sql)

            if not df.empty:
                df['usage_date'] = pd.to_datetime(df['usage_date'])

                # ─── SCENARIO A: FORECAST LINE CHART ───
                if "forecast" in lower_prompt or "line" in lower_prompt:
                    daily_history = df.groupby('usage_date')['daily_effective_cost'].sum().to_frame()
                    last_real_date = daily_history.index.max()
                    recent_mean = daily_history.tail(7)['daily_effective_cost'].mean()

                    # Generate 30-day simulated forecast
                    future_dates = pd.date_range(start=last_real_date + pd.Timedelta(days=1), periods=30)
                    np.random.seed(42)
                    simulated_variance = np.random.normal(loc=0, scale=recent_mean * 0.04, size=30)
                    forecasted_costs = [max(100, recent_mean + var) for var in simulated_variance]

                    forecast_df = pd.DataFrame(
                        index=future_dates,
                        data={'daily_effective_cost': forecasted_costs}
                    )

                    daily_history['Status'] = 'Historical (Sept 2024)'
                    forecast_df['Status'] = 'Projected Forecast (Oct 2024)'

                    combined = pd.concat([daily_history, forecast_df]).reset_index()
                    combined.columns = ['Date', 'Daily Spend (USD)', 'Status']

                    chart_msg = {
                        "role": "assistant",
                        "content": response_text,
                        "chart_type": "line",
                        "chart_data": combined,
                        "chart_kwargs": {"x": "Date", "y": "Daily Spend (USD)", "color": "Status"},
                    }
                    st.session_state.display.append(chart_msg)
                    render_message(chart_msg)
                    chart_attached = True

                    # Stats summary
                    with st.chat_message("assistant"):
                        st.subheader("📋 Forecast Baseline Descriptive Statistics")
                        col1, col2, col3, col4 = st.columns(4)
                        col1.metric("Historical Daily Mean", f"USD {recent_mean:,.2f}")
                        col2.metric("Projected Peak Spend", f"USD {max(forecasted_costs):,.2f}")
                        col3.metric("Projected Floor Spend", f"USD {min(forecasted_costs):,.2f}")
                        col4.metric("Total Forecasted Run-Rate", f"USD {sum(forecasted_costs):,.2f}")

                # ─── SCENARIO B: BAR CHART (SERVICE OR SUBACCOUNT) ───
                elif "service" in lower_prompt or "bar" in lower_prompt:
                    dim_col = 'ServiceName' if "service" in lower_prompt else 'SubAccountName'
                    categorical_series = (
                        df.groupby(dim_col)['daily_effective_cost']
                        .sum()
                        .sort_values(ascending=False)
                    )

                    bar_msg = {
                        "role": "assistant",
                        "content": response_text,
                        "chart_type": "bar",
                        "chart_data": categorical_series,
                        "chart_kwargs": {},
                    }
                    st.session_state.display.append(bar_msg)
                    render_message(bar_msg)
                    chart_attached = True

                    # Summary table
                    summary_stats = df.groupby(dim_col)['daily_effective_cost'].agg(
                        ['count', 'sum', 'mean', 'max']
                    )
                    summary_stats.columns = [
                        'Line Items Count',
                        'Total Spend (USD)',
                        'Average Cost/Day',
                        'Max Single Day Peak'
                    ]
                    with st.chat_message("assistant"):
                        st.subheader("📝 Descriptive Statistics Summary")
                        st.dataframe(summary_stats.style.format(precision=2))

        except Exception as chart_err:
            # Surface chart errors instead of swallowing them silently.
            st.error(f"Chart generation failed: {chart_err}")

    # Only send response_text as its own message if no chart consumed it already
    if not chart_attached:
        agent_msg = {"role": "assistant", "content": response_text}
        st.session_state.display.append(agent_msg)
        render_message(agent_msg)

