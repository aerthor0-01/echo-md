# ECHO format, schema version 1

Both runtimes MUST produce and accept exactly this layout.

## Files
- `ECHO.md` — generated index. Never tracked. At most `index_budget_bytes` (default 4096) UTF-8 bytes.
- `.echo/config.json` — `{agent, adapter, include[], exclude[], max_file_bytes, index_budget_bytes}`.
- `.echo/history.sqlite` — tables below. WAL mode.
- `.echo/objects/<first 2 hex>/<sha256>.blob` — zlib-compressed file bytes. The name is the SHA-256 of the
  **uncompressed** bytes. Written to `.tmp` then renamed. Identical content is stored once.

## Paths
Relative, `/`-separated, no empty, `.` or `..` segments, no leading `/` or drive letter. Symlinks are never
followed. `.echo/` and `ECHO.md` are always excluded. Patterns: `*` matches any characters including `/`;
a pattern without `/` also matches the file name; `dir/**` matches `dir` and everything under it.

## Tables
```sql
captures(version INTEGER PK, captured_at TEXT, label TEXT, manifest_digest TEXT,
         file_count INTEGER, total_bytes INTEGER, consistent INTEGER, runtime TEXT)
capture_files(version, path, sha256, size)          -- full file list per version
changes(version, path, change)                      -- 'added' | 'modified' | 'removed'
integrity_log(id, at, action, version, ok, detail)  -- verify / restore results
meta(key, value)                                    -- schema_version, created_at
```
A version is written in one `BEGIN IMMEDIATE` transaction after its objects exist. Timestamps are UTC
`YYYY-MM-DDTHH:MM:SSZ`.

## Manifest digest
SHA-256 (hex) of the UTF-8 text made of one `path\tsha256\tsize\n` line per file, sorted by path in byte order.
This is the same encoding Echo Vault uses.

## Capture rules
Skip a file if it is larger than `max_file_bytes`, matches a secret pattern (`sk-…`, `gh?_…`, `AKIA…`, `xox?-…`,
private key headers), resolves outside the workspace, or changes size/mtime while being read three times.
