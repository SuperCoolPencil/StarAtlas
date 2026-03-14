import argparse
import os
import sys

from staratlas.enrich import enrich_and_aggregate
from staratlas.extract import fetch_stargazers, load_existing, merge_dedup, save
from staratlas.visualize import render_world_map


def main():
    parser = argparse.ArgumentParser(description="Run StarAtlas end-to-end.")
    parser.add_argument("--owner", default=None)
    parser.add_argument("--repo", default=None)
    parser.add_argument("--output-dir", default="staratlas")
    parser.add_argument("--html", action="store_true", help="Also emit an interactive HTML map.")
    parser.add_argument("--theme", default="light", choices=["light", "dark"], help="Theme for the map.")
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

    output_dir = args.output_dir
    stargazers_path = os.path.join(output_dir, "stargazers.json")
    aggregates_path = os.path.join(output_dir, "aggregates.json")
    map_png = os.path.join(output_dir, "staratlas-map.png")
    map_html = os.path.join(output_dir, "staratlas-map.html") if args.html else None

    existing, last_ts = load_existing(stargazers_path)
    new_entries = fetch_stargazers(owner, repo, token, last_ts)
    merged = merge_dedup(existing, new_entries)
    save(stargazers_path, f"{owner}/{repo}", merged)

    country_counts, _company_counts = enrich_and_aggregate(stargazers_path, aggregates_path)
    render_world_map(country_counts, map_png, map_html, theme=args.theme)

    print(f"Updated {stargazers_path}, {aggregates_path}, and visuals in {output_dir}.")


if __name__ == "__main__":
    main()
