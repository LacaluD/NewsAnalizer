# Makefile Guide

This project includes a Makefile for common local and CI-like routines.

## Core Targets

- `make run`
  - Runs the bot: `python main.py`

- `make install`
  - Installs runtime requirements from `requirements.txt`

- `make install-dev`
  - Installs from`dev-requirements.txt`

## Tests and Coverage

- `make tests`
  - Runs: `python -m coverage run -m pytest -v -c configs/pytest.ini`

- `make tests-build-cov-report`
  - Runs: `python -m coverage report | tee docs/coverage-report.txt`
  - Intended to be used after `make tests`

For direct pytest + coverage over `main.py` and `src/*`:

```bash
python -m pytest src/tests --cov=main --cov=src --cov-report=term-missing
```

## Security

- `make sec-bandit`
  - Bandit scan with project config
  - Saves report to `docs/bandit-report.txt`

- `make sec-pip-audit`
  - Dependency vulnerability scan
  - Saves report to `docs/pip-audit-report.txt`

## Static Analysis and Formatting

- `make lint`
  - mypy checks for `src/`

- `make lint-calls`
  - mypy checks with `call-arg` enabled

- `make typecheck`
  - Ruff + Black check mode

- `make format`
  - Ruff auto-fix + Black check

## Housekeeping and Composite Pipeline

- `make clean`
  - Removes `__pycache__`, `*.pyc`, and coverage artifacts

- `make ci`
  - Sequentially runs tests, security checks, formatting checks, and lint

## Practical Order for Local Validation

```bash
make install
make tests
make tests-build-cov-report
make sec-bandit
make sec-pip-audit
make typecheck
make lint
```
