import migrationauth
import requests

base_url = 'https://api.zenhub.com/public/graphql'
headers = {
    'Authorization': f'Bearer {migrationauth.ZENHUB_TOKEN}',
    'Content-Type': 'application/json',
}
gh_repo_id = '239633281'
workspace_id = '604fab62d4b98d00150a2854'


def get_issue_data(gh_issue_number):
    """Get ZenHub Pipeline and Releases for a GitHub issue"""

    query = """query {
  issueByInfo(
    repositoryGhId: """+gh_repo_id+""", 
    issueNumber: """+gh_issue_number+"""
  ) {
    releases {
      nodes {
        title
      }
    }
    pipelineIssue(workspaceId: \""""+workspace_id+"""\") {
      pipeline {
        name
      }
    }
    estimate {
      value
    }
  }
}"""

    response = requests.post(
        base_url,
        headers=headers,
        json={'query': query}
    ).json()

    issue_info = response['data']['issueByInfo']

    estimate = None
    if issue_info['estimate']:
      estimate = issue_info['estimate']['value']

    pipeline = issue_info['pipelineIssue']['pipeline']['name']

    releases = []
    for release in issue_info['releases']['nodes']:
      releases.append(release['title'])
      
    return {
      'estimate': estimate,
      'pipeline': pipeline, 
      'releases': releases
    }
