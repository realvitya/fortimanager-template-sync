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
### Template format
Each template should have an initial comment which serves as documentation and source metadata information.
It can be omitted but then description or default values won't be added. 

[Example Template](https://github.com/viktorkertesz/fortimanager-template-sync/tree/master/example/repository/pre-run/FG101F-init.j2)

This is the expected format of a Template. First section is called header comment.
```jinja2
{# This is the description for the template
This is only comments for the template
It can be multilined

Empty lines accepted
Here come the variable definitions:
used vars:
variable1: description (default: default value1)
variable2: description (default: value2)
#}
...
Configuration snippets
...
```
#### Metadata variables
Metadata variables are figured out from the template itself. To specify default value for a metadata variable, please
specify it in the header comment.

FMG editor for Metadata variables is at
``Policy&Objects/Object Configurations/Advanced/Metadata Variables``. If it's not there, it must be enabled by the 
``Feature Visibility`` settings in ``Tools`` menu: ``Advanced/Metadata Variables``

Sync tool will create or update metadata variables only if it finds one which is not yet in use. It won't affect
existing variables. If you need to edit a variable, please login to FMG and do the change manually! This is to avoid
accidental and unintentional changes across devices which for example rely on a default value (e.g. mgmt_interface)
### Template-group format