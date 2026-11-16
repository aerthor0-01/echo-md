# Contributing

1. Any change to storage behaviour updates **both** runtimes and `SPEC.md` in the same pull request.
2. Run `python3 tests/test_parity.py` (needs Python 3.11+ and Node 22.18+). Add a test for every new rule.
3. Keep both runtimes dependency-free unless there is a strong reason.
4. Don't claim behaviour the tests don't cover.

By contributing you agree your work is licensed under Apache-2.0.
