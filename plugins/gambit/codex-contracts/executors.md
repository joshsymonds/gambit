# Executor registry on native Codex

The external executor registry is a Claude-only executor registry and does not apply to native
Codex. Native Codex dispatch selects the contracted class and its documented built-in or custom
agent fallback directly; it neither reads nor emulates the Claude registry. Executor selection
never changes the class contract or its authority.
