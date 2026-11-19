"""Offline behavior checks: python3 -m unittest discover -s raspberrypi/tests."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


RUNNER = Path(__file__).resolve().parents[1] / "bin" / "gwr"
MOCK = r'''
import json, os, sys
from pathlib import Path

root = Path(os.environ["MOCK_ROOT"])
name = Path(sys.argv[0]).name
args = sys.argv[1:]
with (root / "calls").open("a") as f:
    f.write(json.dumps([name] + args) + "\n")
config = json.loads((root / "config").read_text())
if name == "flock":
    with (root / "calls").open("a") as f:
        f.write(json.dumps(["lock-path", next(root.glob("*.lock")).name]) + "\n")
    sys.exit(config.get("lock_status", 0))
if name == "sleep":
    sys.exit(0)
assert name == "ghc"
assert os.environ["GHC_FROM"].startswith("gwr")
repo = config.get("repo", "noraworld/diary-templates-assistant")
workflow = config.get("workflow", "batch.yml")
if args[:2] == ["api", f"repos/{repo}"]:
    print("main")
elif args[:3] == ["api", "--method", "POST"]:
    assert args[3] == f"repos/{repo}/actions/workflows/{workflow}/dispatches"
    assert "X-GitHub-Api-Version: 2026-03-10" in args
    assert "ref=main" in args
    print(config.get("run_id", "123"))
    sys.exit(config.get("dispatch_status", 0))
elif args[:2] == ["api", f"repos/{repo}/actions/runs/123"]:
    counter = root / "poll_count"
    index = int(counter.read_text()) if counter.exists() else 0
    counter.write_text(str(index + 1))
    states = config["states"]
    state = states[min(index, len(states) - 1)]
    if state == "API_ERROR":
        sys.exit(1)
    print(state)
elif args[:3] == ["run", "rerun", "123"]:
    assert args[3:] == ["--failed", "--repo", repo]
    sys.exit(config.get("rerun_status", 0))
else:
    raise AssertionError(args)
'''


class GwrTest(unittest.TestCase):
    def run_case(self, states, expected_status=0, reruns=0, dispatches=1,
                 options=None, extra_options=(), **config):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "config").write_text(json.dumps(dict(states=states, **config)))
            for name in ("ghc", "sleep", "flock"):
                executable = root / name
                executable.write_text(f"#!{sys.executable}\n" + MOCK)
                executable.chmod(0o755)
            env = dict(os.environ, PATH=f"{root}:{os.environ['PATH']}",
                       TMPDIR=directory, MOCK_ROOT=directory)
            if options is None:
                options = ["--repo", config.get("repo", "noraworld/diary-templates-assistant"),
                           "--workflow", config.get("workflow", "batch.yml")]
            result = subprocess.run(["/bin/sh", str(RUNNER), *options, *extra_options], env=env,
                                    capture_output=True, text=True, timeout=15)
            call_file = root / "calls"
            calls = [json.loads(line) for line in call_file.read_text().splitlines()] if call_file.exists() else []
            self.assertEqual(result.returncode, expected_status, result.stderr)
            self.assertEqual(sum(c[:3] == ["ghc", "run", "rerun"] for c in calls), reruns)
            self.assertEqual(sum(c[:4] == ["ghc", "api", "--method", "POST"] for c in calls), dispatches)
            return calls, result.stderr

    def test_success_waits_for_completion(self):
        calls, _ = self.run_case(["1 queued pending", "1 in_progress pending", "1 completed success"])
        self.assertEqual(sum(c == ["sleep", "60"] for c in calls), 2)

    def test_rerun_ignores_stale_completion(self):
        self.run_case(["1 completed failure", "1 completed failure", "2 queued pending",
                       "2 completed success"], reruns=1)

    def test_success_on_fifth_attempt(self):
        self.run_case([f"{n} completed failure" for n in range(1, 5)] +
                      ["5 completed success"], reruns=4)

    def test_five_failures_exit_nonzero(self):
        self.run_case([f"{n} completed failure" for n in range(1, 6)],
                      expected_status=1, reruns=4)

    def test_temporary_api_error_does_not_rerun(self):
        self.run_case(["API_ERROR", "1 completed success"])

    def test_persistent_api_errors_exit_without_rerun(self):
        calls, _ = self.run_case(["API_ERROR"], expected_status=1)
        self.assertEqual(sum(c[:2] == ["ghc", "api"] for c in calls), 7)

    def test_dispatch_error_is_not_retried(self):
        self.run_case([], expected_status=1, dispatch_status=1)

    def test_missing_run_id_does_not_select_another_run(self):
        self.run_case([], expected_status=1, run_id="null")

    def test_rerun_error_is_not_retried(self):
        self.run_case(["1 completed failure"], expected_status=1, reruns=1, rerun_status=1)

    def test_timeout_does_not_rerun(self):
        self.run_case(["1 in_progress pending"], expected_status=1,
                      extra_options=["--max-poll-count", "3"])

    def test_stale_rerun_eventually_times_out(self):
        self.run_case(["1 completed failure"], expected_status=1, reruns=1,
                      extra_options=["--max-poll-count", "3"])

    def test_overlapping_invocation_skips_dispatch(self):
        self.run_case([], dispatches=0, lock_status=75)

    def test_lock_error_exits_nonzero(self):
        self.run_case([], expected_status=1, dispatches=0, lock_status=1)

    def test_required_options(self):
        for options in ([], ["--repo", "owner/repo"], ["--workflow", "batch.yml"]):
            with self.subTest(options=options):
                calls, _ = self.run_case([], options=options, expected_status=1, dispatches=0)
                self.assertEqual(calls, [])

    def test_invalid_options_do_not_call_external_commands(self):
        for extra in (["--workflow"], ["--repo="], ["--workflow", ""],
                      ["--unknown", "1"], ["batch.yml"], ["--poll-interval", "--workflow"]):
            with self.subTest(extra=extra):
                calls, _ = self.run_case([], extra_options=extra, expected_status=1, dispatches=0)
                self.assertEqual(calls, [])

    def test_invalid_numeric_options(self):
        for option in ("--max-attempts", "--poll-interval", "--max-poll-count", "--max-api-failures"):
            for value in ("0", "-1", "1.5", "abc", "", "999999999999999999999"):
                with self.subTest(option=option, value=value):
                    calls, _ = self.run_case([], extra_options=[f"{option}={value}"],
                                             expected_status=1, dispatches=0)
                    self.assertEqual(calls, [])

    def test_help_without_required_options(self):
        for flag in ("-h", "--help"):
            calls, _ = self.run_case([], options=[flag], dispatches=0)
            self.assertEqual(calls, [])

    def test_custom_repository_and_workflow(self):
        self.run_case(["1 completed failure", "2 completed success"], reruns=1,
                      repo="other/project", workflow="batch-work.yml")

    def test_equals_syntax(self):
        self.run_case(["1 completed success"],
                      options=["--repo=noraworld/diary-templates-assistant", "--workflow=batch.yml"])

    def test_custom_attempt_limit(self):
        self.run_case(["1 completed failure", "2 completed failure"], expected_status=1,
                      reruns=1, extra_options=["--max-attempts", "2"])

    def test_custom_poll_interval_and_count(self):
        calls, _ = self.run_case(["1 queued pending"], expected_status=1,
                                 extra_options=["--poll-interval", "7", "--max-poll-count", "2"])
        self.assertEqual(sum(c == ["sleep", "7"] for c in calls), 2)

    def test_custom_api_failure_limit(self):
        calls, _ = self.run_case(["API_ERROR"], expected_status=1,
                                 extra_options=["--max-api-failures", "2"])
        self.assertEqual(sum(c[:2] == ["ghc", "api"] for c in calls), 4)

    def test_lock_is_scoped_to_repository_and_workflow(self):
        def lock_name(**config):
            calls, _ = self.run_case(["1 completed success"], **config)
            return next(c[1] for c in calls if c[0] == "lock-path")

        default = lock_name()
        self.assertEqual(default, lock_name())
        self.assertNotEqual(default, lock_name(workflow="batch-work.yml"))
        self.assertNotEqual(default, lock_name(repo="other/project"))


if __name__ == "__main__":
    unittest.main()
