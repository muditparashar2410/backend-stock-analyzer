# Backend - AI-Powered Indian Stock Market Research Assistant

FastAPI backend service powering the Indian Stock Assistant, featuring Google Gemini (`google-genai`), Tapetide MCP integration, and chat persistence.

## Architecture
- **Framework**: FastAPI (Async Python 3.11)
- **LLM Abstraction**: `LLMProvider` interface backed by `GeminiProvider` (`google-genai`).
- **MCP Client**: Official `mcp` SDK connecting to `https://mcp.tapetide.com/mcp`.
- **Database**: SQLite in-memory default for V1, Postgres ready via `DATABASE_URL`.

## Setup & Running
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Copy environment file and configure keys:
   ```bash
   cp .env.example .env
   ```
3. Run dev server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
