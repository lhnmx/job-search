#!/usr/bin/env python3
"""Fetch, scrape, and stage job and internship postings using Firecrawl.

Fetches a job posting from a URL using Firecrawl CLI (or search query), cleans
the extracted markdown content, checks against previously applied roles, and
writes it directly to the target application folder as `job_description.md`.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from applied_jobs import (
    check_applied,
    fetch_sheet_records,
    get_local_applied_slugs,
)


def load_env_file(env_path: Path | None = None) -> None:
    """Load key-value pairs from a .env file into os.environ if not already set."""
    if env_path is None:
        env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.is_file():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip("'\"")
        if key and key not in os.environ:
            os.environ[key] = val


def get_configured_sheet_url() -> str | None:
    """Retrieve Google Sheet URL from environment or .resume/settings.json."""
    load_env_file()
    url = os.environ.get("APPLIED_JOBS_SHEET_URL") or os.environ.get("GOOGLE_SHEET_URL")
    if url:
        return url

    settings_path = Path(__file__).resolve().parents[1] / ".resume" / "settings.json"
    if settings_path.is_file():
        try:
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
            return settings.get("applied_jobs_sheet_url")
        except Exception:
            pass
    return None


def get_all_applied_records(sheet_url: str | None = None, force_refresh: bool = False) -> list[dict[str, str]]:
    """Retrieve combined applied records from Google Sheet and local applications directory."""
    records: list[dict[str, str]] = []

    # 1. Google Sheet records
    url = sheet_url or get_configured_sheet_url()
    if url:
        try:
            sheet_recs = fetch_sheet_records(url, force_refresh=force_refresh)
            for r in sheet_recs:
                r.setdefault("raw", {})["source"] = "Google Sheet"
            records.extend(sheet_recs)
        except Exception as error:
            print(f"Warning: Could not fetch Google Sheet applied records: {error}", file=sys.stderr)

    # 2. Local applications workspace
    local_recs = get_local_applied_slugs()
    records.extend(local_recs)

    return records


def run_firecrawl_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    """Execute a firecrawl CLI command using local binary or npx fallback."""
    load_env_file()
    firecrawl_bin = shutil.which("firecrawl")
    if firecrawl_bin:
        cmd = [firecrawl_bin, *args]
    else:
        npx_bin = shutil.which("npx")
        if not npx_bin:
            raise RuntimeError("Neither 'firecrawl' nor 'npx' command found in PATH.")
        cmd = [npx_bin, "-y", "firecrawl-cli@latest", *args]

    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=True,
    )


def search_jobs(query: str, limit: int = 5) -> list[dict[str, str]]:
    """Search for job or internship postings using firecrawl search."""
    cmd_args = ["search", query, "--json"]
    proc = run_firecrawl_command(cmd_args)
    data = json.loads(proc.stdout)
    items = []
    if data.get("success") and "data" in data and "web" in data["data"]:
        for item in data["data"]["web"][:limit]:
            items.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "description": item.get("description", ""),
            })
    return items


def scrape_job_posting(url: str) -> str:
    """Scrape a job posting URL into clean markdown using firecrawl scrape."""
    cmd_args = ["scrape", url, "--only-main-content"]
    proc = run_firecrawl_command(cmd_args)
    content = proc.stdout.strip()
    if not content:
        raise ValueError(f"No content returned when scraping {url}")
    return content


def derive_folder_slug(company: str, role: str) -> str:
    """Generate a sanitized company-role folder name."""
    raw = f"{company}-{role}".lower()
    slug = re.sub(r"[^a-z0-9]+", "-", raw).strip("-")
    return slug or "new-application"


def parse_company_role_from_title(title: str) -> tuple[str, str]:
    """Heuristic extraction of company and role from search snippet title."""
    delimiters = [" - ", " | ", " at ", " – ", " — "]
    for d in delimiters:
        if d in title:
            parts = title.split(d)
            if len(parts) >= 2:
                p1, p2 = parts[0].strip(), parts[1].strip()
                if any(w in p1.lower() for w in ["intern", "engineer", "analyst", "developer", "scientist", "manager"]):
                    return p2, p1
                return p1, p2
    return "", title


def stage_job_description(content: str, target_dir: Path, source_url: str | None = None) -> Path:
    """Write job description markdown to target application directory."""
    target_dir.mkdir(parents=True, exist_ok=True)
    out_file = target_dir / "job_description.md"

    header = ""
    if source_url:
        header = f"<!-- Source: {source_url} -->\n\n"

    out_file.write_text(header + content.strip() + "\n", encoding="utf-8")
    return out_file


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", nargs="?", help="Job posting URL or search query")
    parser.add_argument("--search", "-s", action="store_true", help="Perform a job search instead of scraping a URL")
    parser.add_argument("--limit", "-n", type=int, default=5, help="Number of search results to display (default: 5)")
    parser.add_argument("--target", "-t", type=Path, help="Target application directory (e.g. applications/<company-role>)")
    parser.add_argument("--company", "-c", help="Company name (used with --role to derive target folder)")
    parser.add_argument("--role", "-r", help="Role title (used with --company to derive target folder)")
    parser.add_argument("--sheet-url", help="Google Sheet URL to check against applied roles")
    parser.add_argument("--refresh-applied", action="store_true", help="Force refresh of applied jobs cache from Google Sheet")
    parser.add_argument("--force", "-f", action="store_true", help="Proceed even if role was already applied to")
    parser.add_argument("--check-applied", action="store_true", help="Check whether a specific company and role was already applied to")

    args = parser.parse_args()

    # Standalone applied check
    if args.check_applied:
        if not args.company or not args.role:
            print("Error: --check-applied requires --company and --role", file=sys.stderr)
            return 1
        applied_recs = get_all_applied_records(sheet_url=args.sheet_url, force_refresh=args.refresh_applied)
        matched = check_applied(args.company, args.role, applied_recs)
        if matched:
            source = matched.get("raw", {}).get("source", "Google Sheet")
            print(f"⚠️  ALREADY APPLIED: {matched['company']} - {matched['role']} (Source: {source})")
            return 0
        else:
            print(f"✓ Not applied yet: {args.company} - {args.role}")
            return 0

    if not args.source:
        parser.print_help()
        return 1

    applied_recs = get_all_applied_records(sheet_url=args.sheet_url, force_refresh=args.refresh_applied)

    if args.search:
        print(f"Searching job postings: '{args.source}'...\n")
        try:
            results = search_jobs(args.source, limit=args.limit)
            if not results:
                print("No results found.")
                return 0
            for idx, res in enumerate(results, 1):
                title = res['title']
                url = res['url']
                comp, role = parse_company_role_from_title(title)
                applied_badge = ""
                if comp:
                    matched = check_applied(comp, role, applied_recs)
                    if matched:
                        source = matched.get("raw", {}).get("source", "Google Sheet")
                        applied_badge = f"  ⚠️  [ALREADY APPLIED: {matched['company']} - {matched['role']} ({source})]"

                print(f"[{idx}] {title}{applied_badge}")
                print(f"    URL: {url}")
                desc_snippet = res['description'].replace("\n", " ")[:150]
                print(f"    Summary: {desc_snippet}...\n")
            print("To stage a role into an application, run:")
            print("  uv run python scripts/fetch_job.py <url> --company <company> --role <role>")
            return 0
        except Exception as error:
            print(f"Error during job search: {error}", file=sys.stderr)
            return 1

    # Single posting URL scrape
    url = args.source
    target_dir = args.target
    company = args.company
    role = args.role

    if not target_dir:
        if company and role:
            slug = derive_folder_slug(company, role)
            target_dir = Path("applications") / slug
        else:
            print("Error: Specify --target <folder> or --company <name> and --role <title>", file=sys.stderr)
            return 1
    elif not company or not role:
        # Infer company and role from target directory name
        slug = target_dir.name
        parts = slug.split("-", 1)
        company = company or parts[0].replace("-", " ")
        role = role or (parts[1].replace("-", " ") if len(parts) > 1 else "intern")

    # Check if already applied
    matched = check_applied(company, role, applied_recs)
    if matched:
        source = matched.get("raw", {}).get("source", "Google Sheet")
        if not args.force:
            print(f"⚠️  ALREADY APPLIED: You have already applied to {matched['company']} - {matched['role']} (Source: {source})", file=sys.stderr)
            print("To stage this application anyway, re-run with --force (or -f).", file=sys.stderr)
            return 1
        else:
            print(f"⚠️  Note: Already applied to {matched['company']} - {matched['role']} (Source: {source}); proceeding with --force.")

    print(f"Scraping job posting from: {url}")
    try:
        content = scrape_job_posting(url)
        staged_path = stage_job_description(content, target_dir, source_url=url)
        print(f"Staged job description: {staged_path}")
        print(f"\nNext steps to tailor resume and cover letter:")
        print(f"  1. Review {staged_path}")
        print(f"  2. uv run python scripts/prepare_application.py {target_dir} --base pre-made/<track>")
        return 0
    except Exception as error:
        print(f"Error scraping job posting: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
