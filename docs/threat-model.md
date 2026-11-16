# Threat model

| Risk | Mitigation | Limit |
|---|---|---|
| Secrets copied into history | Default exclusions and pattern check before storing | Patterns miss novel formats; rotate and purge |
| Symlink or `..` escape | Symlinks skipped, paths validated on capture and restore | — |
| Damaged or edited objects | `verify` re-hashes every object and the manifest | Someone controlling the machine can rewrite both |
| Restore overwrites work | Restore refuses non-empty folders and the workspace | — |
| Prompt injection from old files | Index marks history as untrusted data; nothing is executed | Agents must still treat it as data |
| Interrupted capture | Objects written atomically, version committed in one transaction | Orphan objects may remain (harmless) |
| Data leaving the machine | No network code in either runtime | — |
