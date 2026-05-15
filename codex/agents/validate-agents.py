#!/usr/bin/env python3
"""Validate Codex agent templates for the migration package."""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REQUIRED_FIELDS = {
    "model",
    "model_reasoning_effort",
    "model_verbosity",
    "developer_instructions",
}
CLAUDE_ONLY_FIELDS = {
    "tools",
    "disallowed" + "Tools",
    "skills",
    "memory",
    "max" + "Turns",
}


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def load_toml(path: Path) -> dict[str, object]:
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        fail(f"{path}: invalid TOML: {exc}")


def require_tokens(path: Path, text: str, tokens: list[str]) -> None:
    missing = [token for token in tokens if token not in text]
    if missing:
        fail(f"{path}: developer_instructions missing tokens: {', '.join(missing)}")


def main() -> int:
    files = sorted(ROOT.glob("*.toml"))
    if not files:
        fail("no agent templates found")

    for path in files:
        data = load_toml(path)
        missing = REQUIRED_FIELDS - data.keys()
        if missing:
            fail(f"{path}: missing required fields: {', '.join(sorted(missing))}")

        forbidden = CLAUDE_ONLY_FIELDS & data.keys()
        if forbidden:
            fail(f"{path}: contains Claude-only fields: {', '.join(sorted(forbidden))}")

        instructions = data.get("developer_instructions")
        if not isinstance(instructions, str) or not instructions.strip():
            fail(f"{path}: developer_instructions must be a non-empty string")

        stem = path.stem
        if "reviewer" in stem:
            require_tokens(path, instructions, ["read-only", "findings"])
        if stem == "code-reviewer":
            require_tokens(
                path,
                instructions,
                [
                    "domain language",
                    "owner",
                    "场景",
                    "public behavior",
                    "vertical tracer bullet",
                    "AFK",
                    "HITL",
                    "deletion test",
                ],
            )
        if stem in {"coding-worker", "complex-coding-worker"}:
            require_tokens(path, instructions, ["DONE", "DONE_WITH_CONCERNS", "NEEDS_CONTEXT", "BLOCKED"])
        if stem == "coding-worker":
            require_tokens(path, instructions, ["public behavior", "horizontal slicing", "外部边界"])
        if stem == "complex-coding-worker":
            require_tokens(path, instructions, ["falsifiable hypotheses", "feedback loop", "confirmed hypothesis"])
        if stem == "complex-code-explorer":
            require_tokens(path, instructions, ["read-only", "feedback loop", "falsifiable", "deletion test", "single adapter"])
        if stem == "docs-worker":
            require_tokens(path, instructions, ["NEEDS_CONTEXT"])

    print(f"Validated {len(files)} Codex agent templates.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
