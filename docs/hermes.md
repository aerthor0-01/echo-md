# Using ECHO.md with Hermes

Hermes keeps its own memory files. `echoctl` doesn't replace them; it records versions of them.

```bash
cd ~/.hermes            # or wherever your Hermes home is
echoctl init --adapter hermes --agent my-hermes
```

Capture before and after sessions, for example from a shell alias or a Hermes hook that runs a command:

```bash
echoctl capture -m "after session"
```

Point the agent at `ECHO.md` for a short summary, and let it run `echoctl history --json` or
`echoctl show vN PATH` when it needs detail. Check hook names against the Hermes version you run.
