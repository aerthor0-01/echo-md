"""Runs both runtimes against one workspace. Usage: python3 tests/test_parity.py"""
import json, os, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = [sys.executable, "-m", "echoctl"]
TS = ["node", "--no-warnings", str(ROOT / "typescript/src/cli.ts")]
ENV = dict(os.environ, PYTHONPATH=str(ROOT / "python"))


def run(cmd, cwd, *args, ok=(0,)):
    r = subprocess.run([*cmd, *args], cwd=cwd, env=ENV, capture_output=True, text=True)
    assert r.returncode in ok, (cmd, args, r.stdout, r.stderr)
    return r


class Parity(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.ws = self.tmp / "agent"
        (self.ws / "skills/x").mkdir(parents=True)
        (self.ws / "AGENTS.md").write_text("# rules\n")
        (self.ws / "MEMORY.md").write_text("remember\n")
        (self.ws / "skills/x/SKILL.md").write_text("skill\n")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_cross_runtime_history_and_restore(self):
        for first, second in ((PY, TS), (TS, PY)):
            with self.subTest(first=first[0]):
                shutil.rmtree(self.ws / ".echo", ignore_errors=True)
                run(first, self.ws, "init", ".", "--json")
                (self.ws / "AGENTS.md").write_text("# rules\nnew line\n")
                run(second, self.ws, "capture", "-m", "edit")
                h1 = json.loads(run(first, self.ws, "history", "--json").stdout)
                h2 = json.loads(run(second, self.ws, "history", "--json").stdout)
                self.assertEqual(h1, h2)
                self.assertEqual(h1[0]["changes"], [{"path": "AGENTS.md", "change": "modified"}])
                a, b = self.tmp / f"a-{first[0][-4:]}", self.tmp / f"b-{first[0][-4:]}"
                run(first, self.ws, "restore", "v2", "--to", str(a))
                run(second, self.ws, "restore", "v2", "--to", str(b))
                for p in ("AGENTS.md", "MEMORY.md", "skills/x/SKILL.md"):
                    self.assertEqual((a / p).read_bytes(), (b / p).read_bytes())
                self.assertEqual(json.loads(run(first, self.ws, "receipt").stdout)["manifest_digest"], json.loads(run(second, self.ws, "receipt").stdout)["manifest_digest"])
                (self.ws / "AGENTS.md").write_text("# rules\n")

    def test_tamper_detected(self):
        run(PY, self.ws, "init", ".")
        blob = next((self.ws / ".echo/objects").rglob("*.blob"))
        blob.write_bytes(b"garbage")
        for rt in (PY, TS):
            r = run(rt, self.ws, "verify", "v1", "--json", ok=(1,))
            self.assertFalse(json.loads(r.stdout)["ok"])

    def test_secrets_symlinks_and_restore_safety(self):
        (self.ws / "KEYS.md").write_text("token ghp_" + "a" * 36 + "\n")
        (self.ws / ".env").write_text("X=1\n")
        outside = self.tmp / "outside.md"; outside.write_text("private\n")
        (self.ws / "LINK.md").symlink_to(outside)
        run(TS, self.ws, "init", ".")
        files = {f["path"] for f in json.loads(run(PY, self.ws, "receipt").stdout)["files"]}
        self.assertEqual(files, {"AGENTS.md", "MEMORY.md", "skills/x/SKILL.md"})
        for rt in (PY, TS):
            run(rt, self.ws, "restore", "v1", "--to", str(self.ws), ok=(2,))
            run(rt, self.ws, "restore", "v1", "--to", str(self.ws / "restored"), ok=(2,))
            self.assertFalse((self.ws / "restored").exists())

    def test_more_secret_formats_skipped(self):
        samples = {
            "STRIPE.md": "sk_live_" + "A1b2" * 6,
            "GHPAT.md": "github_pat_" + "a1B2_" * 10,
            "GOOGLE.md": "AIza" + "b" * 35,
            "JWT.md": "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N",
        }
        for name, val in samples.items():
            (self.ws / name).write_text(f"key {val}\n")
        for rt in (PY, TS):
            with self.subTest(rt=rt[0]):
                shutil.rmtree(self.ws / ".echo", ignore_errors=True)
                run(rt, self.ws, "init", ".")
                files = {f["path"] for f in json.loads(run(rt, self.ws, "receipt").stdout)["files"]}
                self.assertEqual(files, {"AGENTS.md", "MEMORY.md", "skills/x/SKILL.md"})

    def test_index_stays_within_budget(self):
        run(PY, self.ws, "init", ".")
        for i in range(120):
            (self.ws / f"note-{i:03}-{'x' * 40}.md").write_text(str(i))
            run(PY if i % 2 else TS, self.ws, "capture", "-m", f"change {i}")
        self.assertLessEqual(len((self.ws / "ECHO.md").read_bytes()), 4096)


if __name__ == "__main__":
    unittest.main()
