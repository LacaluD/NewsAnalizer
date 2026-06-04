run:
	python main.py

docker-build:
	docker build -t crypto-news-bot:latest .

docker-run:
	docker run -d --env-file .env crypto-news-bot:latest

docker-stop:
	docker stop $$(docker ps -q --filter ancestor=crypto-news-bot:latest) || true

docker-rm:
	docker rm $$(docker ps -aq --filter ancestor=crypto-news-bot:latest) || true

docker-clean: docker-stop docker-rm
	docker rmi crypto-news-bot:latest

install:
	pip install -r requirements.txt

install-dev:
	pip install -r dev-requirements.txt

tests:
	python -m coverage run -m pytest -v -c configs/pytest.ini

# Will run normally only after tests run
tests-build-cov-report:
	python -m coverage report | tee docs/coverage-report.txt

sec-bandit:
	bandit -c configs/bandit.yml -r . -f txt \
          --severity-level high --confidence-level high \
          | tee docs/bandit-report.txt

sec-pip-audit:
	pip-audit --format columns | tee docs/pip-audit-report.txt

lint:
	mypy src/ --ignore-missing-imports --explicit-package-bases --config-file configs/mypy.ini

lint-calls:
	mypy src/ --ignore-missing-imports --explicit-package-bases --enable-error-code call-arg --config-file configs/mypy.ini

typecheck:
	ruff check .
	black --check .

format:
	ruff check . --fix
	black .

black-diff:
	black --diff .

# Cleaning
clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -f coverage.xml coverage.json .coverage

ci:
	make tests
	make sec-bandit
	make sec-pip-audit
	make typecheck
	make lint