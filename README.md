# GitHub to Jira Migration

Utilities to migrate GitHub issues to Jira

Largely inspired by the blog
[How to migrate GitHub issues to Jira](https://zmcddn.github.io/how-to-migrate-github-issues-to-jira.html) by
[@zmcddn](https://github.com/zmcddn)

## Prerequisites

1. Install Python dependencies:

   ```shell
   python3 -m pip install requests argparse
   ```

2. Rename and populate the following template files:

   - [`migrationutils.py`](migrationauth_template.py) - Authentication variables for GitHub and Jira
   - [`config.json`](config_template.json) - Configuration for GitHub issue label filtering
   - [`user_map.json`](user_map_template.json) - Mapping of GitHub users to Jira users (this can alternatively be supplied
     using the `user_map` key in `config.json` or not supplied at all if user mapping is not desired.)

## Running the migration script

Invoke the script using the Python CLI. Use arguments to override the `config.json` file, display verbose logging, or
run a dry run:

```
$ python3 jira-migration.py --help

usage: jira-migration.py [-h] [-l LABEL_FILTER] [-e LABEL_EXCLUSIONS]
                         [-c COMPLETION_LABEL] [-s SQUAD_COMPLETION_LABEL]
                         [-m COMPONENT_NAME] [-v] [--dry-run]

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
                        Label to filter/add for issues that have been migrated
                        for non-closeable issues
  -m COMPONENT_NAME, --component-name COMPONENT_NAME
                        Name of the squad or component for messages
  -v, --verbose         Print additional logs for debugging
  --dry-run             Only run get operations and don't update/create issues
```

## Adapting for other use cases

These scripts use some specific label filtering for my use cases. Here are some pointers if you're modifying for a
different use case:

- Update `root_url` in [`jirautils.py`](utils/jirautils.py)
- Update `org_repo` in [`ghutils.py`](utils/ghutils.py)
- Update `project_key`, `security_level`, and custom fields in [`jirautils.py`](utils/jirautils.py)
- Look at the mapping flows in [`migrationutils.py`](utils/migrationutils.py) (we heavily used labels in GitHub to
  specify things like priority and component)

## Resources

- [GitHub API](https://docs.github.com/en/rest)
- [Jira API](https://docs.atlassian.com/software/jira/docs/api/REST/latest)
- [ZenHub API](https://developers.zenhub.com/graphql-api-docs/getting-started)
