# Developing templates

This section tries to describe how an organization can use teamwork to meet the following requirements:

* Syntactically correct and standard formatted Jinja templates
* review and approval process
* testing in acceptance
* Merging changes to production

The steps needed to achieve the goal:

## Create branch for change

The branch name should reflect the change purpose or any relevant business process. It shouldn't be too general, like
"My change".

!!! Note

    Git branching is a way of parallel working of a state and later it is possible to merge these changes back to the
    original. The default branch is named 'main' or 'master'.

!!! Tip

    It is advisable not to use default branch name 'main' but rename it to 'production' and have a permanent
    'acceptance' branch for the integration tests. It is possible later to merge working branches to acceptance and
    later acceptance to the production.

Example of creating a working branch:

![create branch shot](../img/create_branch.png)

## Syntax checking

Templates updated need preliminary testing to check syntax and indicate non-compliant Jinja documents. It's important
to ensure template standard and correctness.

This check is done by GitHub action which triggers by pushing changes to a branch.

## Create Pull Request

This step is necessary to notify other reviewers to check the changes.

!!! Tip

    Create a Pull request template in GitHub so all necessary information will be pre-filled automatically by GitHub.
    More details on [official GitHub docs](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/creating-a-pull-request-template-for-your-repository).

Example of opening a Pull Request:

![open pull request](../img/open_pull_request.png)

## Review

This is basically a 4-eye checking phase.
This phase can last for long, especially if the change is complex and might require additional testing in lab or
consultation with experts.

## Testing

## Merging pull request

## Sync changes to FMG

## Deploy changes to devices
