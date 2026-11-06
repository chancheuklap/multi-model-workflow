---
name: setup-mmw
description: Configure the installed MMW plugin's user model settings and verify its bundled dispatch tools.
---

# Set up MMW

You configure an already installed MMW plugin. Keep the owner's existing model choices.

Use only the installed **dispatch** skill's Runtime section to obtain its `dispatch` path and version, then return here. This starts no night. Run `bash DISPATCH show --host HOST`, with DISPATCH set to that returned path and HOST set to the current host, `codex` or `cursor`.

The command reads `~/.agents/models.json`. When that user file is absent, it creates it from `MMW_MODELS_JSON` if supplied by the environment, otherwise from this plugin's bundled defaults. It does not change an existing user file. To change the owner's choices, edit only the requested host's rows in that user file.

Run `bash DISPATCH row researcher --host HOST` from the consuming repository. Confirm that the host lists this plugin's `dispatch` and `research` skills and that the tool uses the user model file. Return the plugin version, model file path and the observed result.

This skill is an optional configuration check. Other MMW skills prepare their tools through dispatch on first use. To preserve personal model choices across fresh cloud VMs, save the complete user JSON as `MMW_MODELS_JSON` in the platform's environment settings.

The host installs the plugin for cloud chats. Installing the plugin in a VM's separate Codex CLI does not establish that the surrounding cloud chat has it. When that chat does not list MMW, report the missing host installation rather than copying skills into a directory or modifying repository instructions.
