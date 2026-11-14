#!/usr/bin/env python3
"""Check whether a job or internship opening has already been applied to.

Synchronizes applied positions from a shareable Google Sheet (CSV export) on a
daily basis and saves them locally to `.resume/applied_jobs.json`. Also scans the
local workspace as a safety net, and provides fuzzy matching on company and role.
"""

from __future__ import annotations

import argparse
import csv
import datetime
import io
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

DEFAULT_SAVED_PATH = Path(__file__).resolve().parents[1] / ".resume" / "applied_jobs.json"


def normalize_text(text: str) -> str:
    """Lowercase and strip non-alphanumeric characters except single spaces."""
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", " ", text.lower())
    return " ".join(cleaned.split())


def normalize_company(company: str) -> str:
    """Normalize company name by stripping common corporate suffixes."""
    norm = normalize_text(company)
    suffixes = [
        r"\binc\b", r"\bllc\b", r"\bcorp\b", r"\bcorporation\b",
        r"\bltd\b", r"\blimited\b", r"\btechnologies\b", r"\btechnology\b",
        r"\bplatforms\b", r"\bgroup\b", r"\bco\b"
    ]
    for suf in suffixes:
        norm = re.sub(suf, "", norm)
    return " ".join(norm.split())


def normalize_role(role: str) -> str:
    """Normalize role by stripping year, season, and standardizing common titles."""
    norm = normalize_text(role)
    # Strip years (e.g. 2025, 2026, 2027)
    norm = re.sub(r"\b20\d\d\b", "", norm)
    # Strip seasons and generic markers
    norm = re.sub(r"\b(summer|fall|spring|winter)\b", "", norm)
    norm = re.sub(r"\binternship\b", "intern", norm)
    # Standardize swe abbreviations
    norm = re.sub(r"\bswe\b", "software engineer", norm)
    norm = re.sub(r"\bsoftware engineering\b", "software engineer", norm)
    norm = re.sub(r"\bmle\b", "machine learning engineer", norm)
    norm = re.sub(r"\bfde\b", "forward deployed engineer", norm)
    # Collapse repeated words (e.g. intern intern -> intern)
    norm = re.sub(r"\b(\w+)(?:\s+\1\b)+", r"\1", norm)
    return " ".join(norm.split())


def convert_sheet_url_to_csv_url(url: str) -> str:
    """Convert a standard Google Sheets URL into its direct CSV export URL."""
    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", url)
    if not match:
        return url
    sheet_id = match.group(1)

    gid_match = re.search(r"[#&?]gid=([0-9]+)", url)
    gid = gid_match.group(1) if gid_match else "0"

    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"


def find_column(fieldnames: list[str], patterns: list[str]) -> str | None:
    """Find a column name matching any of the regex patterns."""
    for col in fieldnames:
        norm_col = normalize_text(col)
        for pattern in patterns:
            if re.search(pattern, norm_col):
                return col
    return None


def parse_csv_records(csv_text: str) -> list[dict[str, str]]:
    """Parse CSV text into list of dicts with normalized 'company' and 'role'."""
    reader = csv.DictReader(io.StringIO(csv_text))
    if not reader.fieldnames:
        return []

    company_col = find_column(reader.fieldnames, [r"^company", r"^employer", r"^organization", r"^firm"])
    role_col = find_column(reader.fieldnames, [r"^role", r"^title", r"^position", r"^job"])

    if not company_col or not role_col:
        # Fallback: if at least 2 columns exist, assume 1st is company, 2nd is role
        if len(reader.fieldnames) >= 2:
            company_col = reader.fieldnames[0]
            role_col = reader.fieldnames[1]
        else:
            return []

    records = []
    for row in reader:
        comp = row.get(company_col, "").strip()
        role = row.get(role_col, "").strip()
        if comp and role:
            records.append({
                "company": comp,
                "role": role,
                "raw": dict(row),
            })
    return records


def fetch_sheet_records(
    sheet_url: str,
    saved_path: Path = DEFAULT_SAVED_PATH,
    force_refresh: bool = False
) -> list[dict[str, str]]:
    """Fetch applied job records from Google Sheet, saving locally on a daily basis."""
    today = datetime.date.today().isoformat()

    # If already saved today and not forcing refresh, use today's saved records
    if not force_refresh and saved_path.is_file():
        try:
            saved_data = json.loads(saved_path.read_text(encoding="utf-8"))
            if saved_data.get("last_synced") == today:
                return saved_data.get("records", [])
        except Exception:
            pass

    csv_url = convert_sheet_url_to_csv_url(sheet_url)
    req = urllib.request.Request(
        csv_url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; JobSearchAssistant/1.0)"}
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            content = response.read().decode("utf-8", errors="replace")

        records = parse_csv_records(content)

        # Save daily snapshot locally
        saved_path.parent.mkdir(parents=True, exist_ok=True)
        saved_data = {
            "last_synced": today,
            "updated_at": datetime.datetime.now().isoformat(),
            "url": sheet_url,
            "count": len(records),
            "records": records,
        }
        saved_path.write_text(json.dumps(saved_data, indent=2), encoding="utf-8")
        return records

    except Exception as error:
        # If fetch fails but we have an earlier local snapshot, fall back gracefully
        if saved_path.is_file():
            try:
                saved_data = json.loads(saved_path.read_text(encoding="utf-8"))
                last_synced = saved_data.get("last_synced", "unknown")
                print(
                    f"Warning: Could not refresh Google Sheet ({error}); "
                    f"falling back to saved records from {last_synced}.",
                    file=sys.stderr
                )
                return saved_data.get("records", [])
            except Exception:
                pass
        raise error


