"""Task queue of the fixture workbench: the data behind `site/index.html`."""

from __future__ import annotations

from collections.abc import Sequence

from fixture_app.text import slugify

TASKS: tuple[dict[str, str], ...] = (
    {"task_id": "running-main", "name": "商品主图生成任务", "meta": "今天 16:18 · 3 / 5 张", "state": "running", "state_text": "进行中"},
    {"task_id": "completed-main", "name": "商品主图生成任务", "meta": "07-16 10:42 · 3 套 · 3 张成图", "state": "ready", "state_text": "已完成"},
    {"task_id": "partial-main", "name": "商品主图生成任务", "meta": "07-12 19:07 · 1 / 3 张已交付", "state": "partial", "state_text": "部分完成"},
    {"task_id": "failed-main", "name": "商品主图生成任务", "meta": "07-11 14:22 · 0 / 3 张已交付", "state": "failed", "state_text": "失败"},
    {"task_id": "completed-main-old", "name": "商品主图生成任务", "meta": "07-09 09:31 · 2 套 · 2 张成图", "state": "ready", "state_text": "已完成"},
)


def task_slug(task_id: str) -> str:
    """First call site of `slugify`: the queue item's anchor."""
    return f"task-{slugify(task_id)}"


def scene_slug(scene_name: str) -> str:
    """Second call site of `slugify`: the name a baseline scene file is stored under."""
    return slugify(scene_name)


def queue_summary(tasks: Sequence[dict[str, str]] = TASKS) -> dict[str, object]:
    """Counts the sidebar header prints: `{count} 个任务`, and whether the empty state shows."""
    return {"count": len(tasks), "empty": len(tasks) == 0}
