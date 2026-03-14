import argparse
import json
import os
import sys
from datetime import datetime, timezone

import requests
from dateutil import parser as date_parser


GQL_ENDPOINT = "https://api.github.com/graphql"


QUERY = """
query($owner: String!, $repo: String!, $first: Int!, $after: String) {
  repository(owner: $owner, name: $repo) {
    stargazers(first: $first, after: $after, orderBy: {field: STARRED_AT, direction: DESC}) {
      totalCount
      pageInfo { hasNextPage endCursor }
      edges {
        starredAt
        node { login company location }
      }
    }
  }
}
""".strip()


def _parse_iso(value):
    if not value:
        return None
    return date_parser.isoparse(value)


def load_existing(path):
    if not os.path.exists(path):
        return [], None
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if isinstance(data, list):
        stargazers = data
    else:
        stargazers = data.get("stargazers", [])
    last_ts = None
    for item in stargazers:
        ts = _parse_iso(item.get("starredAt"))
        if ts and (last_ts is None or ts > last_ts):
            last_ts = ts
    return stargazers, last_ts


def save(path, repo, stargazers):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    payload = {
        "repo": repo,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "stargazers": stargazers,
    }
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=True, indent=2)


def fetch_stargazers(owner, repo, token, last_ts):
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    all_new = []
    after = None
    reached_old = False
    while True:
        variables = {"owner": owner, "repo": repo, "first": 100, "after": after}
        resp = requests.post(GQL_ENDPOINT, json={"query": QUERY, "variables": variables}, headers=headers, timeout=30)
        if resp.status_code != 200:
            raise RuntimeError(f"GitHub API error {resp.status_code}: {resp.text}")
        payload = resp.json()
        if "errors" in payload:
            raise RuntimeError(f"GitHub API errors: {payload['errors']}")
        repo_data = payload.get("data", {}).get("repository")
        if not repo_data:
            raise RuntimeError("Repository not found or access denied.")
        stargazers = repo_data["stargazers"]
        edges = stargazers.get("edges", [])
        for edge in edges:
            starred_at = edge.get("starredAt")
            starred_ts = _parse_iso(starred_at)
            if last_ts and starred_ts and starred_ts <= last_ts:
                reached_old = True
                break
            node = edge.get("node", {})
            all_new.append(
                {
                    "login": node.get("login", ""),
                    "company": node.get("company") or "",
                    "location": node.get("location") or "",
                    "starredAt": starred_at,
                }
            )
        if reached_old or not stargazers["pageInfo"]["hasNextPage"]:
            break
        after = stargazers["pageInfo"]["endCursor"]
    return all_new


def merge_dedup(existing, new_entries):
    by_login = {}
    for item in existing + new_entries:
        login = item.get("login", "")
        if not login:
            continue
        current = by_login.get(login)
        if not current:
            by_login[login] = item
            continue
        current_ts = _parse_iso(current.get("starredAt"))
        candidate_ts = _parse_iso(item.get("starredAt"))
        if candidate_ts and (current_ts is None or candidate_ts > current_ts):
            by_login[login] = item
    merged = list(by_login.values())
    merged.sort(key=lambda row: _parse_iso(row.get("starredAt")) or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    return merged


def main():
    parser = argparse.ArgumentParser(description="Fetch stargazers via GitHub GraphQL.")
    parser.add_argument("--owner", default=None)
    parser.add_argument("--repo", default=None)
    parser.add_argument("--output", default=os.path.join("starryatlas", "stargazers.json"))
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        print("Missing GITHUB_TOKEN (or GH_TOKEN).", file=sys.stderr)
        sys.exit(1)

    owner = args.owner
    repo = args.repo
    if not owner or not repo:
        gh_repo = os.environ.get("GITHUB_REPOSITORY", "")
        if gh_repo and "/" in gh_repo:
            owner, repo = gh_repo.split("/", 1)
    if not owner or not repo:
        print("Missing --owner and --repo (or GITHUB_REPOSITORY).", file=sys.stderr)
        sys.exit(1)

    existing, last_ts = load_existing(args.output)
    new_entries = fetch_stargazers(owner, repo, token, last_ts)
    merged = merge_dedup(existing, new_entries)
    save(args.output, f"{owner}/{repo}", merged)

    print(f"Fetched {len(new_entries)} new stargazers. Total: {len(merged)}.")


if __name__ == "__main__":
    main()
