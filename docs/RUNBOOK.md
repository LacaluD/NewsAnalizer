# Runbook

## Local Run

1. Create virtual environment.
2. Install dependencies.
3. Create `.env` with required keys.
4. Run `python main.py`.

## Local Testing

Direct commands:

- `python -m pytest src/tests -v`
- `python -m pytest src/tests --cov=main --cov=src --cov-report=term-missing`

Makefile commands:

- `make tests`
- `make tests-build-cov-report`

Latest local result at the time of writing:

- `129 passed`
- Coverage over `main.py` + `src/*`: `99.48%`

Coverage report artifact path (Makefile flow):

- `docs/coverage-report.txt`

For a full list of automation targets, see `docs/MAKEFILE.md`.

## Required Environment Variables

- `AI_TOKEN`
- `TG_BOT_TOKEN`
- `OWNER_TG_ID`
- `ADMIN_CHAT_ID`

## Quick Health Checks

- Confirm bot token and chat permissions.
- Confirm OpenRouter token validity.
- Confirm outgoing internet access.

## Common Issues

1. Bot does not send messages
- Check `TG_BOT_TOKEN` and `ADMIN_CHAT_ID`.
- Ensure the bot has access to target chat/channel.

2. AI request fails
- Check `AI_TOKEN`.
- Check model availability and API quota.

3. Empty output
- Source page may be blocked or extraction returned empty text.
- Try another URL.

4. CI failure in security/type checks
- Download artifacts from workflow run.
- Fix findings and rerun pipeline.
