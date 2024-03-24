# Quick Start Guide

## Installation

In most cases installation via pip is the simplest and best way to install the software.
See [here](installation.md) for advanced installation details.

```shell
# installing via pip
$ pip install fortimanager-template-sync
```

## Setup

Preparing template repository should be the first step. As it deserves its own guide, please check
[Repository Setup](repository.md)!

The above guide is a general setup guide for the template repository. As there are many online Git based collaboration
tools (like GitHub, Bitbucket, GitLab), there are different implementation possibilities of the CI/CD pipelines.

This guide will use GitHub:
[GitHub useful repository settings](../github_guide/github_repository.md)!

### Configure software

It is advisable to use environment variables to configure the code run.

These are the usable variables with example data:

!!! info inline end

    While running the tool in terminal, it's possible to create an `fmgsync.env` file with this content. It will be
    read by the tool. Just beware that sensitive data can be read by other users in the system!

```shell
FMGSYNC_TEMPLATE_REPO=https://someserver/fortinet-templates.git
FMGSYNC_TEMPLATE_BRANCH=acceptance
FMGSYNC_GIT_TOKEN=verysecret
FMGSYNC_LOCAL_REPO=somedir
FMGSYNC_FMG_URL=https://myfmg/
FMGSYNC_FMG_USER=fmgsync
FMGSYNC_FMG_PASS=verysecret
FMGSYNC_FMG_ADOM=test
FMGSYNC_PROTECTED_FW_GROUP=production
```

