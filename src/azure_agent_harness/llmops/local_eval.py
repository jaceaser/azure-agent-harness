from __future__ import annotations

import json
from pathlib import Path

DATASET = Path(__file__).resolve().parents[3] / "llmops" / "datasets" / "example.jsonl"


def main() -> None:
    """Fast deterministic dataset validation for the CI inner loop.

    Cloud LLM-as-judge evaluations belong in a separate CI job so PRs can still
    run deterministic checks without Azure credentials.
    """
    rows = [json.loads(line) for line in DATASET.read_text().splitlines() if line.strip()]
    assert rows, "Regression dataset must not be empty"

    required = {"id", "query", "expected_behavior"}
    for row in rows:
        missing = required - set(row)
        assert not missing, f"{row.get('id', '<unknown>')}: missing {sorted(missing)}"

    print(f"Validated {len(rows)} regression cases from {DATASET}")


if __name__ == "__main__":
    main()
