# Changelog

## 0.1.1 — 2026-11-17

- `restore` now refuses any destination inside the workspace, so restored copies are never captured as new files. Docs use `--to ../restored`.
- Secret check also skips Stripe `sk_live_`/`sk_test_`/`rk_` keys, GitHub `github_pat_` tokens, Google `AIza` keys and JWTs.
- Install with `pipx` or a venv (plain `pip install` fails on externally managed Pythons); Node users get an `echoctl` alias line.
- Clearer TypeScript `diff` output; `npm test` runs the cross-runtime suite.

## 0.1.0 — 2026-11-16
- First public release: `init`, `status`, `capture`, `history`, `diff`, `show`, `verify`, `restore`, `receipt`.
- Python and TypeScript runtimes sharing schema version 1, with cross-runtime tests.
- `generic` and `hermes` adapters; bounded `ECHO.md` index.
