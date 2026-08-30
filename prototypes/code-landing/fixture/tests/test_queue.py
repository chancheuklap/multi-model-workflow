from fixture_app.queue import TASKS, queue_summary, scene_slug, task_slug


def test_task_slug_prefixes_the_slugified_id():
    assert task_slug("running-main") == "task-running-main"
    assert task_slug("v1.2-main") == "task-v1-2-main"


def test_scene_slug_matches_the_baseline_scene_names():
    assert scene_slug("Queue empty") == "queue-empty"
    assert scene_slug("Queue v2.1 empty") == "queue-v2-1-empty"


def test_queue_summary_counts_the_default_scene():
    assert queue_summary() == {"count": 5, "empty": False}


def test_queue_summary_reports_the_empty_scene():
    assert queue_summary([]) == {"count": 0, "empty": True}


def test_every_task_has_a_slug():
    assert [task_slug(t["task_id"]) for t in TASKS][0] == "task-running-main"
