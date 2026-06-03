# Architecture

## Overview

The project is split into small modules with clear responsibilities:

- input and extraction
- AI processing
- Telegram delivery
- shared settings/session/logging

## Modules

- `main.py`
  - application entry point
  - wires parser, AI layer, and Telegram layer
- `src/parser.py`
  - downloads article HTML
  - extracts plain text using trafilatura
- `src/ai_core.py`
  - runs two-step AI process
  - returns normalized result object
- `src/contracts.py`
  - shared result contract (`PipelineResult`)
- `src/bot/analyzing_service.py`
  - service bridge between parser and AI
- `src/bot/sender.py`
  - Telegram command handlers and message delivery
- `src/bot/bot_utils.py`
  - connectivity utility helpers
- `src/settings.py`
  - validated environment configuration
- `src/session_manager.py`
  - shared aiohttp session lifecycle
- `src/logger.py`
  - loguru setup + compact exception logging
- `src/constants.py`
  - prompts, timeout, and app constants

## Data Flow

1. User sends `/analyze <url>` in Telegram (legacy `/analize` is also accepted).
2. Bot validates command and allowed domain.
3. Parser fetches URL and extracts article text.
4. AI step 1 extracts facts.
5. AI step 2 generates concise analysis.
6. Bot formats output and sends to Telegram.

## Current Constraints

- No scheduler/daemon mode in public version.
- Legacy alias `/analize` is still supported for backward compatibility.
- Command naming still uses legacy spelling (`analize`).
