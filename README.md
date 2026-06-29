# AE Remote Script Bridge Skill

This repository contains one installable Codex skill:

```text
skills/ae-remote-script-bridge
```

Copy that folder to another machine's Codex skills directory, for example:

```text
C:\Users\<user>\.codex\skills\ae-remote-script-bridge
```

The skill includes:

- a Windows `AfterFX.com` JSX bridge
- AE ExtendScript rules and pitfalls
- lightweight API and matchName reference tables
- short task cards for common AE scripting work
- a few reusable JSX templates

The bridge does not require a hardcoded AE path. It resolves `AfterFX.com` from `--afterfx`, `AFTERFX_COM_PATH`, optional local `config.json`, or automatic discovery under `C:\Program Files\Adobe`.
