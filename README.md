# negotiator-tester

## Configuration

This project uses environment variables for configuration. Create a `.env` file in the root directory with the following variables:

- `NEGOTIATOR_API_URL`: The URL for the negotiator API (e.g., `http://127.0.0.1:8000/api/v1/inbound/messages`).
- `NEGOTIATOR_INBOUND_BEARER_TOKEN`: The bearer token for inbound messages.
- `NEGOTIATOR_OUTBOUND_BASE_URL`: The base URL for outbound action webhooks.
- `NEGOTIATOR_OUTBOUND_BEARER_TOKEN`: The bearer token for outbound validation.
- `NEGOTIATOR_DB_PATH`: The absolute path to the `negotiator.db` SQLite database file (e.g., `C:\repos\negotiator\negotiator.db`).

The application will read these variables at startup.

## Local Setup

This repository uses `uv` for local environment management and dependency installation.

```bash
uv sync
```

If you need to refresh the environment from scratch, remove the existing `.venv` directory and run `uv sync` again.

### Logging
All application logs, including SQLite connection tracebacks and server start events, are automatically saved to `negotiator-playground.log` in the root of the project directory alongside being printed to the console.

## System Requirements

- **Windows**: Windows 11
- **Linux**: Ubuntu 22.04 LTS or newer

## How to Run

### Windows (Command Prompt)
```cmd
cmd /c "set PYTHONPATH=. && uv run uvicorn main:app --port 3000 --host 127.0.0.1"
```

### Windows (PowerShell)
```powershell
$env:PYTHONPATH="."; uv run uvicorn main:app --port 3000 --host 127.0.0.1
```

### Linux (Ubuntu)
```bash
PYTHONPATH=. uv run uvicorn main:app --port 3000 --host 127.0.0.1
```
