.PHONY: install test lint format eval run

install:
	python -m pip install -e ".[dev,foundry]"

test:
	pytest

lint:
	ruff check .

format:
	ruff format .

eval:
	python -m azure_agent_harness.llmops.local_eval

run:
	python -m azure_agent_harness.agents.example.main "Explain what this starter provides."
