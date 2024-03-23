# FortiManager GIT sync tool

This project aims to synchronize CLI templates from a GIT repository to FortiManager
via API calls automatically.

## Features

1. Test run
2. Check FW sync status before update
3. Error checking during update & rollback
4. Deploy changes to firewalls
5. CI/CD support

## Introduction

FMG by itself does not support GIT repository as backend to store CLI templates which
makes it hard to manage changes. Using GIT has many advances like tracking history, easy rollback to a version
in time. Additionally one could use GitHub to even manage developing these templates in a team with tools like
approval, review process, comments amongst others. Once the template changes are developed and approved, GIT can
merge the changes to its production branch which can trigger a run of this tool to sync up the changes to FMG.

## Installation



## Setup

TBD
This tool is intended to run by scheduler or GIT runner with CI/CD
