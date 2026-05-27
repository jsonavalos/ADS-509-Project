# agent.py

def run_agent(user_input, history=None):
    """
    Temporary FinOps agent backend.

    This placeholder confirms that the Streamlit UI can call a separate
    agent function. Later, this function can route requests to Gemini,
    BigQuery, forecasting logic, or governance checks.
    """

    user_input_lower = user_input.lower()

    if "summarize" in user_input_lower or "billing" in user_input_lower:
        return (
            "I can summarize billing by service. "
            "Next, we will connect this to billing data and return service-level spend trends."
        )

    if "forecast" in user_input_lower:
        return (
            "I can forecast cloud spend. "
            "Next, we will connect this to historical spend data and produce a 30-day forecast."
        )

    if "spend" in user_input_lower or "$10k" in user_input_lower:
        return (
            "I can identify high-spend users or cost centers. "
            "Next, we will connect this to usage data and flag users above the selected threshold."
        )

    return (
        f"FinOps agent received your question: {user_input}\n\n"
        "Next, we will connect this prompt to the real agent workflow."
    )