[![CI](https://img.shields.io/github/actions/workflow/status/LacaluD/flowguard/main.yml?branch=main&label=CI)](https://github.com/LacaluD/flowguard/actions/workflows/main.yml)
[![Coverage](https://codecov.io/gh/LacaluD/flowguard/graph/badge.svg?branch=main)](https://codecov.io/gh/LacaluD/flowguard)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)


# Crypto News Bot

Lightweight Telegram bot that fetches CoinDesk articles, extracts factual content, generates AI-based summaries, and posts the result to Telegram.

> **Note:** This repository contains the base architecture and core business logic of the project.
> It was developed iteratively — the public version contains a sanitized codebase with private configuration and extended features removed.
> The full production version with additional automation runs privately.

## Current Status

- End-to-end manual flow is working via `python main.py`.
- Telegram handlers are available: `/start`, `/connection`, `/analyze`.
- Article extraction and 2-step AI analysis are integrated.
- CI pipeline is active in `.github/workflows/main.yml`.
- Unit test suite exists in `src/tests/` and is passing.

### Local Test Status (latest run)

- `129 passed`
- Coverage for `main.py` + `src/*`: `99.48%`

Command used:

```bash
python -m pytest src/tests --cov=main --cov=src --cov-report=term-missing
```

## Quick Start

### 1) Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 2) Configure environment

Create `.env` in the project root:

```env
AI_TOKEN=...
TG_BOT_TOKEN=...
OWNER_TG_ID=...
ADMIN_CHAT_ID=...
```

### 3) Run

```bash
python main.py
```

## Docker

Multi-stage build keeps the final image clean — build tools stay in the builder stage only.
Image size: ~336MB (multi-stage) vs ~350MB (single-stage).

The difference is small because the project uses pure Python dependencies without
heavy C/Rust-compiled extensions. Multi-stage builds show a larger size reduction
in projects that require compilation (e.g. numpy, psycopg2, cryptography).

Tested locally — bot starts and connects to Telegram successfully.

### Build comparison
| Build type   | Image size |
|--------------|------------|
| Multi-stage  | 336 MB     |
| Single-stage | 350 MB     |

## Testing

Run tests directly (pytest):

```bash
python -m pytest src/tests -v
```

Run tests with coverage (direct command):

```bash
python -m pytest src/tests --cov=main --cov=src --cov-report=term-missing
```

Run tests via Makefile:

```bash
make tests
make tests-build-cov-report
```

## Makefile Commands

Full list of available Makefile commands is documented in [MAKEFILE.md](docs/MAKEFILE.md).


## Usage Example

Analyze one CoinDesk article manually in Telegram:

```text
/analyze https://www.coindesk.com/...
```

## Runtime Pipeline

Full description of pipeline you can find documented in [PIPELINE](docs/PIPELINE.md)

1. Receive article URL from Telegram `/analyze` command.
2. Download article HTML.
3. Extract plain text with `trafilatura`.
4. Run AI Step 1: fact extraction.
5. Run AI Step 2: concise grounded analysis.
6. Format output for Telegram HTML.
7. Send result to configured admin chat.

## Project Skeleton

List of all modules is documented in [ARCHITECTURE](docs/ARCHITECTURE.md)

```text
.
├── main.py
├── requirements.in
├── requirements.txt
├── src/
│   ├── ai_core.py
│   ├── constants.py
│   ├── contracts.py
│   ├── logger.py
│   ├── parser.py
│   ├── session_manager.py
│   ├── settings.py
│   ├── bot/
│       ├── analyzing_service.py
│       ├── bot_utils.py
│       └── sender.py
│   └── tests/
│       └── test_*.py
├── configs/
│   ├── bandit.yml
│   ├── mypy.ini
│   └── pytest.ini
├── docs/
│   ├── INDEX.md
│   ├── ARCHITECTURE.md
│   ├── PIPELINE.md
│   ├── STACK.md
│   ├── RUNBOOK.md
│   ├── MAKEFILE.md
│   └── project_goal.md
└── .github/workflows/main.yml
```

## CI Pipeline Structure

Workflow: `.github/workflows/main.yml`

Main jobs:

- `tests`:
  - Python matrix (3.10, 3.11, 3.12)
  - pytest + coverage reports
  - Codecov upload
- `dependency-review`:
  - PR-only dependency review action
- `security-audit`:
  - `pip-audit` + `bandit`
  - artifacts for scan reports
- `typecheck`:
  - mypy checks + report artifact
- `formatting`:
  - ruff + black checks
- `notify`:
  - Telegram success/failure notification
  - collects available artifacts on failure

## Stack (Minimal)

- Python 3.10+
- aiogram (Telegram bot)
- aiohttp + requests (networking)
- trafilatura (article text extraction)
- loguru (logging)
- pydantic-settings (validated env config)
- GitHub Actions + bandit + pip-audit + mypy + ruff + black

See also [Stack](docs/STACK.md)

## Done

- Telegram command handlers for basic operations.
- Shared HTTP session manager.
- Robust command parsing and URL validation.
- Unified pipeline result contract between layers.
- Basic CI pipeline with tests, security, typing, formatting, and notifications.

## TODO

- Expand and update tests + integration tests
- Add stronger coverage threshold policy in CI.

## Development Recommendations

- Keep tests fast in PR jobs; move heavier checks to main/nightly if needed.
- Keep CI jobs parallel where possible to reduce feedback time.
- Add metrics around extraction failures and AI API errors.
- Add retry strategy for transient external API failures.

## Full Project Description

Crypto News Bot is a modular Python service that turns long-form crypto news into concise Telegram-ready analysis. The system combines deterministic content extraction with AI summarization in two explicit steps (fact extraction and interpretation), reducing hallucination risk by grounding the second step on the first step output. The current public version focuses on architecture clarity, robust error handling, and CI quality controls, while advanced production automation remains private.
