"""Text anchors and paths shared by MMW's scripts.

Paths are relative to mmw-v2/skills/ so this module moves with dispatch/scripts/.
Readers resolve the strings; this registry imports no other module.
"""

PLAYBOOK_STEPS = {
    "work-a-ticket": (
        "Adopted ticket",
        "Claim",
        "Read yourself in",
        "Integrate and run every criterion",
        "Post the decisions",
        "Get reviewed",
        "Run every criterion one final time",
        "Audit against the ticket",
        "Close out",
        "When the orchestrator resumes you",
        "After the closeout of an adopted ticket",
    ),
    "review-a-ticket": ("Pin the diff",),
    "run-a-night": (
        "Check and open",
        "Lint the batch",
        "Advance, then end your turn",
        "Handle each wake",
        "Closing pass",
        "Close the Memory records",
        "Reverify and summarize",
        "Retro",
    ),
    "accept-the-night": ("Read the night out",),
    "land-one-ticket": ("Start the worker", "Handle each wake", "Land"),
    "research-a-question": (),
}

TICKET_HEADINGS = (
    "## Parent",
    "## Owns",
    "## Read first",
    "## Seam",
    "## Moves",
    "## Acceptance criteria",
    "## State list",
)

SUCCESS_MARKERS = (
    "STORY OK",
    "BOUNDARY OK",
    "JOURNEY OK",
    "HARNESS OK",
    "VERBATIM OK",
    "STRUCTURE OK",
    "DRAFTS OK",
)

PRODUCT_RUNNING_RULES = "## Five rules while the product is running"

DISPATCH_SCRIPTS = "dispatch/scripts"
EVENTS_PY = "verify-ticket/scripts/events.py"
VERIFY_TICKET_PY = "verify-ticket/scripts/verify-ticket.py"
ISSUE_TREE_PY = "verify-ticket/scripts/issue_tree.py"
UI_ACCEPTANCE_SCRIPTS = "ui-acceptance/scripts"

GOVERNED_TICKET_DIR_PATTERN = r"^issue-(\d+)$"
