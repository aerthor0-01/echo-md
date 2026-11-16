# Roadmap

Not built yet — contributions welcome.

- `watch`: debounced file watching plus a reconcile scan on start.
- MCP server exposing read-only `echo_status`, `echo_history`, `echo_diff`, `echo_read_version`, `echo_verify`.
- `purge`: remove versions and objects containing a leaked secret.
- Published packages (PyPI `echoctl`, npm `@echostate/echoctl` with a compiled build).
- Measured benchmarks: index size vs full history in tokens, RAM and disk growth.
- Optional, explicit upload to Echo Vault with a preview of what leaves the device.
