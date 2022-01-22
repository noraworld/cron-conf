# cron-conf
If you don’t specify a file path, a command is executed in home directory.
In other words, if you specify a absolute path, a command is exected in any directory.

When you want to use `sudo`, you should register a job as a root user.
It’s dangerous and troublesome to execute `sudo` as a normal user.

It’s not recommended to create or edit a job with `crontab -e`.
You can write a job to `cron.conf` and load it instead.

To reflect `cron.conf` to crontab, execute the following command.

```shell
crontab      < cron.conf      # for a normal user
sudo crontab < root_cron.conf # for a root user
```

To confirm what is executed by crontab, execute the following command.

```shell
crontab -l      # for a normal user
sudo crontab -l # for a root user
```

## Useful tool
* [Crontab.guru - The cron schedule expression editor](https://crontab.guru/#*_*_*_*_*)
