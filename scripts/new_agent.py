from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / "src" / "azure_agent_harness" / "agents"


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python scripts/new_agent.py <agent_name>")

    raw = sys.argv[1].strip().lower().replace("-", "_")
    if not re.fullmatch(r"[a-z][a-z0-9_]*", raw):
        raise SystemExit("Agent name must be a valid snake_case Python package name")

    target = AGENTS / raw
    if target.exists():
        raise SystemExit(f"Already exists: {target}")

    target.mkdir(parents=True)
    (target / "__init__.py").write_text("")
    (target / "instructions.md").write_text(
        f"You are the {raw.replace('_', ' ')} agent.\\n\\nDefine responsibilities and boundaries here.\\n"
    )
    (target / "main.py").write_text(
        "from pathlib import Path\\n\\n"
        "from azure_agent_harness.runtime.factory import build_agent\\n\\n"
        "INSTRUCTIONS = Path(__file__).with_name('instructions.md').read_text()\\n\\n"
        f"agent = build_agent(name='{raw.replace('_', '-')}', instructions=INSTRUCTIONS)\\n"
    )
    print(f"Created {target.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
