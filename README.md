# GitHub to Jira Migration

Utilities to migrate GitHub issues to Jira

Largely inspired by the blog
[How to migrate GitHub issues to Jira](https://zmcddn.github.io/how-to-migrate-github-issues-to-jira.html) by
[@zmcddn](https://github.com/zmcddn)

## Prerequisites

Rename and populate the following template files:

- `migrationutils.py` - Authentication variables for GitHub and Jira
- `config.json` - Configuration for GitHub issue label filtering and mapping GitHub users to Jira users

## Running the migration script

Invoke the script using the Python CLI. Use arguments to override the `config.json` file, display verbose logging, or
run a dry run:

```
$ python3 jira-migration.py --help

usage: jira-migration.py [-h] [-l LABEL_FILTER] [-e LABEL_EXCLUSIONS] [-c COMPLETION_LABEL] [-s SQUAD_COMPLETION_LABEL] [-m COMPONENT_NAME] [-v] [--dry-run]

Utility to migrate issues from GitHub to Jira

options:
  -h, --help            show this help message and exit
  -l LABEL_FILTER, --label-filter LABEL_FILTER
                        Filter issues by GitHub label (comma separated list)
  -e LABEL_EXCLUSIONS, --label-exclusions LABEL_EXCLUSIONS
                        Exclude issues by GitHub label (comma separated list)
  -c COMPLETION_LABEL, --completion-label COMPLETION_LABEL
                        Label to filter/add for issues that have been migrated
  -s SQUAD_COMPLETION_LABEL, --squad-completion-label SQUAD_COMPLETION_LABEL
                        Label to filter/add for issues that have been migrated for non-closeable issues
  -m COMPONENT_NAME, --component-name COMPONENT_NAME
                        Name of the squad or component for messages
  -v, --verbose         Print additional logs for debugging
  --dry-run             Only run get operations and don't update/create issues
```

## Adapting for other use cases

These scripts use some specific label filtering for my use cases. Here are some pointers if you're modifying for a
different use case:

- Update `base_url` in [`jirautils.py`](jirautils.py) and [`ghutils.py`](ghutils.py) to your instances
- Update `project_key`, `security_level`, and custom `gh_issue_field` in [`jirautils.py`](jirautils.py)
- Look at the mapping flows in [`migrationutils.py`](migrationutils.py) (we heavily used labels in GitHub to specify
  things like priority and component)
