setup:
	uv sync --all-groups

lint:
	uv run ruff check .

format:
	uv run ruff format .

format-check:
	uv run ruff format --check .

test:
	uv run pytest

cov:
	uv run pytest --cov=ticketsense --cov-report=term-missing

check: lint format-check test
	