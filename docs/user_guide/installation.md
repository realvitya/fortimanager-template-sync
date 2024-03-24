# Installation

## Installing package

Released versions can be installed from pypi.org by using the `pip`. It all depends on the environment, but it's
advisable to create a separate venv for the tool. Reason is that it's heavily depending on Pydantic 2, which is not
straight back compatible with Pydantic 1. If a system uses Pydantic1, installing this tool can break things.

```shell
# create a venv in local directory 'fmgsync'
$ python -m venv fmgsync
# activate venv in linux
$ . fmgsync/bin/activate
# same on windows
> fmgsync/Script/activate
# update environment
(fmgsync)$ python -m pip install -U pip
# install tool with all features
(fmgsync)$ python -m pip install fortimanager-template-sync[rich]
# test if it's working
(fmgsync)$ fmgsync -h
# or as module (better works for github actions)
(fmgsync)$ python -m fortimanager_template_sync -h
```

## Installing from source

The tool can be installed from GitHub

```shell
# latest main branch
$ pip install git+https://github.com/realvitya/fortimanager-template-sync.git
# specific version tag
$ pip install git+https://github.com/realvitya/fortimanager-template-sync.git@v1.0.0
```

If you want editor mode for development purposes, I recommend forking the project, cloning and installing it:

```shell
# clone repo to local folder
$ git clone https://github.com/{YOURACC}/fortimanager-template-sync
# install repo in editor mode (changes will be reflected immediately)
$ pip install -e ./fortimanager-template-sync[dev,rich]
```

## Configuration

The tool needs information about the template repository and your FMG. Also it may need configuration for custom logging
and debug. All these needs can be asked on the CLI:

```shell
# show main help
$ fmgsync -h
# show sync help
$ fmgsync sync -h
```

### Logging setup

By default, the tool will log based on the following code:

``` python title="Default logging setup"
--8<-- "fortimanager_template_sync/misc.py:default_logging"
```

A new logging setup can be developed in case more granular logging is needed. The format should be YAML and supported
by `logging.dictConfig`.

### Environment variables

It is highly advisable to use env variables as giving program arguments on the command line might expose sensitive data
like passwords in the operating system logs.

!!! Dangerous

    Do not use program arguments which are sensitive (like token, password) in GitHub actions! Use repository secrets!

These variables can be used:

| Name                       | Description                                            | Default         |
|----------------------------|--------------------------------------------------------|-----------------|
| FMGSYNC_TEMPLATE_REPO      | Remote repository URL                                  | -               |
| FMGSYNC_TEMPLATE_BRANCH    | Remote repo's branch to use                            | main            |
| FMGSYNC_GIT_TOKEN          | Token for remote repo                                  | -               |
| FMGSYNC_LOCAL_REPO         | Local folder to keep the repo                          | ./fmg-templates |
| FMGSYNC_FMG_URL            | FMG access URL (no need to use anything after /)       | -               |
| FMGSYNC_FMG_USER           | User for FMG                                           | -               |
| FMGSYNC_FMG_PASS           | Password for FMG                                       | -               |
| FMGSYNC_FMG_ADOM           | ADOM to use                                            | root            |
| FMGSYNC_FMG_VERIFY         | SSL verification (true/false)                          | true            |
| FMGSYNC_PROTECTED_FW_GROUP | Tracked devices should be in this group defined on FMG | automation      |

`FMGSYNC_GIT_TOKEN` should be a token not used by anyone else. It's not advisable to use general PAT (personal access
token), but rather a limited access token dedicated to this repo
([Github fine grained PAT](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-fine-grained-personal-access-token))
