
# Gemini Client Setup Guide

## Prerequisites

- Python 3.8 or higher
- pip package manager
- Google API key for Gemini

## Installation

1. Clone the repository:
```bash
git clone https://github.com/jsonavalos/ADS-509-Project
cd your-project
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Get API Environment Key:
```bash
Go to aistudio.google.com/app/apikey and create an API key for Gemini. Then, add the following line to your .env file, replacing the value with your actual API key.
```

## Configuration

Create a `.env` file in the project root:
```
GEMINI_API_KEY=your-api-key-here
```

## Running the Client

```bash
python gemini_client.py
```

## Troubleshooting

- Verify your API key is correctly set
- Check internet connectivity
- Review logs for error messages
