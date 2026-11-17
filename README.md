# ECHO.md

**A compact change journal for your local AI agents. Keep the history on disk, not in the prompt.**

`echoctl` records the files that define an agent — `AGENTS.md`, `MEMORY.md`, `USER.md`, skills — as numbered,
SHA-256-verified versions in a local `.echo/` folder, and keeps a small `ECHO.md` index (4 KB by default) that an
agent can read instead of its whole history.

- No account, no network calls, no telemetry.
- Two interchangeable runtimes, Python and TypeScript, that read and write the same `.echo/` format.
- Restore any version into an empty folder, then verify the bytes that were actually written.
- Apache-2.0.

```text
your-agent/
├── ECHO.md            small, readable index (bounded)
└── .echo/
    ├── config.json    what is tracked and excluded
    ├── history.sqlite versions, file digests, changes, integrity log
    └── objects/       zlib-compressed file contents, keyed by SHA-256
```

## Quickstart

Python 3.11+ (no dependencies):

```bash
git clone https://github.com/aerthor0-01/echo-md && cd echo-md
pipx install ./python                  # or: python3 -m venv .venv && .venv/bin/pip install ./python
cd ~/my-agent && echoctl init --adapter generic   # or --adapter hermes
```

Node 22.18+ (no dependencies):

```bash
alias echoctl="node $PWD/typescript/src/cli.ts"   # add to ~/.bashrc or ~/.zshrc
cd ~/my-agent && echoctl init
```

Then:

```bash
echoctl status                    # what changed since the last capture
echoctl capture -m "before prompt rewrite"
echoctl history --limit 10
echoctl diff v3 v4 --path AGENTS.md
echoctl show v3 MEMORY.md
echoctl verify v4                 # exit code 1 if any stored byte fails its hash
echoctl restore v3 --to ../restored
echoctl receipt v4 > receipt.json # JSON receipt with the manifest digest
```

Add `--json` to any command for output an agent or script can parse.

## What it does not do

- It cannot recover history from before `echoctl init`.
- It records versions when you (or a script) run `capture`; edits in between are not recorded individually.
- A matching hash proves the bytes are the same. It does not prove an agent will behave the same way.
- Secret detection is a pattern check and can miss things. See [SECURITY.md](SECURITY.md).

## Adapters

| Adapter | Tracks by default |
|---|---|
| `generic` | `AGENTS.md`, `CLAUDE.md`, `SOUL.md`, `MEMORY.md`, `USER.md`, `TOOLS.md`, `IDENTITY.md`, `*.md`, `skills/**` |
| `hermes` | `MEMORY.md`, `USER.md`, `SOUL.md`, `AGENTS.md`, `memories/**`, `skills/**` |

Edit `.echo/config.json` to change `include`, `exclude`, `max_file_bytes` or `index_budget_bytes`.
See [docs/hermes.md](docs/hermes.md) for running alongside Hermes memory.

## Echo Vault

`echoctl receipt` uses the same manifest encoding as [Echo Vault](https://vault.echostate.cloud), so the
digest of a local version matches the digest Echo Vault records when you upload the same files. Echo Vault adds
hosted history, change reviews, release labels and continuity reports; this tool stays fully useful without it.

## Project

- [SPEC.md](SPEC.md) — on-disk format both runtimes follow
- [docs/threat-model.md](docs/threat-model.md)
- [docs/roadmap.md](docs/roadmap.md)
- [CONTRIBUTING.md](CONTRIBUTING.md) · [CHANGELOG.md](CHANGELOG.md) · [RELEASING.md](RELEASING.md)

Tests: `python3 tests/test_parity.py` runs both runtimes against the same workspace.
