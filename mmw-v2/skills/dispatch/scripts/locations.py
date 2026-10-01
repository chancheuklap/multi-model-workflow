"""Text anchors and paths shared by MMW's scripts.

Paths are relative to mmw-v2/skills/ so this module moves with dispatch/scripts/.
Readers resolve the strings; this registry imports no other module.
"""

PLAYBOOK_ANCHORS = {
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
    "research-a-question": (
        "Name the decision it feeds",
        "Run the research",
        "Commit the report",
        "Answer on the ticket",
        "Leave the map alone",
    ),
}

# Event-derived positions. A missing playbook uses the role's roles.json entry.
WHERE_ROWS = {
    "worker": {
        "fresh": {"kind": "FRESH", "step": "Claim"},
        "claimed": {"kind": "BETWEEN", "step": "Read yourself in",
                    "until": "Integrate and run every criterion"},
        "checked": {"kind": "AT", "step": "Post the decisions"},
        "decided": {"kind": "AT", "step": "Get reviewed"},
        "waiting": {"kind": "AT", "step": "Get reviewed",
                    "note": "waiting: end your turn"},
        "reported": {"kind": "AT", "step": "Get reviewed", "note": "fix round"},
        "reviewed": {"kind": "AT", "step": "Run every criterion one final time"},
        "final": {"kind": "BETWEEN", "step": "Audit against the ticket", "until": "Close out"},
        "returned": {"kind": "AT", "step": "Claim",
                     "note": "then from #Integrate and run every criterion"},
    },
}
WHERE_ROWS["adopting-worker"] = {
    **WHERE_ROWS["worker"],
    "closed": {"kind": "AT", "step": "After the closeout of an adopted ticket"},
}
WHERE_ROWS["reviewer"] = {"fresh": {"kind": "FRESH", "step": "Pin the diff"}}
WHERE_ROWS["night-orchestrator"] = {
    "fresh": {"kind": "FRESH", "step": "Check and open"},
    "opened": {"kind": "BETWEEN", "step": "Lint the batch", "until": "Advance, then end your turn"},
    "working": {"kind": "AT", "step": "Handle each wake"},
    "findings": {"kind": "AT", "step": "Closing pass"},
    "closing": {"kind": "BETWEEN", "step": "Close the Memory records", "until": "Reverify and summarize"},
    "closed": {"kind": "AT", "step": "Retro"},
    "retroed": {"kind": "AT", "playbook": "accept-the-night", "step": "Read the night out"},
}
WHERE_ROWS["one-ticket-orchestrator"] = {
    "fresh": {"kind": "FRESH", "step": "Start the worker"},
    "working": {"kind": "AT", "step": "Handle each wake"},
    "finished": {"kind": "AT", "step": "Land"},
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

MODE_DIRECTORY = "mmw"
MODE_PRINCIPLES_DIRECTORY = MODE_DIRECTORY + "/principles"
MODE_PLAYBOOKS_DIRECTORY = MODE_DIRECTORY + "/playbooks"
PSTACK_REFERENCES_DIRECTORY = MODE_DIRECTORY + "/references/pstack"
PSTACK_SCRIPTS_DIRECTORY = MODE_DIRECTORY + "/scripts/pstack"
PSTACK_AGENTS_DIRECTORY = PSTACK_REFERENCES_DIRECTORY + "/agents"
IMPORTS_TSV = "mmw/imports.tsv"
PSTACK_REWRITES_TSV = "../import/pstack-rewrites.tsv"
PSTACK_DIRECTORY = "../upstream-pstack"
PSTACK_MODE_DIRECTORY = PSTACK_DIRECTORY + "/skills/poteto-mode"
UI_ACCEPTANCE_REFUSAL_PY = UI_ACCEPTANCE_SCRIPTS + "/refusal.py"
MODE_NON_NEGOTIABLES = "## Non-negotiables"
MODE_IMPORTED_TRIGGERS = "### Imported triggers"
MODE_PLAYBOOKS = "## Playbooks"
MODE_PRINCIPLES = "## Principles"

GOVERNED_TICKET_DIR_PATTERN = r"^issue-(\d+)$"
