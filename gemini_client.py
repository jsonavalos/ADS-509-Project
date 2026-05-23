import os
import pandas as pd
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()  # Loads variables from .env

# Use Gemini 2.5 Flash for the best Free Tier experience
MODEL_ID = "gemini-2.5-flash"

# --- Define your schema, reuse everywhere ---
CONTEXT_SCHEMA = """
You have access to a Google Cloud Billing BigQuery dataset with the following structure:

TABLE: `project_id.dataset_id.gcp_billing_export_v1`

COLUMNS:
| Column Name                        | Type      | Description |
|------------------------------------|-----------|-------------|
| billing_account_id                 | STRING    | The billing account the usage is associated with |
| service.id                         | STRING    | ID of the Google Cloud service |
| service.description                | STRING    | Human-readable name of the service (e.g., 'BigQuery', 'Compute Engine') |
| sku.id                             | STRING    | ID of the resource used |
| sku.description                    | STRING    | Description of the SKU |
| usage_start_time                   | TIMESTAMP | Start time of the usage period |
| usage_end_time                     | TIMESTAMP | End time of the usage period |
| project.id                         | STRING    | GCP project ID |
| project.name                       | STRING    | GCP project name |
| project.labels                     | RECORD[]  | Labels attached to the project (key/value pairs) |
| labels                             | RECORD[]  | Labels on the resource (key/value pairs) |
| system_labels                      | RECORD[]  | System-generated labels |
| location.location                  | STRING    | Location of the resource |
| location.country                   | STRING    | Country (e.g., 'US') |
| location.region                    | STRING    | Region (e.g., 'us-central1') |
| location.zone                      | STRING    | Zone (e.g., 'us-central1-a') |
| cost                               | FLOAT64   | Cost of the usage before credits |
| currency                           | STRING    | Currency code (e.g., 'USD') |
| currency_conversion_rate           | FLOAT64   | Conversion rate to USD |
| usage.amount                       | FLOAT64   | Amount of usage |
| usage.unit                         | STRING    | Unit of usage (e.g., 'byte-seconds', 'requests') |
| usage.amount_in_pricing_units      | FLOAT64   | Usage amount in pricing units |
| usage.pricing_unit                 | STRING    | Pricing unit |
| credits                            | RECORD[]  | Credits applied (name, amount, type, id) |
| invoice.month                      | STRING    | Invoice month in YYYYMM format |
| cost_type                          | STRING    | Type of cost: 'regular', 'tax', 'adjustment', 'rounding_error' |
| adjustment_info                    | RECORD    | Info about adjustments if cost_type is 'adjustment' |

IMPORTANT QUERY RULES:
- Always use `TIMESTAMP_TRUNC()` for date grouping, not `DATE()` on TIMESTAMP fields
- Access nested fields with dot notation: `project.id`, `service.description`
- For labels, use: `(SELECT value FROM UNNEST(labels) WHERE key = 'env')` 
- Total cost including credits: `SUM(cost) + SUM(IFNULL((SELECT SUM(c.amount) FROM UNNEST(credits) c), 0))`
- Always include a `WHERE usage_start_time >= TIMESTAMP('YYYY-MM-DD')` to limit scan costs
- Use `ROUND(SUM(cost), 2)` for monetary values
- Remove Null values with `IFNULL(field, 0)` or `IFNULL(field, 'Unknown')`
"""

class GeminiClient:
    def __init__(self, model_id=MODEL_ID, schema: str = CONTEXT_SCHEMA):
        self.client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
        self.model_id = model_id
        self.schema = schema

        # System instruction applied to ALL calls automatically
        self._base_config = types.GenerateContentConfig(
            system_instruction=self.schema,
            temperature=0.0,
        )

    def ask(self, question: str) -> str:
        """Ask Gemini a simple question and get a plain text answer."""
        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=question
            )
            # Check if the response was blocked or empty
            return response.text if response.text else "No response generated (check safety settings)."
        except Exception as e:
            return f"Error: {str(e)}"
    
    def convert_prompt_to_sql(self, prompt: str) -> str:
        """Convert a natural language prompt into a SQL query."""
        sql_prompt = f"""
        Convert the following natural language request into a SQL query that can be run against a BigQuery dataset containing cloud billing data:

        Request: {prompt}

        The SQL should be syntactically correct and only include the query itself, without any explanatory text.
        """
        try:
            response = self.client.models.generate_content(
            model=MODEL_ID,
            contents=sql_prompt,
            config=types.GenerateContentConfig(
                temperature=0.0,  # Deterministic output for code generation
                )
            )
            return response.text.strip()
        except Exception as e:
            return f"Error generating SQL: {str(e)}"




gemini_client =GeminiClient()
#print(gemini_client.ask("Where are Meta data stored in BigQuery?"))
print(gemini_client.convert_prompt_to_sql('I would like to get all the column names in my database'))
