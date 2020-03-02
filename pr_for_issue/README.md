# `pr_for_issue`

`pr_for_issue` creates a GitHub PR with an empty commit for a given GitHub
issue number.

## Requirements

`pr_for_issue` has a few requirements to work:

1. An ssh key
1. A github account that is [connected with your ssh
  key](https://help.github.com/en/github/authenticating-to-github/connecting-to-github-with-ssh)

## Usage

Use `pr_for_issue -h` to see documentation:

```
❯ pr_for_issue -h
pr_for_issue
Creates an empty PR on GitHub for fixing a given issue.

IMPORTANT: Make sure you start in your local directory for the repo!

usage: pr_for_issue [issue_number]
 - issue_number - GitHub issue number in that repository
```
