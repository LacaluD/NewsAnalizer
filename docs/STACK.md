# Technology Stack

This document describes the current public stack used in the project: runtime, architecture layers, integrations, and quality tooling.

## Runtime and Core Libraries

| Component | Version / Range | Role in project |
| --- | --- | --- |
| Python | 3.10+ | Main runtime for bot, parsing, and AI orchestration |
| aiogram | >=3.0.0 (locked in requirements) | Telegram bot framework: command handling, dispatching, message sending |
| aiohttp | >=3.9.0 (locked in requirements) | Async HTTP client and shared session lifecycle |
| requests | runtime dependency | Extra HTTP client usage in utility/network flows |
| trafilatura | >=1.9.0 (locked in requirements) | Article content extraction from raw HTML |
| feedparser | >=6.0.0 | Parsing RSS/feeds for news input sources |
| pydantic-settings | >=2.14.1 | Validated environment configuration loading from .env |
| pydantic | transitive | Data validation backbone for settings/models |
| python-dateutil | >=2.8.0 | Date parsing helpers in content handling |
| loguru | >=0.7.3 | Structured logging and compact exception output |

Notes:
- Versions in `requirements.txt` and `dev-requirements.txt` are pinned via pip-compile.
- `pyproject.toml` defines minimum/ranged dependencies for project metadata.

## Application Architecture Layers

### 1. Input and Extraction Layer

- `src/parser.py`: downloads article pages and extracts plain text with trafilatura.
- URL/domain checks are enforced before extraction (CoinDesk-focused flow in public version).

### 2. AI Processing Layer

- `src/ai_core.py` integrates with OpenRouter Chat Completions.
- Two-step prompt strategy:
  - Step 1: fact extraction from article text.
  - Step 2: grounded analysis based on extracted facts.
- Shared result contract is defined in `src/contracts.py` (`PipelineResult`).

### 3. Telegram Delivery Layer

- `src/bot/sender.py`: bot command handlers and delivery.
- `src/bot/analyzing_service.py`: service bridge between parser and AI layers.
- `src/bot/bot_utils.py`: connectivity/helper routines for Telegram-related operations.

### 4. Shared Infrastructure Layer

- `src/settings.py`: centralized, validated settings model.
- `src/session_manager.py`: shared aiohttp session lifecycle.
- `src/logger.py`: loguru setup and error logging conventions.
- `src/constants.py`: prompts, timeouts, and app-level constants.

## External Integrations

| Integration | Purpose |
| --- | --- |
| Telegram Bot API | Receives commands and sends formatted analysis output |
| OpenRouter API | Provides LLM inference for the two-step analysis pipeline |
| CoinDesk article URLs | Primary content source in the public pipeline |

## AI Layer Details

- API: OpenRouter Chat Completions endpoint.
- Prompting approach: deterministic two-step flow to reduce hallucination risk.
- Strategy: second-step interpretation is grounded on first-step factual extraction.
- Output: normalized pipeline result that is formatted for Telegram HTML delivery.

## Quality, Security, and CI Tooling

| Area | Tools | What is checked |
| --- | --- | --- |
| Tests | pytest, pytest-cov, coverage | Unit tests and coverage metrics for `main.py` and `src/*` |
| Static typing | mypy | Type consistency and call argument checks |
| Lint/format | ruff, black | Style, lint violations, and formatting consistency |
| Dependency security | pip-audit | Known vulnerabilities in Python dependencies |
| SAST | bandit | Common Python security issues in codebase |
| CI orchestration | GitHub Actions | Parallel jobs for test, security, typing, and formatting checks |

## Build and Execution Tooling

- Local run entry point: `python main.py`.
- Standard developer tasks are orchestrated via `Makefile` (`tests`, `lint`, `typecheck`, `sec-bandit`, `sec-pip-audit`, `ci`, etc.).
- Docker is supported with dedicated targets:
  - `make docker-build`
  - `make docker-run`
  - `make docker-stop`
  - `make docker-rm`
  - `make docker-clean`

## Configuration and Environment

- Environment variables are loaded from `.env` via pydantic-settings.
- Core runtime secrets/config include bot token, AI token, and Telegram chat/user IDs.
- Validation is centralized in settings layer to fail fast on bad/missing config.

## Summary

The stack is a modular Python 3.10+ Telegram bot platform that combines:

- deterministic text extraction,
- grounded two-step AI analysis via OpenRouter,
- explicit integration boundaries,
- and a CI-oriented quality/security toolchain.
