import os
import pandas as pd
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()  # Loads variables from .env

# Initialize Client
client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))

# Use Gemini 2.5 Flash for the best Free Tier experience
MODEL_ID = "gemini-2.5-flash"

def ask(question: str) -> str:
    """Ask Gemini a simple question and get a plain text answer."""
    try:
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=question
        )
        # Check if the response was blocked or empty
        return response.text if response.text else "No response generated (check safety settings)."
    except Exception as e:
        return f"Error: {str(e)}"


def analyze_dataframe(df: pd.DataFrame, question: str) -> str:
    """Send a dataset summary + question to Gemini."""
    # Using to_markdown() often helps LLMs parse data better than to_string()
    data_summary = df.describe().to_markdown()
    sample = df.head(10).to_markdown()

    prompt = f"""
    You are a data scientist assistant. Here is a dataset summary:

    ### STATISTICS:
    {data_summary}

    ### SAMPLE ROWS:
    {sample}

    ### QUESTION: 
    {question}

    Provide a clear, concise data science interpretation.
    """

    try:
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2, # Lower temperature for more factual data analysis
            )
        )
        return response.text
    except Exception as e:
        return f"Analysis failed: {str(e)}"


def generate_report(df: pd.DataFrame) -> str:
    """Auto-generate a business analytics report."""
    return analyze_dataframe(
        df,
        "Generate a professional business analytics report with key insights, trends, and recommendations."
    )


# --- Simple Q&A demo ---
if __name__ == "__main__":
    print(f"--- Gemini Free Tier Client ({MODEL_ID}) ---")
    print("Type 'exit' to quit\n")
    
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("exit", "quit"):
            print("Goodbye!")
            break
        if not user_input:
            continue
            
        print("Gemini is thinking...")
        answer = ask(user_input)
        print(f"\nGemini: {answer}\n")
        print("-" * 30)