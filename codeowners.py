import sys
import os
import json
import base64
import requests
import logging
import gspread
import pandas as pd
from codeowners import CodeOwners
from oauth2client.service_account import ServiceAccountCredentials

scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
ORG_NAME = '<Insert GitHub org name here>'
GITHUB_TOKEN = base64.b64encode(os.getenv('GITHUB_TOKEN').encode()).decode()


def main():
    logging.getLogger().setLevel(level=logging.INFO)
    repos = get_github_repos()
    repo_sha_dicts = get_repo_sha(repos)
    csv_data = get_csv_result(repo_sha_dicts)
    update_sheet(csv_data)


def update_sheet(csv_data):

    credentials = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scopes)
    client = gspread.authorize(credentials)
    spreadsheet = client.open('<Google_Sheet_Name>')  # Insert name of Google Sheet from your drive here
    client.import_csv(spreadsheet.id, data=csv_data)


def get_github_repos() -> list:
    """Gets repositories from GitHub"""

    github_repos = []
    page = 1

    logging.info("Getting list of GitHub repos...")
    while True:
        response = requests.get(f'https://api.github.com/orgs/{ORG_NAME}/repos?archived=false&per_page=100&page={page}',
                                headers={'Authorization': f'Basic {GITHUB_TOKEN}'})
        if response.status_code != 200:
            logging.fatal(f"Failed to get repos! error: {response.status_code}")
            sys.exit(1)

        data = json.loads(response.text)

        if not data:
            break

        github_repos.append(data)
        page += 1

    logging.info("List of repos acquired!")
    return github_repos


def get_repo_sha(github_repos: list) -> list:

    sha_list = []

    logging.info("Getting SHAs of main branches...")
    for repo_list in github_repos:
        for repo in repo_list:
            repo_name = repo['full_name']
            default_branch = repo['default_branch']

            response = requests.get(f'https://api.github.com/repos/{repo_name}/git/refs/heads/{default_branch}',
                                    headers={'Authorization': f'Basic {GITHUB_TOKEN}'})

            if response.status_code != 200:
                logging.fatal(f"Failed to get SHA! error: {response.status_code}")
                sys.exit(1)

            data = json.loads(response.text)
            sha_list.append({repo_name: data['object']['sha']})

    logging.info("SHAs acquired!")
    return(sha_list)


def get_csv_result(repo_sha_list: list) -> dict:

    result_list = []

    logging.info("Updating CODEOWNERS...")
    for repo_sha_dict in repo_sha_list:
        repo_name = [*repo_sha_dict][0]
        sha = [*repo_sha_dict.values()][0]

        response = requests.get(f'https://api.github.com/repos/{repo_name}/git/trees/{sha}?recursive=true',
                                headers={'Authorization': f'Basic {GITHUB_TOKEN}'})

        if response.status_code != 200:
            logging.fatal(f"Failed to get files! error: {response.status_code}")
            sys.exit(1)

        codeowner_file = get_codeowners_file(repo_name)

        data = json.loads(response.text)
        for tree in data['tree']:
            if tree['type'] != 'blob':
                continue

            path = tree['path']

            if not codeowner_file:
                logging.info(f'{repo_name},{path},{None}')
                result_list.append([repo_name, path, None])
                continue

            codeowners = CodeOwners(codeowner_file)

            if codeowners.of(path):
                codeowner_name = codeowners.of(path)[0][1]

                logging.info(f'{repo_name},{path},{codeowner_name}')
                result_list.append([repo_name, path, codeowner_name])

            else:
                logging.info(f'{repo_name},{path},{None}')
                result_list.append([repo_name, path, None])

    logging.info("Complete!")

    result = pd.DataFrame(result_list, columns=['repo', 'file', 'codeowner'])
    csv_data = result.to_csv('result.csv', index=False)  # Write results to csv
    csv_data = result.to_csv(index=False)
    return csv_data


def get_codeowners_file(repo_name: str) -> str:
    """Get the codeowners file from a repository"""

    response = requests.get(f'https://api.github.com/repos/{repo_name}/contents/CODEOWNERS',
                            headers={'Authorization': f'Basic {GITHUB_TOKEN}'})

    if response.status_code != 200:
        logging.fatal(f"Failed to get codeowners from root directory. Error: {response.status_code}")

    data = json.loads(response.text)

    if data.get('message') == 'Not Found':
        response = requests.get(f'https://api.github.com/repos/{repo_name}/contents/.github/CODEOWNERS',
                                headers={'Authorization': f'Basic {GITHUB_TOKEN}'})
        if response.status_code != 200:
            logging.info(f"Failed to get codeowners from .github directory. Error: {response.status_code}")

        data = json.loads(response.text)

    if data.get('message') != 'Not Found':
        codeowners = base64.b64decode(data['content']).decode()
    else:
        codeowners = None

    return codeowners


if __name__ == '__main__':
    main()
