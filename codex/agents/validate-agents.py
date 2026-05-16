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
    "memory",
    "max" + "Turns",
}
STANDARD_RETURN_TOKENS = [
    "### Verdict",
    "### Evidence",
    "### Result",
    "### Verification",
    "### Open Items",
    "### Routing",
]
STANDARD_RETURN_HEADINGS = set(STANDARD_RETURN_TOKENS)
BANNED_INSTRUCTION_PHRASES = [
    "Fill the `SKILL.md` universal return envelope",
    "SKILL.md universal return envelope",
    "Orchestrate Workflow `SKILL.md` universal return envelope",
]


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


def validate_skills_config(path: Path, data: dict[str, object]) -> None:
    skills = data.get("skills")
    if skills is None:
        return
    if not isinstance(skills, dict) or set(skills) != {"config"}:
        fail(f"{path}: skills must only contain Codex [[skills.config]] entries")

    config = skills.get("config")
    if not isinstance(config, list) or not config:
        fail(f"{path}: skills.config must be a non-empty list")

    for index, entry in enumerate(config, start=1):
        if not isinstance(entry, dict):
            fail(f"{path}: skills.config[{index}] must be a table")
        if set(entry) != {"path", "enabled"}:
            fail(f"{path}: skills.config[{index}] must contain only path and enabled")
        if not isinstance(entry["path"], str) or not entry["path"].endswith("/SKILL.md"):
            fail(f"{path}: skills.config[{index}].path must point to a SKILL.md")
        if not isinstance(entry["enabled"], bool):
            fail(f"{path}: skills.config[{index}].enabled must be a boolean")


def validate_standard_return_headings(path: Path, text: str) -> None:
    headings = [line.strip() for line in text.splitlines() if line.startswith("### ")]
    extra = [heading for heading in headings if heading not in STANDARD_RETURN_HEADINGS]
    if extra:
        fail(f"{path}: non-standard return headings found: {', '.join(extra)}")


def validate_no_ambiguous_skill_reference(path: Path, text: str) -> None:
    hits = [phrase for phrase in BANNED_INSTRUCTION_PHRASES if phrase in text]
    if hits:
        fail(f"{path}: developer_instructions contains ambiguous SKILL.md return reference: {', '.join(hits)}")


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

        validate_skills_config(path, data)

        instructions = data.get("developer_instructions")
        if not isinstance(instructions, str) or not instructions.strip():
            fail(f"{path}: developer_instructions must be a non-empty string")

        stem = path.stem
        require_tokens(path, instructions, STANDARD_RETURN_TOKENS)
        require_tokens(
            path,
            instructions,
            [
                "Return Contract",
                "Do not invent another top-level protocol",
                "pass / blocked / needs repair / needs context",
            ],
        )
        validate_no_ambiguous_skill_reference(path, instructions)
        validate_standard_return_headings(path, instructions)

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
                    "vertical slice",
                    "AFK",
                    "HITL",
                    "deletion test",
                    "交回 parent",
                ],
            )
        if stem in {"coding-worker", "complex-coding-worker"}:
            require_tokens(path, instructions, ["NEEDS_CONTEXT", "BLOCKED"])
        if stem == "coding-worker":
            require_tokens(path, instructions, ["public behavior", "horizontal slicing", "外部边界"])
        if stem == "complex-coding-worker":
            require_tokens(path, instructions, ["falsifiable hypotheses", "feedback loop", "confirmed hypothesis"])
        if stem == "complex-code-explorer":
            require_tokens(path, instructions, ["read-only", "feedback loop", "falsifiable", "deletion test", "single adapter", "交回 parent"])
        if stem == "docs-worker":
            require_tokens(path, instructions, ["NEEDS_CONTEXT", "不要自行改变 issue tracker 状态"])

    print(f"Validated {len(files)} Codex agent templates.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
