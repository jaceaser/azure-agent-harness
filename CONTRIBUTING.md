# Contributing

Thanks for helping improve Azure Agent Harness.

## Principles

- Prefer thin abstractions over reimplementing Microsoft Agent Framework.
- New production-facing behavior should include tests and, where appropriate, eval cases.
- Business rules that protect users or money belong in deterministic code/policy rather than prompt text alone.
- Keep Azure-specific integrations modular so local development remains possible.
- Avoid adding infrastructure by default unless it is required for the minimal path.

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,foundry]"
pytest
ruff check .
```

## Pull requests

PRs should explain:

1. what problem is being solved;
2. what architectural layer changes;
3. security / privacy impact;
4. whether agent behavior changed;
5. which eval/test covers the change.
