# MMW

MMW v5 provides skills and agent dispatch for developing projects. The cloud edition uses a local Coordinator and Cloud Workers; the local-session edition uses independent local sessions.

## Install MMW v5 Cloud

If the user gives you this repository's URL and asks you to install MMW v5 Cloud, follow the instructions for your host:

- **Cursor:** follow [Install the Cursor cloud edition](https://github.com/chancheuklap/multi-model-workflow/blob/mmw-v5/AGENTS.md#install-the-cursor-cloud-edition). Install into the consuming repository's `.cursor/` so its local and cloud Cursor agents use the same skills and tools.
- **Codex:** follow the **Codex** installation commands in the [cloud edition README](https://github.com/chancheuklap/multi-model-workflow/blob/mmw-v5/mmw-v5-cloud/README.md#使用). Install the `mmw-v5-cloud` plugin on the local machine.

Run installation commands from the project the user is developing. This repository supplies MMW; it is not the project to install into unless the user is developing MMW itself. Preserve existing model configuration and unrelated host settings. Report the installed edition, version and location.

The current installation instructions are on the `mmw-v5` development branch. The links above deliberately point there; this landing page is also on the default branch so an agent can find the installer from the repository URL alone.
