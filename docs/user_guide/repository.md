# Template repository

The repository is expected to be a remote repository on a platform like GitHUB, GitLab, Bitbucket, etc.
This project only reads the remote repository, there is no need to provide full access.

## Structure

This section is about how the repository is expected by the sync tool. There is an example structure attached in this
project: [Example repository](https://github.com/viktorkertesz/fortimanager-template-sync/tree/master/example/repository)

### Directory structure

Only the following directories are searched for ``.j2`` files which are the Jinja2 templates containing configuration:

- pre-run
- templates
- template-groups

All other files or directories are simply ignored. You can even keep Jinja files anywhere else in the directory
structure, only those directories above will be scanned.

Example structure:

``` text
fmgsync-repo
|
│   README.md
│
├───.github
│       pull_request_template.md
│
├───pre-run
│       test_FG101F-init.j2
│
├───template-groups
│       test_global.j2
│
└───templates
        test_banner.j2
        test_default-gw.j2
        test_dns.j2
```

### Template format

Each template should have an initial comment which serves as documentation and source metadata information.
It can be omitted but then description or default values won't be added.

[Example Template](https://github.com/viktorkertesz/fortimanager-template-sync/tree/master/example/repository/pre-run/FG101F-init.j2)

This is the expected format of a Template. First section is called header comment.

!!! note inline end

    **Used vars** and **Assigned to** are optional. Not all templates need them.

``` jinja2
{# This is the description for the template
This is only comments for the template
It can be multilined

Empty lines accepted
Here come the variable definitions:
#Used vars:
variable1: description (default: default value1)
variable2: description (default: value2)
#Assigned to: {"name": "test-group"}
#}
...
Configuration snippets
...
```

#### Metadata variables

Metadata variables are figured out from the template itself. To specify default value and description for a metadata
variable, please specify it in the header comment.

Syntax:

!!! note inline end

    Description and default value are optional but advisable.

``` jinja2
#Used vars:
variable1: var1 description (default: default value1)
variable2
variable3: var3 description
```

FMG editor for Metadata variables is at
``Policy&Objects/Object Configurations/Advanced/Metadata Variables``. If it's not there, it must be enabled by the
``Feature Visibility`` settings in ``Tools`` menu: ``Advanced/Metadata Variables``

Sync tool will create or update metadata variables only if it finds one which is not yet in use. It won't affect
existing variables. If you need to edit a variable, please login to FMG and do the change manually! This is to avoid
accidental or unintentional changes across devices which for example rely on a default value (e.g. mgmt_interface)

!!! warning

    If a variable is used in the Jinja template, it must be ensured that the variable has value for all the devices!
    Otherwise the installation will fail and log will show which device failed with lack of metavariable values.

#### Assignment configuration

In the header comment it is possible to configure assignment of this template to certain groups or devices. This line
is looking like this:

``#Assigned to: {"name": "test-group"}``

It is possible to assign the template to multiple things:

``#Assigned to: [{"name": "firewall1", "vdom": "root"}, {"name": "region-ea"}]``

### Template-group format

Template groups also have a header part where description and assignment information can be stored.

Member templates in the group are specified by Jinja2 `include` command. Only jinja templates from the `templates` or
the `templates-groups` folder must be used!

Example template group with some members:

``` jinja2
{# Global templates
These templates will appear in FMG in this order.
Variables will be gathered from them and there must be no conflict between variable default values otherwise, 
the sync operation will stop!
#assigned to: {"name": "test-group"}
#}

{% include "templates/test_banner.j2" %}

{% include "templates/test_dns.j2" %}

```

## Extra information

The tool will only look for the Jinja files in the template folders. It is possible and even desirable to add more
files to this repository such as [GitHub actions](../github_guide/github_repository.md), README or other useful data.
