import utils.ghutils as ghutils
import utils.jirautils as jirautils
import json
import utils.migrationutils as migrationutils
from pprint import pprint
import argparse

try:
    config_file = open('config.json')
    config_json = json.load(config_file)
    config_file.close()
except:
    print('* Error: config.json not found. Please populate the configuration file before continuing.')
    exit(1)

user_map_json = None
try:
    user_map_file = open('user_map.json')
    user_map_json = json.load(user_map_file)
    user_map_file.close()
except:
    print('* Warning: user_map.json not found. This may be ignored if user_map is supplied in config.json or isn\'t used.')

user_map = {}
component_map = {}
if config_json:
    if 'component_map' in config_json:
        component_map = config_json['component_map']
    if user_map_json:
        user_map = user_map_json
    elif 'user_map' in config_json:
        user_map = config_json['user_map']
    if 'default_jira_user' in config_json:
        default_user = config_json['default_jira_user']
    else:
        print('Error finding default Jira user. This is required for creating Jira issues.')
        exit(1)
else:
    print('Error loading config.json.')
    exit(1)

label_filter = ''
label_exclusions = ''
completion_label = ''
squad_completion_label = ''
component_name = ''

# Parse config file
if 'label_filter' in config_json:
    label_filter = config_json['label_filter']
if 'label_exclusions' in config_json:
    label_exclusions = config_json['label_exclusions']
if 'completion_label' in config_json:
    completion_label = config_json['completion_label']
if 'squad_completion_label' in config_json:
    squad_completion_label = config_json['squad_completion_label']
if 'component_name' in config_json:
    component_name = config_json['component_name']

# Parse CLI arguments (these override the config file)
description = 'Utility to migrate issues from GitHub to Jira'
parser = argparse.ArgumentParser(description=description)
parser.add_argument(
    '-l', '--label-filter',
    help='Filter issues by GitHub label (comma separated list)')
parser.add_argument(
    '-e', '--label-exclusions',
    help='Exclude issues by GitHub label (comma separated list)')
parser.add_argument(
    '-c', '--completion-label',
    help='Label to filter/add for issues that have been migrated')
parser.add_argument(
    '-s', '--squad-completion-label',
    help='Label to filter/add for issues that have been migrated for non-closeable issues')
parser.add_argument(
    '-m', '--component-name',
    help='Name of the squad or component for messages')
parser.add_argument(
    '-v', '--verbose',
    default=False, action='store_true',
    help='Print additional logs for debugging')
parser.add_argument(
    '--dry-run',
    default=False, action='store_true',
    help='Only run get operations and don\'t update/create issues')
args = parser.parse_args()

if args.label_filter:
    label_filter = args.label_filter
if args.label_exclusions:
    label_exclusions = args.label_exclusions
if args.completion_label:
    completion_label = args.completion_label
if args.squad_completion_label:
    squad_completion_label = args.squad_completion_label
if args.component_name:
    component_name = args.component_name

# Collect GitHub issues using query config or CLI
gh_issues = ghutils.get_issues_by_label(
    label_filter, f'{completion_label},{squad_completion_label},{label_exclusions}')

jira_mappings = []

# Iterate over GitHub issues and collect mapping objects
for gh_issue in gh_issues:
    gh_url = gh_issue['html_url']
    print(f'* Creating Jira mapping for {gh_url} ({gh_issue["title"]})')

    jira_issue_input, can_close = migrationutils.issue_map(
        gh_issue, component_map, user_map, default_user)

    # Collect comments from the GitHub issue
    gh_comments = ghutils.get_issue_comments(gh_issue)
    jira_comment_input = []
    for comment in gh_comments:
        jira_comment_input.append(
            migrationutils.comment_map(comment))

    # Store issue mapping objects
    mapping_obj = {
        'gh_issue_number': gh_issue['number'],
        'issue': jira_issue_input,
        'comments': jira_comment_input,
        'close_gh_issue': can_close
    }
    jira_mappings.append(mapping_obj)

    if args.verbose:
        pprint(mapping_obj)

# Iterate over Jira mappings to create issues with comments
issue_failures = []
for jira_map in jira_mappings:
    print(
        f'* Creating Jira issue for {jira_map["issue"][jirautils.gh_issue_field]} ({jira_map["issue"]["summary"]})')

    jira_api_url = ''
    jira_key = ''
    if not args.dry_run:
        create_response = jirautils.create_issue(jira_map["issue"])
        if args.verbose:
            pprint(create_response)
        if 'self' in create_response:
            jira_api_url = create_response['self']
        if 'key' in create_response:
            jira_key = create_response['key']

    if not args.dry_run and jira_key == '':
        print('* Error: A Jira key was not returned in the creation response')
        issue_failures.append(jira_map["issue"][jirautils.gh_issue_field])
        continue

    print(f'* Adding comments from GitHub to new Jira issue {jira_key}')

    if not args.dry_run:
        for comment_map in jira_map['comments']:
            comment_response = jirautils.add_comment_from_url(
                f'{jira_api_url}/comment', comment_map)
            if args.verbose:
                pprint(comment_response)

    # Add comment in GH issue with link to new Jira issue
    gh_issue_number = jira_map['gh_issue_number']
    jira_html_url = f'https://issues.redhat.com/browse/{jira_key}'
    gh_comment = 'This issue has been migrated to Jira'
    if component_name != '':
        gh_comment += f' for {component_name}'
    gh_comment += f': {jira_html_url}'

    if not args.dry_run:
        comment_response = ghutils.add_issue_comment(
            gh_issue_number, gh_comment)
        if args.verbose:
            pprint(comment_response)

    # Add migration label and close GH issue if allowed
    print('* Handling GitHub issue labels and closing issue if allowed')
    if not args.dry_run:
        if jira_map['close_gh_issue']:
            label_response = ghutils.add_issue_label(
                gh_issue_number, completion_label)
            if args.verbose:
                pprint(label_response)
            close_response = ghutils.close_issue(gh_issue_number)
            if args.verbose:
                pprint(close_response)
        else:
            # We're not closing, so add squad-level migration label
            label_response = ghutils.add_issue_label(
                gh_issue_number, squad_completion_label)
            if args.verbose:
                pprint(label_response)

if len(issue_failures) > 0:
    print('* Failed to create Jira issues for:')
    for issue in issue_failures:
        print(issue)