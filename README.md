# CODEOWNERS

## Introduction

[CODEOWNERS](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners) are used to define individuals or teams that are responsible for code in a repository. Amongst other things, CODEOWNERS are centric to the identification and remediation of security issues in code.

## Implementation

This python script does the following:

1. Grabs a list of all repositories belonging to a GitHub organization
2. Gets the default/master branches for all the repositories
3. Checks every file for a codeowner using the [codeowners](https://pypi.org/project/codeowners/) library
4. Stores the result as a csv and uploads the results to a Google Sheet

## Requirements

1. GitHub read-only token
2. Google Cloud service account key
