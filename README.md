# FinOps Agent

![Streamlit](https://img.shields.io/badge/Streamlit-App-red?logo=streamlit)
![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![BigQuery](https://img.shields.io/badge/BigQuery-Enabled-669DF6?logo=google-cloud)
![Gemini](https://img.shields.io/badge/Gemini-2.5_Flash-8A2BE2?logo=google)
![SMTP](https://img.shields.io/badge/Email-SMTP-green)
![License](https://img.shields.io/badge/License-MIT-black)

---

## 📌 Overview

The **FinOps Agent** is an interactive Streamlit application that helps finance and engineering teams explore cloud-spend data, generate insights, and automate cost-governance communication.

It integrates:

- Google BigQuery for FOCUS-style billing analytics
- Gemini 2.5 Flash for natural-language SQL generation
- A multi-turn email approval workflow
- SMTP email delivery
- Markdown previews of HTML emails for clean rendering in Streamlit

The agent supports multi-turn conversations, cost-analysis queries, and automated communication workflows.

---

## ✨ Features

**FinOps Intelligence**
- Natural-language cloud cost queries
- Automatic SQL generation for BigQuery
- Executive-ready summaries
- Anomaly detection
- Cost-driver analysis

**Email Workflow**
- Draft → Preview → Revise → Approve → Send
- Markdown preview for clean rendering
- Sends actual HTML via SMTP
- Strict recipient validation
- Unlimited revision loop

**Streamlit UI**
- Chat-style interface
- Suggested prompts
- Multi-message responses
- Session-aware conversation

---

## 📁 Project Structure

```
.
├── app.py                 # Streamlit UI
├── agent.py               # Core agent logic + approval loop
├── tools/
│   └── mailing_tool.py    # SMTP email sender
├── requirements.txt
├── README.md
└── .env                    # API keys + config
```

---

## ⚙️ Requirements

- Python 3.10+
- Google Cloud project with BigQuery enabled
- Gemini API key
- SMTP credentials
- Streamlit


Create and activate a Python 3 virtual environment:
 
```bash
python3 -m venv venv
```
 
On macOS/Linux:
 
```bash
source venv/bin/activate
```
 
On Windows:
 
```bash
venv\Scripts\activate
```
 
Install dependencies:
 
```bash
pip install -r requirements.txt
```
 
When you're done working, deactivate the environment with:
 
```bash
deactivate
```

---

## 🔧 Environment Variables

Create a `.env` file:

```
GOOGLE_API_KEY=your_key
GCP_PROJECT_ID=your_project
BQ_DATASET=your_dataset
BQ_TABLE=your_table
SENDER_EMAIL=your_email
APP_PASSWORD=your_app_password
```

If using a service account, add the credentials to `.streamlit/secrets.toml`.

### Getting a Gemini API Key (GOOGLE_API_KEY)
 
1. Go to [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) and sign in with your Google account
2. Accept the Terms of Service if prompted
3. Click **Create API key**
4. Choose to create the key in a new Google Cloud project, or select an existing project
5. Copy the generated key (it starts with `AIza`) into `GOOGLE_API_KEY` in your `.env` file

### Setting up SENDER_EMAIL and APP_PASSWORD
 
`SENDER_EMAIL` is the Gmail address the agent sends from. `APP_PASSWORD` is a Google App Password generated for that account, used in place of your regular Gmail password for SMTP authentication.

To generate an `APP_PASSWORD`:
 
1. Go to your [Google Account Settings](https://myaccount.google.com/)
2. Select **Security** on the left menu
3. Ensure **2-Step Verification** is turned on (required)
4. Click **2-Step Verification**, scroll to the bottom, and select **App passwords**
5. Type an app name (e.g., "Python Script") and click **Create**
6. Copy the 16-character code displayed on your screen into `APP_PASSWORD` in your `.env` file
---

## 🚀 Running the App

```bash
streamlit run app.py
```

---

## 💬 Email Approval Workflow

1. User asks: "Draft a warning email for high-spend resources."
2. Agent requests recipient details, e.g. `Name: John Doe, Email: john@example.com`.
3. Agent generates a Markdown preview (for display) and an HTML version (stored for sending).
4. User can respond with "Revise," "Change tone to sassy," "Shorten it," or "Approve."
5. On approval, the agent sends the actual HTML email via SMTP.

---

## 🧠 FinOps Query Examples

Try prompts like:

- Summarize cloud spend by service for the most recent month
- Identify top cost drivers and explain what changed
- Find anomalous spend in September
- Create an executive summary with risks and recommendations
- Draft a warning email for owners of high-spend resources

---

## 🔍 Key Components

**Agent Logic** (`agent.py`) — handles email drafting, the revision loop, approval flow, BigQuery SQL generation, and FinOps summarization.

**Streamlit UI** (`app.py`) — handles chat history, Markdown rendering, and multi-message responses.

**Email Sender** (`tools/mailing_tool.py`) — contains the SMTP delivery logic.

---

## 🛡️ Safety & Validation

- Strict parsing of `Name:` and `Email:` fields
- No email is sent without explicit approval
- Markdown preview avoids unsafe HTML rendering
- Real HTML is preserved for sending

---

## 📈 BigQuery Schema

The agent automatically fetches schema metadata from:

```
{GCP_PROJECT_ID}.{BQ_DATASET}.{BQ_TABLE}
```

If the schema changes, the agent adapts dynamically.

---

## ☁️ Deployment Guide

### Option 1 — Streamlit Cloud (Easiest)

1. Push your repo to GitHub
2. Go to https://share.streamlit.io
3. Select your repo
4. Set the entrypoint to `app.py`
5. Add environment variables in the Streamlit Cloud UI
6. Add your service account JSON to `secrets.toml`

---

## 🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss the proposal.

---

## 📜 License

MIT License.
