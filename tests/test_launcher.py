"""Run the installed launcher against local CLI stubs; no model calls."""

import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "aspera.sh"
STUB = r'''
import json, os, signal, sys
from pathlib import Path
args = sys.argv[1:]
with open(os.environ["STUB_CALLS"], "a") as f:
    f.write(json.dumps(args) + "\n")
sys.stdin.read()
def event(name):
    with open(os.environ[name], "w") as f:
        f.write(str(os.getpid()))
def stop(signum, frame):
    event("STUB_STOPPED")
    with open(os.environ["STUB_STOP_GATE"], "rb") as f:
        f.read(1)
    os._exit(143)
if "STUB_READY" in os.environ:
    signal.signal(signal.SIGTERM, stop)
    event("STUB_READY")
    with open(os.environ["STUB_GATE"], "rb") as f:
        f.read(1)
mode = os.environ.get("STUB_MODE", "ok")
if mode == "fail":
    sys.exit(9)
report = "fixture review\n"
if mode == "empty":
    report = ""
elif mode == "blank":
    report = " \n\t"
if Path(sys.argv[0]).name == "claude":
    model = args[args.index("--model") + 1]
    data = dict(subtype="success", is_error=False, result=report, modelUsage={model: {}})
    if mode == "error":
        data["is_error"] = True
    elif mode == "bad-subtype":
        data["subtype"] = "error_during_execution"
    elif mode == "mismatch":
        data["modelUsage"] = {"other-model": {}}
    print("{broken" if mode == "malformed" else json.dumps(data))
elif mode != "missing":
    Path(args[args.index("-o") + 1]).write_text(report)
'''


class LauncherTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="aspera-test-")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        for name in ("codex", "claude"):
            stub = self.bin / name
            stub.write_text(f"#!{sys.executable}\n" + STUB)
            stub.chmod(0o700)
        self.target = self.root / "target.md"
        self.target.write_text("Fixture target.\n")
        self.brief = self.root / "brief.md"
        self.brief.write_text("Read-only fixture review.\n")
        self.calls = self.root / "calls.jsonl"
        self.out = self.root / "runs"
        self.env = {k: v for k, v in os.environ.items()
                    if not k.startswith(("ASPERA_", "STUB_")) and k != "CODEX_THREAD_ID"}
        self.env.update(PATH=str(self.bin) + os.pathsep + os.environ["PATH"],
                        HOME=str(self.root), STUB_CALLS=str(self.calls),
                        ASPERA_OUT_DIR=str(self.out))

    def command(self, host="cursor", target=None):
        route = ["--from", host] if host is not None else []
        return ["bash", str(SCRIPT)] + route + ["--target", str(target or self.target),
                "--brief", str(self.brief), "--cd", str(self.root)]

    def run_script(self, command=None, **env):
        return subprocess.run(command or self.command(), env=dict(self.env, **env),
                              capture_output=True, text=True, timeout=10)

    def recorded_calls(self):
        return [json.loads(line) for line in self.calls.read_text().splitlines()] if self.calls.exists() else []

    def assert_success(self, result):
        self.assertEqual(result.returncode, 0, (result.stdout, result.stderr))
        self.assertIn("ASPERA_DONE ", result.stdout)
        self.assertNotIn("ASPERA_FAILED", result.stdout)

    def assert_unlocked(self):
        self.assertEqual(list((self.out / ".locks").iterdir()), [])

    def blocked(self, host="cursor"):
        folder = Path(tempfile.mkdtemp(dir=self.root, prefix="gate-"))
        fds, env = {}, {}
        for name in ("READY", "GATE", "STOPPED", "STOP_GATE"):
            fifo = folder / name
            os.mkfifo(fifo)
            fds[name] = os.open(fifo, os.O_RDWR | os.O_NONBLOCK)
            self.addCleanup(os.close, fds[name])
            env["STUB_" + name] = str(fifo)
        process = subprocess.Popen(self.command(host), env=dict(self.env, **env),
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                   start_new_session=True)

        def cleanup():
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.communicate(timeout=5)

        self.addCleanup(cleanup)
        child = int(self.event(fds["READY"]))
        return process, child, fds

    def event(self, fd):
        self.assertTrue(select.select([fd], [], [], 5)[0], "stub event timed out")
        return os.read(fd, 4096).decode()

    def test_host_routing_and_explicit_overrides(self):
        for host, provider, default in (("codex", "claude", "claude-opus-5-5"),
                                        ("claude", "codex", "gpt-6-astra"),
                                        ("cursor", "codex", "gpt-6-astra")):
            for override in (False, True):
                with self.subTest(host=host, override=override):
                    env = {"ASPERA_MODEL": "explicit-model", "ASPERA_EFFORT": "high"} if override else {}
                    self.assert_success(self.run_script(self.command(host), **env))
                    args = self.recorded_calls()[-1]
                    flag = "--model" if provider == "claude" else "-m"
                    self.assertEqual(args[args.index(flag) + 1], "explicit-model" if override else default)
                    effort = "high" if override else "xhigh"
                    if provider == "claude":
                        self.assertEqual(args[args.index("--effort") + 1], effort)
                        self.assertIn("--safe-mode", args)
                        self.assertIn("--restricted", args)
                    else:
                        self.assertIn("model_reasoning_effort=" + effort, args)
                        self.assertEqual(args[args.index("-s") + 1], "read-only")
                    self.assert_unlocked()

    def test_omitted_host_uses_cursor_astra_default(self):
        self.assert_success(self.run_script(self.command(host=None)))
        args = self.recorded_calls()[-1]
        self.assertEqual(args[args.index("-m") + 1], "gpt-6-astra")
        self.assertIn("model_reasoning_effort=xhigh", args)
        self.assertEqual(args[args.index("-s") + 1], "read-only")
        self.assert_unlocked()

    def test_codex_context_requires_explicit_host_before_launch(self):
        result = self.run_script(self.command(host=None), CODEX_THREAD_ID="fixture-codex-thread")
        self.assertEqual(result.returncode, 2, (result.stdout, result.stderr))
        self.assertIn("Pass --from codex, claude or cursor when CODEX_THREAD_ID is set", result.stderr)
        self.assertIn("ASPERA_FAILED", result.stdout)
        self.assertNotIn("ASPERA_DONE", result.stdout)
        self.assertEqual(self.recorded_calls(), [])

    def test_argument_errors_do_not_launch(self):
        for command, message in ((self.command("unknown"), "--from must be codex, claude or cursor"),
                                 (["bash", str(SCRIPT), "--target"], "Missing value for --target")):
            with self.subTest(command=command):
                result = self.run_script(command)
                self.assertEqual(result.returncode, 2, (result.stdout, result.stderr))
                self.assertIn(message, result.stderr)
                self.assertIn("ASPERA_FAILED", result.stdout)
                self.assertNotIn("ASPERA_DONE", result.stdout)
                self.assertEqual(self.recorded_calls(), [])

    def test_invalid_claude_json_fails_and_allows_retry(self):
        for mode in ("malformed", "error", "bad-subtype", "empty", "blank", "mismatch"):
            with self.subTest(mode=mode):
                result = self.run_script(self.command("codex"), STUB_MODE=mode)
                self.assertEqual(result.returncode, 1, (result.stdout, result.stderr))
                self.assertIn("ASPERA_FAILED", result.stdout)
                self.assertNotIn("ASPERA_DONE", result.stdout)
                self.assert_unlocked()
                self.assert_success(self.run_script(self.command("codex")))

    def test_codex_failure_and_blank_review_allow_retry(self):
        for mode, code in (("fail", 9), ("missing", 1), ("empty", 1), ("blank", 1)):
            with self.subTest(mode=mode):
                result = self.run_script(STUB_MODE=mode)
                self.assertEqual(result.returncode, code, (result.stdout, result.stderr))
                self.assertIn("ASPERA_FAILED", result.stdout)
                self.assertNotIn("ASPERA_DONE", result.stdout)
                self.assert_unlocked()
                self.assert_success(self.run_script())

    def test_duplicate_rejected_but_distinct_target_path_runs(self):
        process, _, fds = self.blocked()
        duplicate = self.run_script()
        self.assertEqual(duplicate.returncode, 75, duplicate.stderr)
        self.assertIn("already owned", duplicate.stderr)
        self.assertIn(f"pid={process.pid}", duplicate.stderr)
        self.assertEqual(len(self.recorded_calls()), 1)
        other = self.root / "other.md"
        other.write_text(self.target.read_text())
        self.assert_success(self.run_script(self.command(target=other)))
        self.assertEqual(len(self.recorded_calls()), 2)
        os.write(fds["GATE"], b"x")
        stdout, stderr = process.communicate(timeout=10)
        self.assertEqual(process.returncode, 0, (stdout, stderr))
        self.assert_unlocked()
        self.assert_success(self.run_script())

    def test_cancellation_holds_lock_until_own_child_stops(self):
        for host in ("cursor", "codex"):
            with self.subTest(host=host):
                before = len(self.recorded_calls())
                process, child, fds = self.blocked(host)
                process.send_signal(signal.SIGTERM)
                self.assertEqual(int(self.event(fds["STOPPED"])), child)
                os.kill(child, 0)
                duplicate = self.run_script(self.command(host))
                self.assertEqual(duplicate.returncode, 75, duplicate.stderr)
                self.assertEqual(len(self.recorded_calls()), before + 1)
                os.write(fds["STOP_GATE"], b"x")
                stdout, stderr = process.communicate(timeout=15)
                self.assertEqual(process.returncode, 143, (stdout, stderr))
                self.assertIn("ASPERA_FAILED", stdout)
                self.assertNotIn("ASPERA_DONE", stdout)
                with self.assertRaises(ProcessLookupError):
                    os.kill(child, 0)
                self.assert_unlocked()
                self.assert_success(self.run_script(self.command(host)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
