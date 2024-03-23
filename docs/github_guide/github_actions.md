# Using GitHub actions in template repository

!!! Warning

    Please do not use public GitHub to store your configuration templates! It's dangerous to pose your sensitive
    data publicly on the Internet!

## Jinja2 linting

I recommend to use an action like this to check template syntax by each push to the template folders:

```yaml title=".github/workflows/jinja-linter.yml"
---
name: Jinja2 linting

#
# Documentation:
# https://help.github.com/en/articles/workflow-syntax-for-github-actions
#

#############################
# Start the job on all push #
#############################
on:
  push:
    paths:
      - templates
      - pre-run
      - templates-groups
  workflow_dispatch:

###############
# Set the Job #
###############
jobs:
  linting:
    # Name the Job
    name: Lint Code Base
    # Set the agent to run on
    runs-on: ubuntu-latest

    steps:
      ######################
      # Checkout templates #
      ######################
      - name: Checkout Code
        uses: actions/checkout@v4

      ################################
      # Run Linter against templates #
      ################################
      - name: Install Jinja2
        run: |
          pip install j2lint
      - name: Lint Jinja templates
        run: |
          python -m j2lint pre-run templates template-groups
```

## Sync test

The sync and deploy actions may be very customized, the following example is only a basic one. Though it is indeed
possible to integrate ticketing system, add customized inputs for the action so the user has to provide additional
information (e.g. change ticket number)

```yaml
---
name: Sync Test

on:
  pull_request:
    branches: [production, acceptance]
    paths:
      - templates
      - pre-run
      - templates-groups
  workflow_dispatch:

jobs:
    linting:
    # Name the Job
    name: Lint Code Base
    # Set the agent to run on
    runs-on: ["self-hosted", "org-runner", "Linux"]

    steps:
      ######################
      # Checkout templates #
      ######################
      - name: Checkout Code
        uses: actions/checkout@v4

      ################################
      # Run Linter against templates #
      ################################
      - name: Install Jinja2
        run: |
          pip install j2lint
      - name: Lint Jinja templates
        run: |
          python -m j2lint pre-run templates template-groups

    sync_test:
      name: Sync test run
      runs-on: ["org-runner", "linux"]
      needs: linting
      environment: $GITHUB_BASE_REF
      steps:
        - name: Checkout Code
          uses: actions/checkout@v4
          with:
            path: fmg-templates
        - name: Install and update pip and fmgsync
          run: |
            pip install -U pip
            python -m pip install fortimanager-template-sync
        - name: Run fmgsync test
          # Pre-requisites:
          #  1. to have all environment variables set at GitHub environment/variables & secrets
          #  2. Runner need to access FMG API interface! Set firewalls and network accordingly!
          #  3. The credential used for FMG connection must have API read/write access
          run: |
            python -m fortimanager_template_sync sync
```
