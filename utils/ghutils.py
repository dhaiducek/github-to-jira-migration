import migrationauth
import requests

org_repo = 'stolostron/backlog'
root_url = 'https://api.github.com/repos'
base_url = f'{root_url}/{org_repo}/issues'


def get_issues_by_label(labels, label_exclusions, pagination=100):
    """Get list of issues by label"""
    assert 0 < pagination <= 100  # pagination size needs to be set properly
    assert labels                 # Labels cannot be None

    issues = []
    page = 0
    url = f'{base_url}'

    while True:
        page += 1
        data = {
            'per_page': pagination,
            'labels': labels,
            'page': page
        }
        response = requests.get(
            url,
            auth=(migrationauth.GH_USERNAME, migrationauth.GH_TOKEN),
            params=data
        )

        if response.status_code == 200:
            # Get all the issues excluding the PRs and specified labels
            issues.extend([issue for issue in response.json()
                        if not has_label(issue, label_exclusions) and not issue.get("pull_request")])
        
        else:
            print(f'* An unexpected response was returned from GitHub: {response}')
            print(response.json())
            exit(1)

        if not 'next' in response.links.keys():
                break

    return issues


def has_label(issue, label_query):
    """Whether an issue has a given label"""

    label_list = label_query.split(',')

    for label_obj in issue['labels']:
        for label_name in label_list:
            if str(label_obj['name']) == label_name:
                return True

    return False


def get_single_issue(issue_number):
    """Get specific issue data"""

    url = f'{base_url}/{issue_number}'
    return requests.get(
        url,
        auth=(migrationauth.GH_USERNAME, migrationauth.GH_TOKEN)
    ).json()


def close_issue(issue_number):
    """Close issue"""

    url = f'{base_url}/{issue_number}'
    data = {
        'state': 'closed'
    }
    return requests.patch(
        url,
        auth=(migrationauth.GH_USERNAME, migrationauth.GH_TOKEN),
        json=data
    ).json()


def get_issue_comments(issue):
    """Get comments from given issue dict"""

    comment_url = issue['comments_url']

    response = requests.get(
        comment_url,
        auth=(migrationauth.GH_USERNAME, migrationauth.GH_TOKEN)
    )

    # Omit comments from selected bots
    comments = []
    comments.extend([comment for comment in response.json()
                    if comment['user']['login'] != 'stale[bot]' and comment['body'] != 'dependency_scan failed.'])

    return comments


def add_issue_label(issue_number, label):
    """Add label to given issue"""

    url = f'{base_url}/{issue_number}/labels'

    data = {
        'labels': [label]
    }

    response = requests.post(
        url,
        auth=(migrationauth.GH_USERNAME, migrationauth.GH_TOKEN),
        json=data
    )

    return response.json()


def add_issue_comment(issue_number, comment):
    """Add comment to given issue"""

    url = f'{base_url}/{issue_number}/comments'

    data = {
        'body': comment
    }

    response = requests.post(
        url,
        auth=(migrationauth.GH_USERNAME, migrationauth.GH_TOKEN),
        json=data
    )

    return response.json()