def get_local_applied_slugs(applications_dir: Path | None = None) -> list[dict[str, str]]:
    """Inspect local applications directory to complement Google Sheet tracking."""
    if applications_dir is None:
        applications_dir = Path(__file__).resolve().parents[1] / "applications"
    if not applications_dir.is_dir():
        return []

    records = []
    for folder in applications_dir.iterdir():
        if folder.is_dir() and not folder.name.startswith("."):
            parts = folder.name.split("-", 1)
            company = parts[0]
            role = parts[1] if len(parts) > 1 else ""
            records.append({
                "company": company.replace("-", " "),
                "role": role.replace("-", " "),
                "raw": {"source": f"applications/{folder.name}"},
            })
    return records


def check_applied(company: str, role: str, applied_records: list[dict[str, str]]) -> dict[str, str] | None:
    """Check if (company, role) matches any record in applied_records.

    Returns the matching applied record dict if found, else None.
    """
    target_comp = normalize_company(company)
    target_role = normalize_role(role)
    target_role_words = set(target_role.split())

    for rec in applied_records:
        rec_comp = normalize_company(rec["company"])
        rec_role = normalize_role(rec["role"])

        # Check company match
        comp_match = (
            target_comp == rec_comp
            or (target_comp and target_comp in rec_comp)
            or (rec_comp and rec_comp in target_comp)
        )
        if not comp_match:
            continue

        # Check role match
        # 1. Exact or substring normalized match
        if target_role == rec_role or (target_role and target_role in rec_role) or (rec_role and rec_role in target_role):
            return rec

        # 2. Significant word overlap (e.g. at least 60% of significant words match)
        rec_role_words = set(rec_role.split())
        common_words = target_role_words.intersection(rec_role_words)
        if len(common_words) >= 2 and len(common_words) >= min(len(target_role_words), len(rec_role_words)) * 0.6:
            return rec

    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sync", action="store_true", help="Sync and save today's snapshot from Google Sheet")
    parser.add_argument("--status", action="store_true", help="Show current sync status and total applied records")
    parser.add_argument("--list", "-l", action="store_true", help="List all saved applied roles")
    parser.add_argument("--sheet-url", help="Override Google Sheet URL")
    parser.add_argument("--company", "-c", help="Company to check")
    parser.add_argument("--role", "-r", help="Role to check")

    args = parser.parse_args()

    # Load environment
    from fetch_job import get_configured_sheet_url, get_all_applied_records
    sheet_url = args.sheet_url or get_configured_sheet_url()

    if args.sync:
        if not sheet_url:
            print("Error: No Google Sheet URL configured in .env (APPLIED_JOBS_SHEET_URL) or passed via --sheet-url", file=sys.stderr)
            return 1
        print(f"Syncing applied jobs from Google Sheet: {sheet_url}...")
        recs = fetch_sheet_records(sheet_url, force_refresh=True)
        today = datetime.date.today().isoformat()
        print(f"✓ Successfully saved daily snapshot for {today} ({len(recs)} applied jobs saved to {DEFAULT_SAVED_PATH}).")
        return 0

    if args.status:
        if not DEFAULT_SAVED_PATH.is_file():
            print(f"No local snapshot found at {DEFAULT_SAVED_PATH}.")
            print("Run with --sync to fetch today's snapshot from your Google Sheet.")
            return 0
        data = json.loads(DEFAULT_SAVED_PATH.read_text(encoding="utf-8"))
        print(f"Daily Applied Snapshot Status:")
        print(f"  Last synced date: {data.get('last_synced')}")
        print(f"  Updated at:       {data.get('updated_at')}")
        print(f"  Total records:    {data.get('count', len(data.get('records', [])))}")
        print(f"  Saved file:       {DEFAULT_SAVED_PATH}")
        return 0

    if args.list:
        records = get_all_applied_records(sheet_url=sheet_url)
        print(f"Applied Roles ({len(records)} total):")
        for idx, r in enumerate(records, 1):
            source = r.get("raw", {}).get("source", "Google Sheet")
            print(f"  [{idx}] {r['company']} - {r['role']} ({source})")
        return 0

    if args.company and args.role:
        records = get_all_applied_records(sheet_url=sheet_url)
        matched = check_applied(args.company, args.role, records)
        if matched:
            source = matched.get("raw", {}).get("source", "Google Sheet")
            print(f"⚠️  ALREADY APPLIED: {matched['company']} - {matched['role']} (Source: {source})")
            return 0
        else:
            print(f"✓ Not applied yet: {args.company} - {args.role}")
            return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
