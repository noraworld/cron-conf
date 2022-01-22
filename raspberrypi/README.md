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

## Usage

```shell
# set the period of internet fasting (<NUMBER> is the number of days)
internet-fasting-period set <NUMBER>

# confirm how many days left
internet-fasting-period get
```

## How it works
When the internet fasting mode is off, Dnsmasq configurations that restrict websites and/or services that distract you are disabled durinig the night. By turning on the internet fasting mode, these configurations remain enabled. Instead, the internet fasting counters, which are managed in specific files, decrease by 1. When the internet fasting counters get 0, Dnsmasq configurations start to be disabled again at night.
