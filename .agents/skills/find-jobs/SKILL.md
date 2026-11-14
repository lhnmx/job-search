---
name: find-jobs
description: Search, discover, scrape, and verify active job and internship postings using Firecrawl, and stage them directly into the application tailoring workflow.
---

# Find Jobs & Internships

Use this skill when the user wants to search for current job or internship opportunities, verify employer postings, or stage an online job description directly into an application workspace for resume and cover letter tailoring.

## Overview & Prerequisites

- **Firecrawl CLI**: Installed locally at `/opt/homebrew/bin/firecrawl` (or via `npx firecrawl-cli`).
- **Free Keyless Tier**: Supports search, scrape, parse, and interact without an API key.
- **Authenticated Tier**: If an API key is available via `FIRECRAWL_API_KEY` (or after `firecrawl login --browser`), higher rate limits and Alexandria data providers are unlocked.
- **Deduplication / Applied Tracker**: Automatically cross-references searched/staged roles against previously applied roles from your Google Sheet (`APPLIED_JOBS_SHEET_URL` in `.env`) and local applications workspace.
- **Privacy & Storage**: Retrieved postings are saved to `applications/<company-role>/job_description.md` (which is gitignored).

---

## Workflow Steps

### 1. Discover Opportunities
Search for active roles using the Firecrawl CLI or the repo helper script:

```bash
uv run python scripts/fetch_job.py --search "software engineering intern summer 2025" --limit 5
```

Or using the Firecrawl CLI directly:
```bash
firecrawl search "<role> <location or remote> <term>" --sources web --json
```

Filter for active opportunities, prioritizing direct employer postings (e.g. Greenhouse, Lever, Workday, company careers sites) over aggregator listings.

### 2. Verify Posting Status & Deduplication
Before presenting an opening as verified:
- Check whether the role was already applied to:
  ```bash
  uv run python scripts/fetch_job.py --check-applied --company "<company>" --role "<role>"
  ```
  During `--search`, results matching your Google Sheet or local workspace are automatically badged with `⚠️ [ALREADY APPLIED]`.
- Scrape the official posting using `firecrawl scrape "<posting-url>" --only-main-content`.
- Check application status, closing dates, expiration banners, or redirected links.
- Confirm whether applications are actively being accepted. If ambiguous or closed, exclude or clearly mark it as unverified.

### 3. Stage Application Workspace
When a role is selected, stage it into its own application folder:

```bash
uv run python scripts/fetch_job.py "<posting-url>" --company "<company>" --role "<role>"
# OR
uv run python scripts/fetch_job.py "<posting-url>" --target applications/<company-role>
```

If the role matches an already-applied job in your Google Sheet or workspace, staging will warn and abort unless `--force` (or `-f`) is supplied.

This creates `applications/<company-role>/job_description.md` containing the extracted, clean markdown of the role requirements and qualifications.

### 4. Seamless Handoff to Tailoring
Once staged:
1. Review the requirements and qualifications in `applications/<company-role>/job_description.md`.
2. Select the closest track baseline from `pre-made/<track>/resume.md` (e.g. `pre-made/tech-swe/`).
3. Tailor the resume and cover letter using `$tailor-resume` and `$tailor-cover-letter` or `scripts/prepare_application.py`:
   ```bash
   uv run python scripts/prepare_application.py applications/<company-role> --base pre-made/<track>
   ```
4. Build and verify the 1-page A4 PDFs and present the complete diff and visual renders for user review.
