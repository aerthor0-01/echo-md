# ECHO.md — one-page pitch

**Problem.** An AI agent is defined by a folder of text files that change constantly. When behaviour shifts,
nobody can say which version was running, and stuffing the whole history into the prompt wastes context.

**What we built.** A local, zero-telemetry change journal with two interchangeable runtimes (Python and
TypeScript) over one documented format. It stores SHA-256-addressed versions on disk, keeps a bounded
`ECHO.md` index for the agent, and restores any version into a clean folder with byte-level verification.

**Why it's credible.** Cross-runtime tests: each runtime reads, verifies and restores the other's history, detects
tampered objects, skips secrets and symlinks, and keeps the index under its byte budget across 120 versions.

**Honest limits.** No history before `init`; capture is explicit; hashes prove bytes, not behaviour.

**Try it.** `pip install ./python && echoctl init` — Apache-2.0, from EchoState (https://vault.echostate.cloud).
