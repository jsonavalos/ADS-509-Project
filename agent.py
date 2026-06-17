# agent.py
import os
import pandas as pd
from dotenv import load_dotenv
from google import genai
from google.cloud import bigquery
from google.oauth2 import service_account
import google.auth
import streamlit as st
import html2text

# Import your email sending tool
from tools.mailing_tool import send_email

load_dotenv()

MODEL_ID = "gemini-2.5-flash"

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
BQ_DATASET = os.getenv("BQ_DATASET")
BQ_TABLE = os.getenv("BQ_TABLE")


# ───────────────────────────────────────────────
# BIGQUERY CREDENTIALS
# ───────────────────────────────────────────────
def get_bq_credentials():
    try:
        service_acct = st.secrets["gcp_service_account"]
        return service_account.Credentials.from_service_account_info(service_acct)
    except Exception:
        creds, _ = google.auth.default()
        return creds


bq_client = bigquery.Client(
    project=GCP_PROJECT_ID,
    credentials=get_bq_credentials()
)

gemini_client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))


# ───────────────────────────────────────────────
# SYSTEM PROMPT
# ───────────────────────────────────────────────
SYSTEM_PROMPT = """
You are a Strategic Finance FinOps Agent for a class prototype.
You help finance and engineering users understand cloud cost trends using a BigQuery-hosted FOCUS-style cloud billing dataset.

Data Availability Limitations:
- The dataset ONLY contains cloud billing records from March 20, 2024 to September 30, 2024.
- The "most recent month" or latest available data in this dataset is September 2024.

Your responsibilities:
- Answer open-ended questions about cloud spend.
- Generate SQL queries for BigQuery when data is needed.
- Summarize results in business-friendly language.
- Identify cost drivers, anomalies, and governance risks.
- Recommend actions such as investigation, budget review, owner notification, or simulated access suspension.

Constraints:
- Do not claim to suspend access unless a real integration exists.
- For governance actions, describe them as prototype/simulated.
- If the question is ambiguous, ask a clarifying question.
- If the dataset schema is unknown, ask for schema details.
- Keep responses concise, practical, and executive-ready.
"""


# ───────────────────────────────────────────────
# GEMINI HELPERS
# ───────────────────────────────────────────────
def ask_gemini(prompt: str) -> str:
    response = gemini_client.models.generate_content(
        model=MODEL_ID,
        contents=prompt
    )
    return response.text


# ───────────────────────────────────────────────
# EMAIL TEMPLATE GENERATOR
# ───────────────────────────────────────────────
def generate_email_template(user_input: str) -> str:
    prompt = f"""
You are a professional assistant. The user is asking for an email draft:

\"\"\"{user_input}\"\"\"

Return a clean, professional email template as a COMPLETE HTML document.

STRICT RULES:
- Output HTML ONLY. No explanations, no comments, no markdown.
- The ENTIRE response must be a single, valid HTML document:
  - Starts with <html> and ends with </html>
  - Contains <head> with <meta charset="UTF-8"> and a <title>
  - Contains <body> with all visible content
- Use simple inline styles.
- Include greeting, context, body, and closing.
- Address the recipient as: Dear [Name],
- Use 'USD 1,234' instead of '$1,234'.
- Do NOT include placeholders for subject, From, or To.
- Do NOT output anything outside the HTML tags.

Return ONLY the HTML document.
"""
    return ask_gemini(prompt)


# ───────────────────────────────────────────────
# STRICT FORMAT RECIPIENT EXTRACTION
# ───────────────────────────────────────────────
def extract_recipient(text):
    """
    Strict format:
    Name: John Doe, Email: john@example.com
    """
    try:
        parts = text.split(",")
        name = parts[0].split(":", 1)[1].strip()
        email = parts[1].split(":", 1)[1].strip()
        return name, email
    except:
        return None, None


# ───────────────────────────────────────────────
# BIGQUERY HELPERS
# ───────────────────────────────────────────────
def run_bigquery(sql: str) -> pd.DataFrame:
    query_job = bq_client.query(sql)
    return query_job.to_dataframe()


def get_table_schema() -> str:
    table_id = f"{GCP_PROJECT_ID}.{BQ_DATASET}.{BQ_TABLE}"
    table = bq_client.get_table(table_id)

    schema_lines = [f"- {field.name}: {field.field_type}" for field in table.schema]
    return "\n".join(schema_lines)


def generate_sql(user_input: str, schema: str) -> str:
    prompt = f"""
{SYSTEM_PROMPT}

You are generating BigQuery SQL for this table:

`{GCP_PROJECT_ID}.{BQ_DATASET}.{BQ_TABLE}`

Schema:
{schema}

User question:
{user_input}

Return only valid BigQuery SQL. No markdown fences.
"""
    sql = ask_gemini(prompt)
    return sql.replace("```sql", "").replace("```", "").strip()


