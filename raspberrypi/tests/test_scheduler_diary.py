"""Check scheduled diary commands with mocked runners, without dispatching Actions."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


RASPBERRYPI = Path(__file__).resolve().parents[1]
RUNNER_MOCK = r'''
import json, os, sys, time
from pathlib import Path

args = sys.argv[1:]
assert args[:3] == ["--repo", "noraworld/diary-templates-assistant", "--workflow"]
assert len(args) == 4
workflow = args[3]
assert workflow in ("batch.yml", "batch-work.yml")
root = Path(os.environ["MOCK_ROOT"])
(root / (workflow + ".started")).write_text(json.dumps(args))
peer = "batch-work.yml" if workflow == "batch.yml" else "batch.yml"
deadline = time.monotonic() + 5
while not (root / (peer + ".started")).exists():
    if time.monotonic() >= deadline:
        sys.exit("The other workflow was not started while this one was running")
    time.sleep(0.02)
sys.exit(1 if os.environ["FAILED_WORKFLOW"] == workflow else 0)
'''


class SchedulerDiaryTest(unittest.TestCase):
    def test_cron_commands_run_independently_and_preserve_exit_status(self):
        entries = []
        for line in (RASPBERRYPI / "schedules.cron").read_text().splitlines():
            fields = line.split()
            if fields[5:7] in (["scheduler", "diary-batch"], ["scheduler", "work-batch"]):
                self.assertEqual(fields[:5], ["59", "6", "*", "*", "*"])
                self.assertEqual(len(fields), 7)
                entries.append(fields[6])
        self.assertCountEqual(entries, ["diary-batch", "work-batch"])

        for failed_workflow in ("", "batch.yml", "batch-work.yml"):
            with self.subTest(failed_workflow=failed_workflow), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                runner = root / "gwr"
                runner.write_text(f"#!{sys.executable}\n" + RUNNER_MOCK)
                runner.chmod(0o755)
                garnish = root / "garnish"
                garnish.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$MOCK_ROOT/garnish-calls"\n')
                garnish.chmod(0o755)
                env = dict(os.environ, PATH=f"{root}:/usr/bin:/bin", MOCK_ROOT=directory,
                           FAILED_WORKFLOW=failed_workflow)
                processes = []
                try:
                    for service in entries:
                        process = subprocess.Popen(
                            ["/bin/sh", str(RASPBERRYPI / "bin" / "scheduler"), service],
                            env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                        processes.append((service, process))
                    for service, process in processes:
                        _, stderr = process.communicate(timeout=10)
                        workflow = "batch.yml" if service == "diary-batch" else "batch-work.yml"
                        self.assertEqual(process.returncode, int(failed_workflow == workflow), stderr)
                    self.assertEqual((root / "garnish-calls").read_text(), "wipe --force\n")
                finally:
                    for _, process in processes:
                        if process.poll() is None:
                            process.kill()
                            process.communicate()


if __name__ == "__main__":
    unittest.main()
