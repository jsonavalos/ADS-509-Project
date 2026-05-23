# Proof of concept to connect to database!

import os
from dotenv import load_dotenv
from google import genai
from google.cloud import bigquery

load_dotenv()

class BigQueryClient:
    def __init__(self):
        self.client = bigquery.Client(project=os.environ.get("GCP_PROJECT_ID"))

    def run_query(self, sql: str):
        try:
            query_job = self.client.query(sql)
            results = query_job.result()
            return [dict(row) for row in results]
        except Exception as e:
            return f"Error running query: {str(e)}"


bigquery_client = BigQueryClient()
print(bigquery_client.run_query("SELECT * FROM `FinOps.focus_sample` LIMIT 10;"))
