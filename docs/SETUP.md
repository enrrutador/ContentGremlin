# ContentGremlin – Setup Guide

## Requirements

- Python 3.11+
- Git
- (Optional) FFmpeg for local video processing
- API keys for the LLM provider you want to use

## Installation

```bash
git clone https://github.com/enrrutador/ContentGremlin.git
cd ContentGremlin

python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
```

Edit the `.env` file with at least one LLM provider.

YouTube credentials can be added later from the web interface.

## Running

```bash
python main.py
```

The application will start at:

**http://localhost:8000**

Open that URL in your browser. You will see the full interface with all tabs ready.

## First-time Configuration

1. Go to the **Configuration** tab.
2. Add at least one LLM provider and test the connection.
3. (Optional) Configure YouTube Data API when you are ready to upload.
4. Set your preferred mode (Supervised or Autonomous).
5. Define your content style / niche preferences.

Everything can be changed later without restarting (most settings).

## Using with Agents

Once the server is running, any agent can talk to it via the REST API.

Full interactive documentation is available at:

**http://localhost:8000/docs**

This makes integration with OpenClaw, Hermes and other agent frameworks straightforward.
