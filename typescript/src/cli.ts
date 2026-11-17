#!/usr/bin/env node
// Command line interface. Every query supports --json; exit codes: 0 ok, 1 problem found, 2 usage/error.
import * as path from "node:path";
import { parseArgs } from "node:util";
import { EchoError, Workspace } from "./core.ts";

const VERSION = "0.1.1";
const v = (s: string) => Number.parseInt(s.replace(/^v/i, ""), 10);
const USAGE = `echoctl ${VERSION} (typescript): local change journal for agent files

  init [path] [--agent NAME] [--adapter generic|hermes]
  status
  capture [-m LABEL]
  history [--limit N]
  diff vA vB [--path FILE]
  show vN PATH
  verify [vN]
  restore vN --to DIR
  receipt [vN]

Add --json to any query for machine-readable output.`;

function lineDiff(a: string[], b: string[], max: number): string[] {
  // Small LCS diff, enough for agent files (size-limited by config).
  const n = a.length, m = b.length; const dp = Array.from({ length: n + 1 }, () => new Int32Array(m + 1));
  for (let i = n - 1; i >= 0; i--) for (let j = m - 1; j >= 0; j--) dp[i][j] = a[i] === b[j] ? dp[i + 1][j + 1] + 1 : Math.max(dp[i + 1][j], dp[i][j + 1]);
  const out: string[] = []; let i = 0, j = 0;
  while ((i < n || j < m) && out.length < max) {
    if (i < n && j < m && a[i] === b[j]) { i++; j++; }
    else if (i < n && (j >= m || dp[i + 1][j] >= dp[i][j + 1])) out.push("  - " + a[i++]);
    else out.push("  + " + b[j++]);
  }
  return out;
}

function main(argv: string[]): number {
  const { values: o, positionals: p } = parseArgs({ args: argv, allowPositionals: true, options: {
    json: { type: "boolean" }, agent: { type: "string" }, adapter: { type: "string", default: "generic" }, label: { type: "string", short: "m" },
    limit: { type: "string", default: "10" }, path: { type: "string" }, content: { type: "boolean" }, to: { type: "string" }, version: { type: "boolean" }, help: { type: "boolean", short: "h" },
  } });
  const say = (data: unknown, text: string) => console.log(o.json ? JSON.stringify(data, null, 2) : text);
  const [cmd, ...rest] = p;
  if (o.version) { console.log(`echoctl ${VERSION} (typescript)`); return 0; }
  if (!cmd || o.help) { console.log(USAGE); return cmd ? 0 : 2; }
  try {
    switch (cmd) {
      case "init": {
        if (o.adapter !== "generic" && o.adapter !== "hermes") throw new EchoError("--adapter must be generic or hermes");
        const ws = new Workspace(rest[0] ?? "."); ws.init(o.agent ?? path.basename(ws.root), o.adapter);
        const r = ws.capture("baseline");
        say({ version: r.version, files: r.changes.length, skipped: r.skipped }, `Initialised ${ws.root}\nCaptured v${r.version} baseline with ${r.changes.length} file(s).` + r.skipped.map((s) => `\n  skipped ${s}`).join(""));
        return 0;
      }
      case "status": {
        const ws = Workspace.find(process.cwd()); const r = ws.pending();
        say({ latest: ws.latest(), pending: r.changes, skipped: r.skipped }, [`Latest: v${ws.latest()}`, r.changes.length ? "Changes since last capture:" : "No changes since last capture.", ...r.changes.map((c) => `  ${c.change.padEnd(8)} ${c.path}`), ...r.skipped.map((s) => `  skipped  ${s}`)].join("\n"));
        return 0;
      }
      case "capture": {
        const ws = Workspace.find(process.cwd()); const r = ws.capture(o.label ?? "");
        if (r.version === null) say({ version: null }, "Nothing changed; no new version.");
        else say({ version: r.version, changes: r.changes, skipped: r.skipped }, `Captured v${r.version}: ` + r.changes.map((c) => `${c.path} ${c.change}`).join(", "));
        return 0;
      }
      case "history": {
        const h = Workspace.find(process.cwd()).history(Number(o.limit));
        say(h, h.map((x) => `v${x.version}  ${x.captured_at}  ${x.file_count} files  ${x.label}\n` + x.changes.slice(0, 20).map((c) => `    ${c.change.padEnd(8)} ${c.path}\n`).join("")).join("").trimEnd() || "No versions yet.");
        return 0;
      }
      case "diff": {
        const ws = Workspace.find(process.cwd()); if (rest.length < 2) throw new EchoError("usage: diff vA vB");
        const A = new Map(ws.files(v(rest[0])).map((f) => [f.path, f])); const B = new Map(ws.files(v(rest[1])).map((f) => [f.path, f]));
        let paths = [...new Set([...A.keys(), ...B.keys()])].sort(); if (o.path) paths = paths.filter((x) => x === o.path);
        const rows: { path: string; change: string }[] = []; const text: string[] = [];
        for (const x of paths) {
          const fa = A.get(x), fb = B.get(x); if (fa && fb && fa.sha256 === fb.sha256) continue;
          const change = !fa ? "added" : !fb ? "removed" : "modified"; rows.push({ path: x, change }); if (text.length) text.push(""); text.push(`${change.padEnd(8)} ${x}`);
          if (o.path || o.content) text.push(...lineDiff(fa ? ws.getObject(fa.sha256).toString("utf8").split("\n") : [], fb ? ws.getObject(fb.sha256).toString("utf8").split("\n") : [], 200));
        }
        say(rows, text.join("\n") || "No differences."); return 0;
      }
      case "show": {
        const ws = Workspace.find(process.cwd()); const f = ws.files(v(rest[0])).find((x) => x.path === rest[1]);
        if (!f) throw new EchoError(`${rest[1]} not in ${rest[0]}`); process.stdout.write(ws.getObject(f.sha256)); return 0;
      }
      case "verify": {
        const ws = Workspace.find(process.cwd()); const ver = rest[0] ? v(rest[0]) : ws.latest()!; const pr = ws.verify(ver);
        say({ version: ver, ok: !pr.length, problems: pr }, `v${ver}: ` + (pr.length ? "FAILED\n  " + pr.join("\n  ") : "verified")); return pr.length ? 1 : 0;
      }
      case "restore": {
        if (!o.to) throw new EchoError("restore needs --to DIR"); const pr = Workspace.find(process.cwd()).restore(v(rest[0]), o.to);
        say({ ok: !pr.length, problems: pr }, `Restored ${rest[0]} to ${o.to}: ` + (pr.length ? "mismatch in " + pr.join(", ") : "bytes verified")); return pr.length ? 1 : 0;
      }
      case "receipt": {
        const ws = Workspace.find(process.cwd()); console.log(JSON.stringify(ws.receipt(rest[0] ? v(rest[0]) : ws.latest()!), null, 2)); return 0;
      }
      default: console.error(USAGE); return 2;
    }
  } catch (e) {
    if (e instanceof EchoError) { console.error(`echoctl: ${e.message}`); return 2; }
    throw e;
  }
}
process.exitCode = main(process.argv.slice(2));
