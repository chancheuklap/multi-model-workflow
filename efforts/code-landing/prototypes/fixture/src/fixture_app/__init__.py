"""Test-bench package for the code-landing fixture ticket.

`slugify` is the shared function: `task_slug` and `scene_slug` both call it, so a
ticket that names only one of them still has two call sites to find.
"""

from fixture_app.queue import queue_summary, scene_slug, task_slug
from fixture_app.text import slugify

__all__ = ["slugify", "task_slug", "scene_slug", "queue_summary"]
