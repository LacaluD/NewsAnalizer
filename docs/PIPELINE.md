# Pipelines

## Runtime Pipeline

1. Receive `/analyze <url>` command (legacy `/analize` is supported).
2. Validate command format and domain.
3. Download article HTML.
4. Extract plain text.
5. AI Step 1: fact extraction.
6. AI Step 2: analysis based on extracted facts.
7. Convert output to Telegram HTML.
8. Send message to configured chat.

## Error Handling Model

The runtime path uses a unified `PipelineResult` object:

- `success`: operation status
- `text`: payload
- `tag`: optional hashtag
- `error`: user-safe error message

This removes `tuple | str | None` ambiguity between layers.

## CI Pipeline

Workflow file: `.github/workflows/main.yml`

Jobs:

- `tests`:
  - Python matrix 3.10/3.11/3.12
  - pytest + coverage outputs
- `dependency-review`:
  - PR dependency security review
- `security-audit`:
  - `pip-audit` vulnerability scan
  - `bandit` static security scan
- `typecheck`:
  - mypy checks
- `formatting`:
  - ruff and black checks
- `notify`:
  - Telegram success/failure notifications
  - report packaging on failures

## Local Quality Pipeline (Makefile)

Common local sequence:

1. `make tests`
2. `make tests-build-cov-report`
3. `make sec-bandit`
4. `make sec-pip-audit`
5. `make typecheck`
6. `make lint`

See `docs/MAKEFILE.md` for target details.
