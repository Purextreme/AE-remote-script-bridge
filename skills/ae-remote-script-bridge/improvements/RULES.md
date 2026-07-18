# AE Remote Script Bridge Improvement Queue Rules

This directory is a review queue for reusable experience discovered during real After Effects operations. Each file under `pending/` is one candidate, not an established Skill rule. A maintainer must review it before moving anything into `SKILL.md`, a task card, a reference, or bridge code.

## Recording workflow

- Record only behavior observed in a real run with concrete evidence such as an error, warning, run artifact, or reproducible command.
- Record only after the user's main task is safe and verified. Logging must not interrupt error recovery or delay the primary task.
- Do not list, search, or read existing files under `pending/` before recording. Duplicate detection and consolidation belong to maintainer review.
- Create exactly one new Markdown file per candidate. Do not append to or rewrite an existing entry.
- Name new files `YYYY-MM-DDTHH-mm-ss-short-title.md`. Use a concise lowercase ASCII slug and append a numeric suffix only if that exact path already exists.
- Set `Status` to `pending review`.
- Keep user secrets, authentication data, private asset contents, and unnecessary machine identifiers out of entries.
- Do not promote a candidate into established Skill guidance or code without maintainer review.

## Entry template

```markdown
# Short title

- Status: pending review
- Date: YYYY-MM-DD
- Context: What operation and environment exposed the issue.
- Observation: Exact behavior, error, or warning.
- Evidence: Relevant command, run artifact, or reproducible condition.
- Workaround: What safely unblocked the task.
- Candidate destination: Possible `SKILL.md`, reference, task card, or bridge-code location.
- Review notes: Leave blank for the maintainer.
```

## Maintainer review

Only when review or absorption is explicitly requested, read the files under `pending/`, consolidate duplicates, validate their evidence, and decide whether each candidate should be accepted or rejected. Promote accepted knowledge to the smallest appropriate canonical destination, then remove the reviewed pending files. Do not treat an unreviewed entry as established guidance.
