# agent.py
import os
import pandas as pd
from dotenv import load_dotenv
from google import genai
from google.cloud import bigquery

load_dotenv()

MODEL_ID = "gemini-2.5-flash"

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
BQ_DATASET = os.getenv("BQ_DATASET")
BQ_TABLE = os.getenv("BQ_TABLE")

gemini_client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
bq_client = bigquery.Client(project=GCP_PROJECT_ID)


SYSTEM_PROMPT = """
You are a Strategic Finance FinOps Agent for a class prototype.

You help finance and engineering users understand cloud cost trends using a BigQuery-hosted FOCUS-style cloud billing dataset.

Your responsibilities:
- Answer open-ended questions about cloud spend.
- Generate SQL queries for BigQuery when data is needed.
- Summarize results in business-friendly language.
- Identify cost drivers, anomalies, and potential governance risks.
- Recommend actions such as investigation, budget review, owner notification, or simulated access suspension.

Important constraints:
- Do not claim to suspend access unless an actual system integration exists.
- For governance actions, describe them as prototype/simulated unless explicitly connected to a real internal system.
- If the question is ambiguous, ask a clarifying question.
- If the dataset schema is unknown, use only known fields or ask for schema details.
- Keep responses concise, practical, and executive-ready.
"""


def run_bigquery(sql: str) -> pd.DataFrame:
    """Run a SQL query against BigQuery and return a dataframe."""
    query_job = bq_client.query(sql)
    return query_job.to_dataframe()


def get_table_schema() -> str:
    """Return the BigQuery table schema as text."""
    table_id = f"{GCP_PROJECT_ID}.{BQ_DATASET}.{BQ_TABLE}"
    table = bq_client.get_table(table_id)

    schema_lines = []
    for field in table.schema:
        schema_lines.append(f"- {field.name}: {field.field_type}")

    return "\n".join(schema_lines)


def ask_gemini(prompt: str) -> str:
    """Send a prompt to Gemini and return text."""
    response = gemini_client.models.generate_content(
        model=MODEL_ID,
        contents=prompt
    )
    return response.text


def generate_sql(user_input: str, schema: str) -> str:
    """Ask Gemini to generate BigQuery SQL for the user's FinOps question."""
    prompt = f"""
{SYSTEM_PROMPT}

You are generating BigQuery SQL for this table:

`{GCP_PROJECT_ID}.{BQ_DATASET}.{BQ_TABLE}`

Schema:
{schema}

User question:
{user_input}

Return only valid BigQuery SQL. Do not include markdown fences.
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

Write a concise FinOps answer using markdown. Use these EXACT section headers and formats:

### 🔍 Key Finding
One or two sentences summarizing the main insight.

### 💸 Cost Drivers & Risks
- Service Name: +USD X.XX (reason if known)
- Service Name: +USD X.XX (reason if known)

### ✅ Recommended Actions
1. Action one
2. Action two

### ⚠️ Caveats
Any data limitations or assumptions.

IMPORTANT:
- Never use dollar signs ($). Write "USD 36.00" instead of "$36.00".
- Use markdown headers (###) and bullet points (-) exactly as shown above.
- Do not wrap the response in code fences.
"""
    return ask_gemini(prompt)


def run_agent(user_input, history=None):
    """
    Main FinOps agent function called by Streamlit.
    Routes user questions to BigQuery and Gemini.
    """

    lower_input = user_input.lower()

    # Governance action guardrail
    if "suspend" in lower_input or "cut off" in lower_input or "disable access" in lower_input:
        return (
            "For this prototype, I can identify high-spend users or resources and draft a warning message, "
            "but I will treat access suspension as a simulated governance action unless a real internal access system is connected."
        )

    try:
        schema = get_table_schema()
        sql = generate_sql(user_input, schema)
        df = run_bigquery(sql)

        if df.empty:
            return (
                "I queried the BigQuery dataset, but the result returned no rows. "
                "Try broadening the time window, service, project, or cost threshold."
            )

        return summarize_results(user_input, sql, df)

    except Exception as e:
        return (
            "I was not able to complete the BigQuery-backed analysis yet.\n\n"
            f"Error: {e}\n\n"
            "This usually means the BigQuery project, dataset, table, credentials, or schema configuration needs to be updated."
        )