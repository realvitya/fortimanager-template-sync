# Quick Start Guide

## Installation

In most cases installation via pip is the simplest and best way to install the software.
See [here](installation.md) for advanced installation details.

```shell
pip install fortimanager_template_sync
```

## Setup

Preparing template repository should be the first step. As it deserves its own guide, please check
[Repository Setup](repository.md)!

!!! Tip

    Check out [GitHub useful repository settings](../github_guide/github_repository.md)!

### Configure software

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

!!! Tip

    By using GitHub environments it is possible to configure the variables based on which branch are we working with.
    For example production and acceptance FMG or ADOM can be different.

## Test

### Main options

```
fmgsync -h

Usage: fmgsync [OPTIONS] COMMAND [ARGS]...

  Fortimanager Template Sync

Options:
  -V, --version              print version
  -l, --logging_config TEXT  logging config file in YAML format
  -D, --debug                debug logs  [default: 0]
  -h, --help                 Show this message and exit.

Commands:
  deploy  Firewall deployment operation
  sync    GIT/FMG sync operation

```

### Sync options

These options should come from environment variables, but can be specified as cmd line argument:

```
fmgsync sync -h

Usage: fmgsync sync [OPTIONS]

  GIT/FMG sync operation

Options:
  -t, --template-repo TEXT        Template repository URL  [env var: FMGSYNC_TEMPLATE_REPO]
  -b, --template-branch TEXT      Branch in repository to sync  [env var: FMGSYNC_TEMPLATE_BRANCH; default: main]
  --git-token TEXT                [env var: FMGSYNC_GIT_TOKEN]
  -l, --local-path PATH           [env var: FMGSYNC_LOCAL_REPO; default: ./fmg-templates/]
  -url, --fmg-url TEXT            [env var: FMGSYNC_FMG_URL]
  -u, --fmg-user TEXT             [env var: FMGSYNC_FMG_USER]
  -p, --fmg-pass TEXT             [env var: FMGSYNC_FMG_PASS]
  -a, --fmg-adom TEXT             [env var: FMGSYNC_FMG_ADOM; default: root]
  --fmg-verify / --no-fmg-verify  [env var: FMGSYNC_FMG_VERIFY; default: fmg-verify]
  -pg, --protected-firewall-group TEXT
                                  This group in FMG will be checked for FW status. Also this group will be deployed
                                  only  [env var: FMGSYNC_PROTECTED_FW_GROUP; default: automation]
  -d, --delete-unused-templates
  -f, --force-changes             do changes
  -h, --help                      Show this message and exit.
```

To run a dry-run sync which doesn't modify FMG at all but clone the Git repository locally,
run the command without any option:

```
fmgsync sync

[2024-03-21 22:50:07] - INFO - sync_task.py:125 - Checking out template repository
[2024-03-21 22:50:07] - INFO - sync_task.py:132 - Cloning template repository
[2024-03-21 22:50:08] - INFO - sync_task.py:145 - Load files from repository
[2024-03-21 22:50:08] - INFO - common_task.py:82 - Gathering firewall statuses in group 'automation'
[2024-03-21 22:50:08] - INFO - sync_task.py:279 - Loading templates from FMG
[2024-03-21 22:50:09] - INFO - sync_task.py:442 - Updating templates
[2024-03-21 22:50:09] - INFO - sync_task.py:452 - TEST - Updating template 'test_banner'
[2024-03-21 22:50:09] - INFO - sync_task.py:452 - TEST - Updating template 'test_default-gw'
[2024-03-21 22:50:09] - INFO - sync_task.py:464 - TEST - Updating template_group 'test_global'
[2024-03-21 22:50:09] - INFO - sync_task.py:94 - No changes happened
[2024-03-21 22:50:09] - INFO - sync_run.py:69 - Operation took 1.6s
[2024-03-21 22:50:09] - INFO - sync_run.py:71 - Sync task finished successfully!
```
