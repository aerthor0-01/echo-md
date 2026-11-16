"""Command line interface. Every query supports --json; exit codes: 0 ok, 1 problem found, 2 usage/error."""
from __future__ import annotations

import argparse
import difflib
import json
import sys
from pathlib import Path

from . import __version__
from .core import EchoError, Workspace


def _v(s: str) -> int:
    return int(s.lstrip("vV"))


def out(args, data, text: str) -> None:
    print(json.dumps(data, indent=2) if args.json else text)


def cmd_init(a):
    ws = Workspace(Path(a.path))
    ws.init(a.agent or ws.root.name, a.adapter)
    v, changes, skipped = ws.capture("baseline")
    out(a, {"version": v, "files": len(changes), "skipped": skipped},
        f"Initialised {ws.root}\nCaptured v{v} baseline with {len(changes)} file(s)." + "".join(f"\n  skipped {s}" for s in skipped))


def cmd_status(a):
    ws = Workspace.find(Path.cwd())
    changes, _, skipped = ws.pending()
    data = {"latest": ws.latest(), "pending": [{"path": p, "change": c} for p, c in changes], "skipped": skipped}
    lines = [f"Latest: v{ws.latest()}", "No changes since last capture." if not changes else "Changes since last capture:"]
    lines += [f"  {c:<8} {p}" for p, c in changes] + [f"  skipped  {s}" for s in skipped]
    out(a, data, "\n".join(lines))


def cmd_capture(a):
    ws = Workspace.find(Path.cwd())
    v, changes, skipped = ws.capture(a.label or "")
    if v is None:
        out(a, {"version": None}, "Nothing changed; no new version.")
        return 0
    out(a, {"version": v, "changes": [{"path": p, "change": c} for p, c in changes], "skipped": skipped},
        f"Captured v{v}: " + ", ".join(f"{p} {c}" for p, c in changes))


def cmd_history(a):
    ws = Workspace.find(Path.cwd())
    h = ws.history(a.limit)
    text = "\n".join(f"v{x['version']}  {x['captured_at']}  {x['file_count']} files  {x['label']}\n" + "".join(f"    {c['change']:<8} {c['path']}\n" for c in x["changes"][:20]) for x in h)
    out(a, h, text.rstrip() or "No versions yet.")


def cmd_diff(a):
    ws = Workspace.find(Path.cwd())
    A = {f.path: f for f in ws.files(_v(a.a))}
    B = {f.path: f for f in ws.files(_v(a.b))}
    paths = sorted(set(A) | set(B))
    if a.path:
        paths = [p for p in paths if p == a.path]
    rows, text = [], []
    for p in paths:
        fa, fb = A.get(p), B.get(p)
        if fa and fb and fa.sha256 == fb.sha256:
            continue
        kind = "added" if not fa else "removed" if not fb else "modified"
        rows.append({"path": p, "change": kind})
        text.append(f"{kind:<8} {p}")
        if a.path or a.content:
            old = ws.get_object(fa.sha256).decode("utf-8", "replace").splitlines() if fa else []
            new = ws.get_object(fb.sha256).decode("utf-8", "replace").splitlines() if fb else []
            d = list(difflib.unified_diff(old, new, f"{a.a}/{p}", f"{a.b}/{p}", lineterm=""))[: a.max_lines]
            text += d
    out(a, rows, "\n".join(text) or "No differences.")


def cmd_show(a):
    ws = Workspace.find(Path.cwd())
    f = next((f for f in ws.files(_v(a.version)) if f.path == a.path), None)
    if not f:
        raise EchoError(f"{a.path} not in {a.version}")
    sys.stdout.write(ws.get_object(f.sha256).decode("utf-8", "replace"))


def cmd_verify(a):
    ws = Workspace.find(Path.cwd())
    v = _v(a.version) if a.version else ws.latest()
    problems = ws.verify(v)
    out(a, {"version": v, "ok": not problems, "problems": problems}, f"v{v}: " + ("verified" if not problems else "FAILED\n  " + "\n  ".join(problems)))
    return 1 if problems else 0


def cmd_restore(a):
    ws = Workspace.find(Path.cwd())
    problems = ws.restore(_v(a.version), Path(a.to))
    out(a, {"ok": not problems, "problems": problems}, f"Restored {a.version} to {a.to}: " + ("bytes verified" if not problems else "mismatch in " + ", ".join(problems)))
    return 1 if problems else 0


def cmd_receipt(a):
    ws = Workspace.find(Path.cwd())
    print(json.dumps(ws.receipt(_v(a.version) if a.version else ws.latest()), indent=2))


def build() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="echoctl", description="Local change journal for agent files.")
    p.add_argument("--version", action="version", version=f"echoctl {__version__} (python)")
    sub = p.add_subparsers(dest="cmd", required=True)
    def add(name, fn, help):
        s = sub.add_parser(name, help=help); s.set_defaults(fn=fn); s.add_argument("--json", action="store_true"); return s
    s = add("init", cmd_init, "start tracking a folder"); s.add_argument("path", nargs="?", default="."); s.add_argument("--agent"); s.add_argument("--adapter", choices=["generic", "hermes"], default="generic")
    add("status", cmd_status, "show changes since the last capture")
    s = add("capture", cmd_capture, "record a new version"); s.add_argument("-m", "--label")
    s = add("history", cmd_history, "list versions"); s.add_argument("--limit", type=int, default=10)
    s = add("diff", cmd_diff, "compare two versions"); s.add_argument("a"); s.add_argument("b"); s.add_argument("--path"); s.add_argument("--content", action="store_true"); s.add_argument("--max-lines", type=int, default=200)
    s = add("show", cmd_show, "print a file from a version"); s.add_argument("version"); s.add_argument("path")
    s = add("verify", cmd_verify, "check stored bytes against the manifest"); s.add_argument("version", nargs="?")
    s = add("restore", cmd_restore, "rebuild a version into an empty folder"); s.add_argument("version"); s.add_argument("--to", required=True)
    s = add("receipt", cmd_receipt, "print a JSON receipt for a version"); s.add_argument("version", nargs="?")
    return p


def main(argv=None) -> int:
    a = build().parse_args(argv)
    try:
        return a.fn(a) or 0
    except EchoError as e:
        print(f"echoctl: {e}", file=sys.stderr)
        return 2
