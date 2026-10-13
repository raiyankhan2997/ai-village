# Agent governance audit

Keyword check of each agent's instructions against a responsible-AI checklist.
It shows what the instructions say, not how the agent behaves.

## content-creator  (4/6 controls found)
- Model: sonnet  |  Tools: WebSearch, WebFetch, Read, Write, Bash
- Elevated tools to review: Write (can create/overwrite files); Bash (can run shell commands)
- [ ] No invented facts — Reduces fabricated numbers and sources
- [x] Sources / evidence required — Makes claims checkable by a human
- [ ] Legal / compliance check — Flags legal risk before anything is acted on
- [x] Human review before use — Keeps a person accountable for outputs
- [x] Explicit prohibitions — States what the agent must not do
- [x] Honest about uncertainty — Encourages the agent to flag what it doesn't know

## researcher  (6/6 controls found)
- Model: sonnet  |  Tools: WebSearch, WebFetch, Read, Write, Bash
- Elevated tools to review: Write (can create/overwrite files); Bash (can run shell commands)
- [x] No invented facts — Reduces fabricated numbers and sources
- [x] Sources / evidence required — Makes claims checkable by a human
- [x] Legal / compliance check — Flags legal risk before anything is acted on
- [x] Human review before use — Keeps a person accountable for outputs
- [x] Explicit prohibitions — States what the agent must not do
- [x] Honest about uncertainty — Encourages the agent to flag what it doesn't know

## university  (5/6 controls found)
- Model: sonnet  |  Tools: WebSearch, WebFetch, Read, Write, Bash
- Elevated tools to review: Write (can create/overwrite files); Bash (can run shell commands)
- [x] No invented facts — Reduces fabricated numbers and sources
- [x] Sources / evidence required — Makes claims checkable by a human
- [ ] Legal / compliance check — Flags legal risk before anything is acted on
- [x] Human review before use — Keeps a person accountable for outputs
- [x] Explicit prohibitions — States what the agent must not do
- [x] Honest about uncertainty — Encourages the agent to flag what it doesn't know
