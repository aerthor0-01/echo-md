# Releasing

1. Update the version in `python/pyproject.toml`, `python/echoctl/__init__.py`, `typescript/package.json` and
   `typescript/src/cli.ts`, and add a `CHANGELOG.md` entry.
2. Run `python3 tests/test_parity.py` locally and wait for CI to pass on `main`.
3. Tag: `git tag vX.Y.Z && git push --tags`, then create a GitHub Release from the tag with the changelog text.
4. PyPI (optional): `cd python && python -m build && twine upload dist/*` (needs a PyPI account and token).
5. npm (optional, not ready): Node won't run TypeScript from `node_modules`, so add a compile step to JavaScript
   before publishing `@echostate/echoctl`.
6. Update the download on https://vault.echostate.cloud/open-source to point at the release.
