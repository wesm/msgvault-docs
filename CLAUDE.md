# Claude Code Guidelines

## Writing style

- Never use em dashes (—) or en dashes (–) in documentation text. Use commas, periods, semicolons, colons, or parentheses instead. The only exception is table cells where "—" indicates "none" or "not applicable".

## Technical facts

- msgvault deletion is always permanent. There is no trash mode. `msgvault delete-staged` permanently deletes messages from Gmail. Do not reference "trash", "recoverable", or "30 days" in deletion documentation.
- msgvault requests full Gmail account access (not narrow/minimal scopes). Do not claim it uses restricted or read-only OAuth scopes.

## Git workflow

- Never commit directly to `main`. Always create a feature branch and open a PR.
- Never switch branches without being asked. Stay on the current branch.
- Never push to remote unless explicitly asked.
- Never force push unless explicitly asked.