!!! Tip

    By using [GitHub environments](https://docs.github.com/en/enterprise-cloud@latest/actions/deployment/targeting-different-environments/using-environments-for-deployment)
    it is possible to configure the variables based on which branch are we working with.
    For example production and acceptance FMG or ADOM can be different.

## Running the tool

!!! Note

    Before running the tool, FMG must be setup. Read the [FMG minimum configuration](lab_setup.md#fmg-minimum-configuration)
    what to do on the FMG!

### Main options

```shell
$ fmgsync -h

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

### Sync

These options should come from environment variables, but can be specified as cmd line argument:

```shell
$ fmgsync sync -h

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

```shell
$ fmgsync sync

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

Running the tool in write mode:

```shell
$ fmgsync -DDD sync -f

[2024-03-23 19:46:32] - INFO - sync_task.py:128 - Checking out template repository
[2024-03-23 19:46:33] - INFO - sync_task.py:148 - Load files from repository
[2024-03-23 19:46:33] - DEBUG - sync_task.py:152 - Loading templates from fmgsync-repo\templates
[2024-03-23 19:46:33] - DEBUG - sync_task.py:195 - Parsing 'test_banner' template
[2024-03-23 19:46:33] - DEBUG - sync_task.py:195 - Parsing 'test_dns' template
[2024-03-23 19:46:33] - DEBUG - sync_task.py:162 - Loading pre-run templates from fmgsync-repo\pre-run
[2024-03-23 19:46:33] - DEBUG - sync_task.py:195 - Parsing 'test_FG101F-init' template
[2024-03-23 19:46:33] - DEBUG - sync_task.py:173 - Loading template groups from fmgsync-repo\template-groups
[2024-03-23 19:46:33] - DEBUG - sync_task.py:248 - Parsing 'test_global' group
[2024-03-23 19:46:34] - INFO - common_task.py:82 - Gathering firewall statuses in group 'automation'
[2024-03-23 19:46:34] - DEBUG - common_task.py:91 - Found 1 devices
[2024-03-23 19:46:34] - DEBUG - common_task.py:105 - Device FG01: {'conf_status': 'insync', 'db_status': 'nomod', 
        'dev_status': 'installed', 'cli_status': {'root': {'name': 'test_global', 'status': 'modified', 'type': 'cli'}}}
[2024-03-23 19:46:34] - DEBUG - sync_task.py:295 - 1 pre-run templates loaded
[2024-03-23 19:46:34] - DEBUG - sync_task.py:306 - 3 templates loaded
[2024-03-23 19:46:34] - DEBUG - sync_task.py:318 - 1 template groups loaded
[2024-03-23 19:46:34] - INFO - sync_task.py:445 - Updating templates
[2024-03-23 19:46:34] - INFO - sync_task.py:94 - Changes applied successfully
[2024-03-23 19:46:34] - INFO - sync_run.py:68 - Operation took 1.85s
[2024-03-23 19:46:34] - INFO - sync_run.py:70 - Sync task finished successfully!
```

Now, the lab firewall should have a CLI template modified status and the next phase is Deployment:

### Deploy

First, here is an output for a test run:

```shell
$ fmgsync -DDD deploy 

[2024-03-23 19:46:41] - INFO - common_task.py:82 - Gathering firewall statuses in group 'automation'
[2024-03-23 19:46:41] - DEBUG - common_task.py:91 - Found 1 devices
[2024-03-23 19:46:41] - DEBUG - common_task.py:105 - Device FG01: {'conf_status': 'insync', 'db_status': 'nomod', 
        'dev_status': 'installed', 'cli_status': {'root': {'name': 'test_global', 'status': 'modified', 'type': 'cli'}}}
[2024-03-23 19:46:41] - DEBUG - deploy_task.py:124 - Found 1 firewall/VDOMs to deploy
[2024-03-23 19:46:41] - INFO - deploy_task.py:145 - TEST - to deploy to {'FG01': ['root']}
[2024-03-23 19:46:41] - INFO - deploy_task.py:67 - No checking required
[2024-03-23 19:46:41] - INFO - deploy_run.py:69 - Operation took 0.05s
[2024-03-23 19:46:41] - INFO - deploy_run.py:71 - Deploy task finished successfully!
```

The `test_global` template group has `modified` status, meaning it need to be installed on the device. This test run
only indicates, which device would be installed.

Here is the output for the actual installation:

```shell
$ fmgsync -DDD deploy -f

[2024-03-23 20:41:45] - INFO - common_task.py:82 - Gathering firewall statuses in group 'automation'
[2024-03-23 20:41:45] - DEBUG - common_task.py:91 - Found 1 devices
[2024-03-23 20:41:45] - DEBUG - common_task.py:105 - Device FG01: {'conf_status': 'insync', 'db_status': 'nomod', 
        'dev_status': 'installed', 'cli_status': {'root': {'name': 'test_global', 'status': 'modified', 'type': 'cli'}}}
[2024-03-23 20:41:45] - INFO - deploy_task.py:124 - Found 1 firewall/VDOMs to deploy
[2024-03-23 20:41:45] - DEBUG - deploy_task.py:147 - Deploying to [Scope(name='FG01', vdom='root')]
[2024-03-23 20:41:45] - INFO - deploy_task.py:151 - Running install for 1 items
[2024-03-23 20:41:47] - DEBUG - deploy_task.py:135 - 0%: start to install dev (FG01)
[2024-03-23 20:41:49] - DEBUG - deploy_task.py:135 - 52%: init state: start to get pre-checksum
[2024-03-23 20:41:53] - DEBUG - deploy_task.py:135 - 62%: script done state: start to FGFM install
[2024-03-23 20:42:01] - DEBUG - deploy_task.py:135 - 85%: fgfm install state: prepare to post-checksum
[2024-03-23 20:42:05] - DEBUG - deploy_task.py:135 - 90%: post-checksum state: start verification
[2024-03-23 20:42:09] - DEBUG - deploy_task.py:135 - 95%: install and save finished status=OK
[2024-03-23 20:42:13] - DEBUG - deploy_task.py:135 - 100%: install and save finished status=OK
[2024-03-23 20:42:13] - INFO - common_task.py:82 - Gathering firewall statuses in group 'automation'
[2024-03-23 20:42:13] - DEBUG - common_task.py:91 - Found 1 devices
[2024-03-23 20:42:13] - DEBUG - common_task.py:105 - Device FG01: {'conf_status': 'insync', 'db_status': 'nomod', 
       'dev_status': 'installed', 'cli_status': {'root': {'name': 'test_global', 'status': 'installed', 'type': 'cli'}}}
[2024-03-23 20:42:13] - INFO - deploy_task.py:124 - Found 0 firewall/VDOMs to deploy
[2024-03-23 20:42:13] - INFO - deploy_task.py:65 - CLI template install task ran successfully
[2024-03-23 20:42:13] - INFO - deploy_run.py:69 - Operation took 28.52s
[2024-03-23 20:42:13] - INFO - deploy_run.py:71 - Deploy task finished successfully!
```
