import migrationauth
import requests
from pprint import pprint

base_url = 'https://issues.redhat.com/rest/api/latest'
issue_url = f'{base_url}/issue'
project_key = 'ACM'
security_level = 'Red Hat Employee'  # To be safe, restrict to RH Employees
gh_issue_field = 'customfield_12316846'
data = {
    'projectKeys': project_key
}
headers = {
    'Authorization': f'Bearer {migrationauth.JIRA_TOKEN}',
    'Content-Type': 'application/json',
}


def get_user(user_query):
    """Get user object from query (username, name, or e-mail)"""

    url = f'{base_url}/user/search'
    data = {
        'username': user_query
    }

    response = requests.get(
        url,
        headers=headers,
        params=data,
    )

    return response.json()


def get_issue_types():
    """Get types of issues from Jira"""

    url = f'{issue_url}/createmeta'

    response = requests.get(
        url,
        headers=headers,
        params=data,
    )

    return response.json()['projects'][0]['issuetypes']


def get_issue_meta(issue_type_name):
    """Get meta fields for an issue type"""

    request_data = data
    request_data['issuetypeNames'] = issue_type_name
    request_data['expand'] = 'projects.issuetypes.fields'

    url = f'{issue_url}/createmeta'

    response = requests.get(
        url,
        headers=headers,
        params=request_data,
    )

    return response.json()['projects'][0]['issuetypes'][0]


def create_issue(props):
    """Create Jira issue"""

    url = issue_url
    request_data = {
        'fields': {
            'project': {
                'key': project_key
            },
            'security': {
                'name': security_level
            },
            'issuetype': props['issuetype'],
            'components': props['components'],
            'summary': props['summary'],
            'description': props['description'],
            'reporter': props['reporter'],
            'assignee': props['assignee'],
            # 'status': props['status'],
            'priority': props['priority'],
            # 'versions': props['version'],
            # Custom "GitHub Issue" field
            gh_issue_field: props[gh_issue_field]
        }
    }

    pprint(request_data)

    response = requests.post(
        url,
        json=request_data,
        headers=headers,
    )

    return response.json()


def get_issue_from_url(api_url):
    """Get specific issue data given API URL"""

    return requests.get(
        api_url,
        headers=headers,
    )


def get_single_issue(issue_key):
    """Get specific issue data"""

    url = f'{issue_url}/{issue_key}'

    response = get_issue_from_url(url)

    return response.json()


def add_comment(issue_key, props):
    """Add comment given issue key and props"""

    api_url = f'{issue_url}/{issue_key}/comment'

    return add_comment_from_url(api_url, props)


def add_comment_from_url(api_url, props):
    """Add comment given API URL and props"""

    request_data = {
        'visibility': {
            'type': 'group',
            'value': security_level
        },
        'author': props['author'],
        'body': props['body']
    }

    response = requests.post(
        api_url,
        headers=headers,
        json=request_data
    )

    return response.json()
