# Quick Start Guide

## Installation

In most cases installation via pip is the simplest and best way to install the software.
See [here](installation.md) for advanced installation details.

```shell
pip install fortimanager_template_sync
```

## Setup

It is advisable to use environment variables to configure the code run.

These are the usable variables with example data:

```shell
FMGSYNC_TEMPLATE_REPO=https://someserver/fortinet-templates.git
FMGSYNC_TEMPLATE_BRANCH=acceptance
FMGSYNC_GIT_TOKEN=verysecret
FMGSYNC_LOCAL_PATH=somedir
FMGSYNC_FMG_URL=https://myfmg/
FMGSYNC_FMG_USER=fmgsync
FMGSYNC_FMG_PASS=verysecret
FMGSYNC_FMG_ADOM=test
FMGSYNC_PROTECTED_FW_GROUP=production
```

## Test

List options:

```shell
fmgsync -h

Usage: fmgsync [OPTIONS]

  Main program

Options:
  -V, --version              print version
  -f, --force-changes        do changes
  -D, --debug                debug logs  [default: 0]
  -l, --logging_config TEXT  logging config file in YAML format
  -h, --help                 Show this message and exit.

```

To run a dry-run sync which doesn't modify FMG at all, run the command without any option:

```shell
fmgsync

TODO: show a test run output
```
