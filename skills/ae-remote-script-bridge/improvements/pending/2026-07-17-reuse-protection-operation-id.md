# Reuse one protection operation ID throughout the same task

- Status: pending review
- Date: 2026-07-17
- Context: A single user request required an initial AE edit followed by a layout adjustment and repeated verification calls.
- Observation: Treating related mutations as separate protected operations repeats the saved/clean check and may create redundant project backups, adding avoidable latency. The bridge already supports protection-state reuse for this case.
- Evidence: Passing the same `--operation-id` to the follow-up mutation produced `[AE BACKUP REUSED]` and reused the first protected backup instead of creating another one.
- Workaround: Generate one stable `--operation-id` per user-request batch and reuse it for every related mutating bridge call, including corrective iterations. Start a new ID only for a genuinely new user request; read-only inspection continues to use `--no-protect` where permitted.
- Candidate destination: Make operation-ID reuse more prominent in the core mutation workflow and command templates; consider a client-side task or session helper if agents still generate new IDs accidentally.
- Review notes:
