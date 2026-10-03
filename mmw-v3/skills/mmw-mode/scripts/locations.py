"""Text anchors and paths shared by MMW's scripts.

Paths are relative to mmw-v3/skills/ so this module moves with mmw-mode/scripts/.
Readers resolve the strings; this registry imports no other module.
"""

PLAYBOOK_ANCHORS = {
    "research-a-question": (
        "Name the decision it feeds",
        "Run the research",
        "Commit the report",
        "Answer on the ticket",
        "Leave the map alone",
    ),
}

MODE_DIRECTORY = "mmw-mode"
MODE_SCRIPTS = MODE_DIRECTORY + "/scripts"
MODE_PRINCIPLES_DIRECTORY = MODE_DIRECTORY + "/principles"
MODE_PLAYBOOKS_DIRECTORY = MODE_DIRECTORY + "/playbooks"
MODE_PRINCIPLES = "## Principles"