def summarize_results(user_input: str, sql: str, df: pd.DataFrame) -> str:
    preview = df.head(20).to_string(index=False)

    prompt = f"""
{SYSTEM_PROMPT}

User question:
{user_input}

SQL used:
{sql}

Query result preview:
{preview}

Write a concise FinOps answer using markdown with these exact sections:

### 🔍 Key Finding
### 💸 Cost Drivers & Risks
### ✅ Recommended Actions
### ⚠️ Caveats

Rules:
- Never use $ signs. Use "USD 36.00".
- No code fences.
"""
    return ask_gemini(prompt)

def html_to_markdown(html: str) -> str:
    return html2text.html2text(html)

# ───────────────────────────────────────────────
# MAIN AGENT LOGIC (WITH APPROVAL LOOP)
# ───────────────────────────────────────────────
def run_agent(user_input, history=None):

    # Initialize approval state
    if "email_draft" not in st.session_state:
        st.session_state.email_draft = None

    if "awaiting_approval" not in st.session_state:
        st.session_state.awaiting_approval = False

    if "awaiting_recipient" not in st.session_state:
        st.session_state.awaiting_recipient = False

    if "pending_email_prompt" not in st.session_state:
        st.session_state.pending_email_prompt = None

    lower_input = user_input.lower()

    # ───────────────────────────────────────────────
    # STEP 1 — Detect Email Draft Intent
    # ───────────────────────────────────────────────
    if any(x in lower_input for x in [
        "draft an email",
        "write an email",
        "email draft",
        "draft a reply",
        "compose an email",
        "warning email",
        "draft message"
    ]):
        st.session_state.awaiting_recipient = True
        st.session_state.pending_email_prompt = user_input

        return (
            "I can draft that email. Please provide the recipient details in this exact format:\n\n"
            "Name: John Doe, Email: john@example.com"
        )

    # ───────────────────────────────────────────────
    # STEP 2 — Detect Name + Email Provided (Strict Format)
    # ───────────────────────────────────────────────
    if st.session_state.get("awaiting_recipient", False):

        lower_text = user_input.lower()

        if "name:" not in lower_text or "email:" not in lower_text:
            return (
                "I still need the recipient details.\n\n"
                "Please provide them in this exact format:\n"
                "Name: John Doe, Email: john@example.com"
            )

        name, email = extract_recipient(user_input)

        if not (name and email):
            return (
                "I could not parse the name and email.\n\n"
                "Please provide them in this exact format:\n"
                "Name: John Doe, Email: john@example.com"
            )

        # Generate draft (but do NOT send yet)
        st.session_state.awaiting_recipient = False
        original_prompt = st.session_state.pending_email_prompt
        st.session_state.pending_email_prompt = None

        html_email = generate_email_template(original_prompt)
        html_email = html_email.replace("[Name]", name)

        # Store draft + approval state
        st.session_state.email_draft = html_email
        st.session_state.awaiting_approval = True
        st.session_state.recipient_email = email
        st.session_state.recipient_name = name

        return (
            f"Here is the drafted email for {name} ({email}):\n\n"
            f"{html_to_markdown(html_email)}\n\n"
            "Would you like to **approve**, **revise**, or **cancel**?"
        )

    # ───────────────────────────────────────────────
    # STEP 3 — Approval Loop
    # ───────────────────────────────────────────────
    if st.session_state.get("awaiting_approval", False):

        lower = user_input.lower()

        # APPROVE → send email
        if "approve" in lower or "send" in lower:
            try:
                send_email(
                    to=st.session_state.recipient_email,
                    subject="[FinOps] Notification",
                    body=st.session_state.email_draft
                )
                msg = f"✓ Email sent to {st.session_state.recipient_email}."
            except Exception as e:
                msg = f"⚠️ Failed to send email: {e}"

            # Reset state
            st.session_state.awaiting_approval = False
            st.session_state.email_draft = None
            return msg

        # REVISE → regenerate draft
        if "revise" in lower or "change" in lower or "edit" in lower:
            revised = generate_email_template(user_input)
            revised = revised.replace("[Name]", st.session_state.recipient_name)
            st.session_state.email_draft = revised

            return (
                "Here is the revised draft:\n\n"
                f"{html_to_markdown(revised)}\n\n"
                "Approve, revise again, or cancel."
            )

        # CANCEL
        if "cancel" in lower:
            st.session_state.awaiting_approval = False
            st.session_state.email_draft = None
            return "Email drafting canceled."

        # Invalid input
        return "Please say **approve**, **revise**, or **cancel**."

    # ───────────────────────────────────────────────
    # NORMAL FINOPS SQL + SUMMARY FLOW
    # ───────────────────────────────────────────────
    try:
        schema = get_table_schema()
        sql = generate_sql(user_input, schema)

        if not (sql.strip().upper().startswith("SELECT") or sql.strip().upper().startswith("WITH")):
            return sql

        df = run_bigquery(sql)

        if df.empty:
            return (
                "I queried the BigQuery dataset, but the result returned no rows. "
                "Try broadening the time window, service, project, or cost threshold."
            )

        return summarize_results(user_input, sql, df)

    except Exception as e:
        return (
            "I was not able to complete the BigQuery-backed analysis.\n\n"
            f"Error: {e}\n\n"
            "This usually means the BigQuery project, dataset, table, credentials, or schema configuration needs to be updated."
        )
