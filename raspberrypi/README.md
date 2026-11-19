# About internet fasting mode
Internet fasting mode is a system that restricts certain websites and/or services you may be unable to stop watching but want to stop, such as YouTube and Netflix.

## Why internet fasting is needed?
Unfortunately, certain websites and services cause an addiction, and you probably can’t realize you are affected by them.

The purpose is to reduce the amount of the digital dopamine in your brain and release you from the addiction.

## Tips
* You will be probably mentally hard **at first 12 hours** since you start it, but keep it in mind that it will make you feel better after you overcome it
* You will feel good quite after you try it **for a month**
* The longer you continue it, the more it can take effect

For more details, see [a YouTube clip (Japanese)](https://www.youtube.com/watch?v=SWFRdY5E0B0).

## Diary batch runner

`bin/diary-batch-runner` dispatches a workflow and monitors that run using `ghc`.
Both `--repo` and `--workflow` are required:

```shell
diary-batch-runner --repo noraworld/diary-templates-assistant --workflow batch.yml
diary-batch-runner --repo noraworld/diary-templates-assistant --workflow batch-work.yml --max-attempts 3
```

It requires an authenticated GitHub CLI through `ghc`, `flock` (util-linux),
and `sha256sum` (coreutils).
The dispatch uses GitHub REST API version `2026-03-10` to obtain the exact run ID.

The following options are optional and accept positive integers:

| Option | Default | Meaning |
| --- | --- | --- |
| `--max-attempts` | `5` | Total attempts, including the initial execution |
| `--poll-interval` | `60` | Seconds between status checks |
| `--max-poll-count` | `180` | Maximum status checks per attempt |
| `--max-api-failures` | `5` | Maximum consecutive API failures |

Values must be between 1 and 2147483647. Both `--option VALUE` and
`--option=VALUE` are supported. Use `--help` to display usage.

The default attempt limit includes the initial execution, allowing up to four reruns.
Reruns use `--failed` to resume failed jobs and their dependents. A successful
run exits with status 0; exhausted attempts or API errors exit with status 1.
Missing required options, missing values, and invalid options also exit with
status 1 before any GitHub requests. With the default polling interval and
count, each attempt has roughly 3 hours of monitoring.

Overlapping invocations by the same OS user for the same repository and
workflow skip execution while the runner holds its lock. Different repositories
or workflows use separate locks and can run concurrently. Use consistent
repository spelling and workflow identifiers: file names and numeric IDs for
the same workflow produce different locks.

Callers must pass both required options; a bare `diary-batch-runner` invocation
fails. `scheduler good` runs `batch.yml`, and `scheduler good-work` runs
`batch-work.yml`, both in `noraworld/diary-templates-assistant`.
Separate entries in `schedules.cron` start these commands daily at 06:59 in
the cron daemon's timezone, allowing both workflows to run in parallel.

After a monitoring timeout, interrupted runner, or dispatch
error, check GitHub Actions before launching another batch: the remote run
may still be active.

Offline tests: `python3 -m unittest discover -s raspberrypi/tests`.

## Usage

```shell
# set the period of internet fasting (<NUMBER> is the number of days)
internet-fasting-period set <NUMBER> <TARGET_COUNTER_FILE>

# confirm how many days left
internet-fasting-period get
```

## How it works
When the internet fasting mode is off, Dnsmasq configurations that restrict websites and/or services that distract you are disabled durinig the night. By turning on the internet fasting mode, these configurations remain enabled. Instead, the internet fasting counters, which are managed in specific files, decrease by 1. When the internet fasting counters get 0, Dnsmasq configurations start to be disabled again at night.
