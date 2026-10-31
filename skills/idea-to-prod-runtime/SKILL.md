---
name: idea-to-prod-runtime
description: Support files for the idea-to-prod skills, holding the pipeline protocol, factory templates and root tools that the other skills read by path from this folder. Never invoke it, and never remove it while those skills are installed.
---

# idea-to-prod runtime

Built from idea-to-prod 0.24.0. The skills CLI copies each skill's
folder alone, so this folder carries the plugin root the other skills
read. Its files keep their root-relative paths: `docs/pipeline-protocol.md`,
`CONTEXT.md`, `factory/`, `.claude-plugin/plugin.json` and every root
`*.py` tool. Nothing here is meant to be invoked as a skill.
