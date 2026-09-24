# OQL standard ownership

This repository owns a domain standard, not an OQL runtime or deployment service.
Normative requirements live in policy.json. Keep documentation consistent with it.
Do not add a second OQL parser: validate review metadata and delegate grammar to
adopters. Examples are synthetic, secret-free and never execution authority.

Use the primary checkout's Planfile allocator and controller-issued lease. The
active initial ticket is PLF-001, mapped to ticket-001. Worktrees follow the host
Wellmanifest v5 policy. One writer per ticket; preserve other checkouts.

Run `python3 -m unittest discover -s tests -v`, both example conformance commands,
and pinned Docs/DSL manifest checks before publication. No live device operations
are part of standard validation. Record local commit, push/PR and merge separately.
Cross-repository audit is owned by subactor/docs ticket-210; link to it here.
