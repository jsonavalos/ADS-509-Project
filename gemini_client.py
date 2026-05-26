import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from tools.bq_tool import BigQueryClient

load_dotenv()  # Loads variables from .env

# Use Gemini 2.5 Flash for the best Free Tier experience
MODEL_ID = "gemini-2.5-flash"

# --- Define your schema, reuse everywhere ---
CONTEXT_SCHEMA = """
You have access to a Google Cloud Billing BigQuery dataset following the FOCUS (FinOps Open Cost and Usage Specification) standard.

TABLE: `FinOps.focus_sample`

COLUMNS:
| Column Name                  | Type      | Description |
|------------------------------|-----------|-------------|
| AvailabilityZone             | STRING    | Availability zone where the resource was deployed |
| BilledCost                   | FLOAT     | Actual billed cost for the charge |
| BillingAccountId             | STRING    | ID of the billing account |
| BillingAccountName           | STRING    | Human-readable name of the billing account |
| BillingCurrency              | STRING    | Currency code for all cost columns (e.g., 'USD') |
| BillingPeriodEnd             | TIMESTAMP | End of the billing period |
| BillingPeriodStart           | TIMESTAMP | Start of the billing period |
| ChargeCategory               | STRING    | High-level category of the charge (e.g., 'Usage', 'Tax', 'Credit') |
| ChargeClass                  | STRING    | Classification of the charge (e.g., 'Correction') |
| ChargeDescription            | STRING    | Human-readable description of the charge |
| ChargeFrequency              | STRING    | How often the charge recurs (e.g., 'One-Time', 'Recurring', 'Usage-Based') |
| ChargePeriodEnd              | TIMESTAMP | End of the charge period |
| ChargePeriodStart            | TIMESTAMP | Start of the charge period |
| CommitmentDiscountCategory   | STRING    | Category of commitment discount (e.g., 'Spend', 'Usage') |
| CommitmentDiscountId         | STRING    | ID of the commitment discount (e.g., CUD, SUD) |
| CommitmentDiscountName       | STRING    | Name of the commitment discount |
| CommitmentDiscountStatus     | STRING    | Whether usage was covered by a commitment ('Used', 'Unused') |
| CommitmentDiscountType       | STRING    | Type of commitment (e.g., 'Committed Use Discount') |
| ConsumedQuantity             | STRING    | Actual quantity of resource consumed |
| ConsumedUnit                 | STRING    | Unit for ConsumedQuantity (e.g., 'hours', 'GB') |
| ContractedCost               | STRING    | Cost based on contracted rates |
| ContractedUnitPrice          | STRING    | Contracted unit price before discounts |
| EffectiveCost                | FLOAT     | Cost after all discounts and credits are applied |
| InvoiceIssuerName            | STRING    | Name of the entity issuing the invoice (e.g., 'Google') |
| ListCost                     | FLOAT     | Cost at public list/on-demand price |
| ListUnitPrice                | STRING    | Public list price per unit |
| PricingCategory              | STRING    | How the charge was priced (e.g., 'On-Demand', 'Committed') |
| PricingQuantity              | FLOAT     | Quantity used for pricing calculation |
| PricingUnit                  | STRING    | Unit used for pricing (e.g., 'hour', 'GB-month') |
| ProviderName                 | STRING    | Cloud provider name (e.g., 'Google') |
| PublisherName                | STRING    | Publisher of the service |
| RegionId                     | STRING    | Machine-readable region ID (e.g., 'us-central1') |
| RegionName                   | STRING    | Human-readable region name |
| ResourceId                   | STRING    | Unique identifier for the resource |
| ResourceName                 | STRING    | Human-readable name of the resource |
| ResourceType                 | STRING    | Type of resource (e.g., 'Compute Instance', 'Storage Bucket') |
| ServiceCategory              | STRING    | High-level service category (e.g., 'Compute', 'Storage', 'AI and Machine Learning') |
| Id                           | INTEGER   | Unique row identifier |
| ServiceName                  | STRING    | Name of the cloud service (e.g., 'Cloud Run', 'BigQuery') |
| SkuId                        | STRING    | Unique SKU identifier |
| SkuPriceId                   | STRING    | Unique identifier for the SKU price |
| SubAccountId                 | STRING    | Sub-account or project ID |
| SubAccountName               | STRING    | Sub-account or project name |
| Tags                         | STRING    | Resource tags/labels as a serialized string |

IMPORTANT QUERY RULES:
- All cost columns (BilledCost, EffectiveCost, ListCost) are FLOAT — use ROUND(..., 2) for display
- ConsumedQuantity, ContractedCost, ContractedUnitPrice, ListUnitPrice are STRING — CAST to FLOAT if doing math: CAST(ConsumedQuantity AS FLOAT64)
- Use ChargePeriodStart / ChargePeriodEnd (not BillingPeriodStart) for usage-level time filtering
- Use TIMESTAMP_TRUNC(ChargePeriodStart, MONTH) for monthly grouping
- Filter time ranges with: WHERE ChargePeriodStart >= TIMESTAMP('YYYY-MM-DD')
- Tags is a flat STRING — use JSON_EXTRACT or LIKE to filter: WHERE Tags LIKE '%"env":"prod"%'
- For net cost after discounts, prefer EffectiveCost over BilledCost
- For commitment discount analysis, filter: WHERE CommitmentDiscountId IS NOT NULL
- Use IFNULL(BilledCost, 0) and IFNULL(ServiceName, 'Unknown') to handle NULLs
- Group by SubAccountName or SubAccountId to break down costs by project
- FOCUS schema uses PascalCase column names — do not use snake_case equivalents
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

        Return ONLY the raw SQL query. No markdown, no code fences, no explanations.
        """
        try:
            response = self.client.models.generate_content(
            model=MODEL_ID,
            contents=sql_prompt,
            config=self._base_config,
            #config=types.GenerateContentConfig(
            #    temperature=0.0,  # Deterministic output for code generation
            #    )
            )
            return response.text.strip()
        except Exception as e:
            return f"Error generating SQL: {str(e)}"
        



######################### TESTING / EXAMPLE USAGE BELOW #########################
gemini_client =GeminiClient()
#print(gemini_client.ask("Where are Meta data stored in BigQuery?"))
#print(gemini_client.convert_prompt_to_sql('What is the service that has exceeded $10k in spend this week?'))

bq_client = BigQueryClient()
sql_query = gemini_client.convert_prompt_to_sql('What are the services that we use in the company?')
print(sql_query)
print("Resulting SQL Query: (What are the services that we use in the company?)")
print(bq_client.run_query(sql_query))