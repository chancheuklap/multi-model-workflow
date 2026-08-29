from fixture_app.text import slugify


def test_slugify_lowercases_and_dashes_separators():
    assert slugify("Queue Empty_State") == "queue-empty-state"


def test_slugify_drops_characters_with_no_ascii_form():
    assert slugify("任务队列") == ""


def test_slugify_collapses_repeated_dashes():
    assert slugify("task -- main") == "task-main"
