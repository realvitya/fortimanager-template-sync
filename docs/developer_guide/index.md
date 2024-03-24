# Developer Guide

First, thank you for being interested in developing this tool! The following topics tries to describe the intended
setup and workflow to develop the library!

## Installing dev tools

For development, you can use the project framework by installing the library with `dev` extras:

```shell
# clone your fork
git clone https://github.com/{YOURFORK}/fortimanager-template-sync.git
# install in edit mode
pip install -e ./fortimanager-template-sync[dev]
# optionally install rich to get more fancy debug output and colors
pip install -e ./fortimanager-template-sync[dev,rich]
```

## Using Invoke

The project uses [Invoke](https://www.pyinvoke.org/) for common tasks. You may check all tasks supported in the
`tasks.py` config file or just run `invoke -l`

### Run linters

Linters are invoked by pre-commit which is installed with the dev tools.

You can either use pre-commit through `invoke`:

```shell
invoke lint
```

Or you can install pre-commit hook and it will then automatically run all checks before accepting any commit:

```shell
pre-commit install
```

## Developing documentation

This project uses mkdocs with material theme. Manual documentation is written in
[Markdown](https://www.mkdocs.org/user-guide/writing-your-docs/) in the `docs` folder.

An easy way of developing is to run mkdocs server and monitor your changes in a browser window.

Running the server:

```shell
invoke mkdocs-serve
```
