# Force UTF-8 console output for bridge runs under Chinese paths

- Status: pending review
- Date: 2026-07-17
- Context: Ran `client\send_to_ae.py` from a workspace path containing Chinese characters on Windows with Python 3.12.
- Observation: The bridge stopped before JSX execution while printing `Run Dir`; the console used `cp1252` and raised `UnicodeEncodeError: 'charmap' codec can't encode characters`.
- Evidence: Reproduced when the run directory contained `AINAS项目素材`; rerunning the same command with `PYTHONIOENCODING=utf-8` completed normally.
- Workaround: In PowerShell, set `$env:PYTHONIOENCODING='utf-8'` for the bridge process before invoking Python.
- Candidate destination: Bridge launcher code or the Windows command examples in `SKILL.md`.
- Review notes:
