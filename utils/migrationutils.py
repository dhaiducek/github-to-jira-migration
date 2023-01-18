import utils.ghutils as ghutils
import utils.jirautils as jirautils
import utils.zenhubutils as zenhubutils

jira_product_versions = {}

def user_map(gh_username, user_mapping, default_user=''):
    """Return the user e-mail from the usermap"""
    assert user_mapping != None  # user_mapping cannot be None

    user = None
    user_email = default_user

    if gh_username in user_mapping:
        user_email = user_mapping[gh_username]

    if user_email != '':
        user_query = jirautils.get_user(user_email)
        if user_query and len(user_query) > 0:
            user = {'name': user_query[0]['name']}

    return user


def component_map(gh_labels, component_map):
    """Return the Jira components from a given GitHub label"""

    components = []
    component_count = 0
    is_ui = False
    for label in gh_labels:
        label_name = str(label['name'])
        if label_name.startswith('squad:'):
            component_count += 1
            if label_name in component_map:
                components.append({'name': component_map[label_name]})
                if label_name.endswith("-ui"):
                    is_ui = True

    return components, component_count, is_ui


def type_map(gh_labels):
    """Return the Jira issue type from a given GitHub label"""

    type_map = {
        'task': 'Task',
        'bug': 'Bug',
        'user_story': 'Story',
        'Epic': 'Epic'
    }

    for label in gh_labels:
        label_name = str(label['name'])
        if label_name in type_map:
            return type_map[label_name]

    return 'Task'


def priority_map(gh_labels):
    """Return the Jira priority from a given GitHub label"""

    priority_map = {
        'blocker (P0)': 'Blocker',
        'Priority/P1': 'Critical',
        'Priority/P2': 'Normal',
        'Priority/P3': 'Minor',
    }

    priority = {
        'name': 'Undefined'
    }

    for label in gh_labels:
        label_name = str(label['name'])
        if label_name in priority_map:
            if priority_map[label_name] != '':
                priority['name'] = priority_map[label_name]
                break

    return priority


def severity_map(gh_labels):
    """Return the Jira severity from a given GitHub label"""

    severity_map = {
        'Severity 1 - Urgent': 'Critical',
        'Severity 2 - Major': 'Moderate',
        'Severity 3 - Minor': 'Low',
    }

    severity = {}

    for label in gh_labels:
        label_name = str(label['name'])
        if label_name in severity_map:
            if severity_map[label_name] != '':
                severity['value'] = severity_map[label_name]
                break

    if 'value' in severity:
        return severity

    return None


def status_map(pipeline, issue_type):
    """Return equivalent Jira status for a given ZenHub pipeline"""

    # Untriaged and Backlogs will remain in the state on creation ("New" or "To Do")
    pipeline_map = {
        "In Progress": {
            "Bug": "ASSIGNED",
            "Default": "In Progress"
        },
        "Awaiting Verification": {
            "Bug": "ON_QA",
            "Default": "Review",
            "Epic": "Testing"
        },
        "Epics In Progress": "In Progress",
        "Ready For Playback": {
            "Bug": "ON_QA",
            "Epic": "Testing",
            "Default": "Review"
        },
        "Awaiting Docs": "In Progress",
        "Closed": "Closed"
    }

    if pipeline in pipeline_map:
        mapping_obj = pipeline_map[pipeline]
        if isinstance(mapping_obj, str):
            return mapping_obj
        if issue_type in mapping_obj:
            return mapping_obj[issue_type]
        if 'Default' in mapping_obj:
            return mapping_obj['Default']

    return None


def should_close(gh_issue):
    """Return the whether an issue has a label signaling it should not be closed"""

    no_close_labels = 'bugzilla,canary-failure'

    return ghutils.has_label(gh_issue, no_close_labels)


def issue_map(gh_issue, component_mapping, user_mapping, default_user):
    """Return a dict for Jira to process from a given GitHub issue"""
    assert user_mapping != None  # user_mapping cannot be None

    gh_labels = gh_issue['labels']

    # Flag for whether the GitHub issue can be closed after migration
    # Don't close the issue if:
    # - It's connected to Bugzilla
    # - It's a multi-squad issue
    can_close = True
    components, component_count, is_ui = component_map(
        gh_labels, component_mapping)
    if component_count > 1 or should_close(gh_issue):
        can_close = False

    assignee = None
    contributors = []
    for gh_assignee in gh_issue['assignees']:
        assignee_id = user_map(gh_assignee['login'], user_mapping)
        if assignee_id:
            if assignee:
                contributors.append(assignee_id)
            else:
                assignee = assignee_id

    # Make sure a string is returned for the issue body
    issue_body = ''
    if gh_issue['body']:
        issue_body = gh_issue['body']

    issue_title = gh_issue['title']
    issue_type = type_map(gh_labels)

    zenhub_data = zenhubutils.get_issue_data(str(gh_issue['number']))

    releases = []
    for release in zenhub_data['releases']:
        # Only fetch if not already populated
        if not issue_type in jira_product_versions:
            print(f'* Fetching releases for issue type {issue_type}')
            version_response = jirautils.get_issue_meta(issue_type)['fields']['fixVersions']['allowedValues']
            if len(version_response) > 0:
                jira_product_versions[issue_type] = list(map(lambda version: version['name'], version_response))

        for version in jira_product_versions[issue_type]:
            if version == release:
                releases.append({
                    'name': release
                })
                break

    # Handle labels
    labels = []
    if is_ui:
        labels.append('ui')

    issue_mapping = {
        'issuetype': {
            'name': issue_type
        },
        'components': components,
        'summary': issue_title,
        'description': issue_body,
        'reporter': user_map(gh_issue['user']['login'], user_mapping, default_user),
        'assignee': assignee,
        jirautils.contributors_field: contributors,
        'status': status_map(zenhub_data['pipeline'], issue_type),
        'priority': priority_map(gh_labels),
        'fixVersions': releases,
        'labels': labels,
        jirautils.story_points_field: zenhub_data['estimate'],
        jirautils.gh_issue_field: gh_issue['html_url']
    }

    if issue_type == 'Epic':
        # Custom "Epic Name" field
        issue_mapping[jirautils.epic_field] = issue_title

    if issue_type == 'Bug':
        # Custom "Severity" field
        issue_mapping[jirautils.severity_field] = severity_map(gh_labels)

    return issue_mapping, can_close


def comment_map(gh_comment):
    """Return a dict for Jira to process from a given GitHub comment"""

    gh_user = gh_comment['user']['login']

    return {
        'body': f'{gh_comment["created_at"]} @{gh_user}\n{gh_comment["body"]}'
    }
