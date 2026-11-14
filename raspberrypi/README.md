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

`bin/diary-batch-runner` dispatches `batch.yml` in
`noraworld/diary-templates-assistant` and monitors that run using `ghc`.
It requires an authenticated GitHub CLI through `ghc` and `flock` (util-linux).
The dispatch uses GitHub REST API version `2026-03-10` to obtain the exact run ID.

`MAX_ATTEMPTS=5` includes the initial execution, allowing up to four reruns.
Reruns use `--failed` to resume failed jobs and their dependents. A successful
run exits with status 0; exhausted attempts or API errors exit with status 1.
Monitoring retries temporary API errors up to `MAX_API_FAILURES` consecutive
failures, polling every `POLL_INTERVAL=60` seconds. `MAX_POLL_COUNT=180`
limits each attempt to roughly 3 hours of monitoring. These constants are
defined at the top of the script.

Overlapping invocations by the same OS user skip execution while the runner
holds its lock. After a monitoring timeout, interrupted runner, or dispatch
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
