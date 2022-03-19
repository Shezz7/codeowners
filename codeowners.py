import sys
import os
import json
import base64
import requests


ORG_NAME = '<Insert GitHub org name here>'
GITHUB_TOKEN = base64.b64encode(os.getenv('GITHUB_TOKEN').encode()).decode()


def main():
    repos = get_github_repos()
    print(repos)


def get_github_repos():
    """Gets repositories from GitHub"""

    github_repos = []
    page = 1

    print("Getting list of GitHub repos...")
    while True:
        response = requests.get(f'https://api.github.com/orgs/{ORG_NAME}/repos?archived=false&per_page=100&page={page}',
                                headers={'Authorization': f'Basic {GITHUB_TOKEN}'})
        if response.status_code != 200:
            print(f"Failed to get repos! error: {response.status_code}")
            sys.exit(1)

        data = json.loads(response.text)

        if not data:
            break

        github_repos.append(data)
        page += 1

    print("List of repos acquired!")
    return github_repos


if __name__ == '__main__':
    main()
