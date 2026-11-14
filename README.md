# Agentic Resume Customization

A local-first system for turning one comprehensive resume into focused, job-specific applications with your choice of AI assistant.

Bring your own resume, add any reusable content or layout templates you prefer, and give the agent a job description. The workflow selects relevant experience, proposes targeted wording, shows the complete diff for review, and builds a verified one-page A4 PDF without inventing facts.

[View the example resume](public/resume.md) · [Download the example PDF](public/Morgan_Le_Resume.pdf)

## What it does

- Uses your private master resume as the source of truth.
- Reuses optional track-specific baselines for engineering, data science, finance, consulting, or other roles.
- Reviews every proposed change with you in the active assistant conversation.
- Preserves verified employers, titles, dates, metrics, and responsibilities.
- Builds ATS-readable PDFs with working hyperlinks.
- Keeps private resumes, applications, and cover letters out of Git.

## Quick start

### 1. Clone and install

```bash
git clone https://github.com/lhnmx/job-search.git
cd job-search

# macOS
brew install uv tectonic poppler
uv sync
```

Requirements:

- An assistant that can read repository files and run commands, or a chat assistant with manual Markdown handoff. No particular provider, model, or repository skill loader is required.
- Python 3.12 and [uv](https://docs.astral.sh/uv/)
- [Tectonic](https://tectonic-typesetting.github.io/) for PDF builds
- [Poppler](https://poppler.freedesktop.org/) for visual PDF checks

### 2. Add your resume

Create the private workspace and add your comprehensive resume:

```bash
uv run python scripts/init_workspace.py --resume /path/to/your/resume.md
uv run python scripts/doctor.py
```

This copies your Markdown into `master/resume.md` without overwriting existing content. It is private and ignored by Git. To try the public sample instead, run `uv run python scripts/init_workspace.py --example`; sample facts are for demonstration only.

On Linux, install uv using its [official instructions](https://docs.astral.sh/uv/getting-started/installation/), install [Tectonic](https://tectonic-typesetting.github.io/en-US/install.html), and install Poppler (`poppler-utils` on Debian/Ubuntu). Run `uv sync` afterward. The builders require Bash: use a Linux environment such as WSL on Windows. Native Windows shell builds are not supported. Tectonic may download its TeX resources on the first build.

`doctor.py` reports missing prerequisites without installing anything. Run the tests on a fresh clone with `uv run python -m unittest discover -v`; they use fictional fixtures and require no private resume.

The expected Markdown structure is simple:

```markdown
# Your Name

[email@example.com](mailto:email@example.com) | 212-555-0100 | [Portfolio](https://example.com)

## Experience

### Company | Role | Location
*Jan 2024 – Present*
- Accomplished a specific outcome using a specific skill.
- **Technologies:** Python, SQL
```

### 3. Add your own templates (optional)

Academic research can live under Projects with an affiliation in the second
heading field. Add source-only `**Historical Role:** <verified role>` metadata
when local preferences allow presenting it as experience for a specific track;
the validator checks that affiliation, role, and dates when it moves sections.

The included Jake layout works out of the box. You can also add private, reusable content baselines:

```text
pre-made/
  software-engineering/
    resume.md
    cover_letter.md       # optional
  data-science/
    resume.md
```

Formatting templates live in `templates/`. Add or adapt a layout there if you want a different visual style.

### 4. Find jobs & internships (optional)

Discover and verify current openings directly using Firecrawl, with automatic daily deduplication against your Google Sheet:

```bash
# Sync today's applied jobs from your Google Sheet (saves daily snapshot locally):
uv run python scripts/applied_jobs.py --sync

# Search for active roles (automatically flags roles you've applied to):
uv run python scripts/fetch_job.py --search "software engineering intern summer 2025" --limit 5

# Scrape an official posting and stage it into an application workspace:
uv run python scripts/fetch_job.py "<posting-url>" --company "<company>" --role "<role>"
```

This verifies that the position is open and saves the clean markdown to `applications/<company-role>/job_description.md`. You can also load `.agents/skills/find-jobs/SKILL.md` in your assistant.

### 5. Tailor for a job

Open the repository in your preferred assistant and ask:

```text
Read AGENTS.md and .agents/skills/tailor-resume/SKILL.md.
Tailor my resume for this job description:

<paste the complete job description>
```

The agent will:

1. Read the job description and your private resume.
2. Select the closest optional baseline, when available.
3. Propose targeted bullets and project choices using verified facts only.
4. Save the tailored Markdown under `applications/<company-role>/`.
5. Immediately build, validate, and visually inspect an ATS-readable, one-page A4 PDF.
6. When subagents are available, get an independent recruiter-perspective review grounded in the job description, separating explicit requirements from editorial judgment. The reviewer gives feedback; the main agent checks facts and applies justified improvements.
7. Rebuild and verify any revisions, then show the PDF, complete Markdown diff, and accepted/rejected feedback with reasons, without waiting for separate build approval. If delegation is unavailable, disclose that and use a self-review.

For a cover letter, load `.agents/skills/tailor-cover-letter/SKILL.md` in the same way. Codex users may still invoke `$tailor-resume` or `$tailor-cover-letter`; automatic skill discovery is optional. Requested tweaks trigger an immediate rebuild and verification, followed by the updated PDF and complete diff. An explicit request for Markdown only or to defer building takes precedence.

## Output

Each private application is self-contained:

```text
applications/<company-role>/
  resume.md
  _resume.tex
  Resume.pdf
  cover_letter.md                 # optional
  _cover_letter.tex               # optional
  Cover_Letter.pdf      # optional
```

`applications/` is ignored by Git, so generated application materials remain local.

## Useful commands

Build a Markdown resume with the default Jake template:

```bash
uv run python scripts/md_to_latex.py \
  applications/<company-role>/resume.md \
  --template jake \
  --build
```

Compare a baseline with a tailored resume:

```bash
uv run python scripts/diff_resume.py \
  pre-made/<track> \
  applications/<company-role>
```

Validate a completed resume:

```bash
uv run python .agents/skills/tailor-resume/scripts/validate_resume.py \
  applications/<company-role>
```

Run the test suite:

```bash
uv run python -m unittest discover -v
# Include real PDF build checks when Tectonic and Poppler are installed:
RESUME_PDF_INTEGRATION=1 uv run python -m unittest discover -v
```

## Build and review in one action

After tailoring the Markdown, prepare the resume with one command:

```bash
uv run python scripts/prepare_application.py applications/<company-role> \
  --base pre-made/<track>
```

To build the resume and cover letter together, add the letter baseline:

```bash
uv run python scripts/prepare_application.py applications/<company-role> \
  --base pre-made/<track> \
  --cover-letter-base pre-made/<track>
```

For a cover letter alone, supply only `--cover-letter-base`. Baselines must come
from `pre-made/` or `master/`; the command reads only the selected application.
New resume claims require explicit user confirmation before supplying a repeated
`--confirmed-fact` argument.

This action builds with Jake, validates resume content against the master,
checks each PDF for exactly one A4 page, extractable text, hyperlinks, and PDF
compatibility, and renders page images for visual review. Both documents must
pass before it replaces any existing submission outputs. It prints the complete
Markdown diff with all unchanged context and saves private review copies, diffs,
images, and a report under `.resume/reviews/<review-id>/`.

Inspect the page images before submitting: automated PDF checks cannot confirm
that text is unclipped or free of overlap. Cover-letter facts still require
conversation review; this command checks their PDF and placeholders. Review
folders are intentionally retained for review and can be deleted afterward.
Failed attempts remove their temporary build and review files automatically.

The standalone builders also verify PDFs before replacing the previous output.
Vmock is no longer an available converter option.

See [the portable chat workflow guide](docs/PORTABLE_WORKFLOW.md) for assistants
with repository access and manual Markdown handoff. All tailoring and review
happen in the active chat; there is no local web application to run.

## Personal preferences

Default output names are `Resume.pdf` and `Cover_Letter.pdf`. Optional gitignored `.resume/settings.json` may contain:

```json
{"resume_pdf": "Your_Name_Resume.pdf", "cover_letter_pdf": "Your_Name_Cover_Letter.pdf"}
```

Put applicant-specific writing and layout preferences in `.resume/preferences.md`. Assistants read this optional file alongside the shared rules; they must confirm facts against the master. New clones do not inherit another applicant's private preferences.

Cover-letter openings use natural target-role wording, such as “the Software Engineering Intern position,” rather than reproducing a full posting title with recruiting labels or requisition codes. Use title case for the role name, keep surrounding words such as “position” lowercase, and preserve official company/product capitalization and technical acronyms. Preserve the role, specialization, and internship level.

## Public and private files

Only the approved example resume and reusable system code belong in the public repository.

| Path | Purpose | Tracked |
| --- | --- | --- |
| `public/` | Approved public resume and PDF | Yes |
| `templates/` | Generic formatting templates | Yes |
| `.agents/skills/`, `scripts/` | Agentic workflow and tooling | Yes |
| `master/` | Comprehensive personal resume | No |
| `pre-made/` | Personal reusable baselines | No |
| `applications/` | Tailored resumes and cover letters | No |
| `.resume/` | Sessions, previews, and private backups | No |

`master/`, `pre-made/`, `applications/`, and `.resume/` remain local: commits and pushes do not synchronize these gitignored folders. Updating private resume sources or rebuilding their PDFs does not update the approved artifacts in `public/`. Publishing a private artifact requires explicit approval for that exact artifact; do not force-add private folders to Git.

Previously committed private files remain in Git history until the history is rewritten. Ignoring them prevents future commits but does not erase earlier revisions.

## Core guarantees

- Never invent experience, metrics, technologies, dates, or outcomes.
- Never change an official historical job title to match a posting.
- Keep every verified work position represented with at least one substantive bullet; tools lists do not count.
- Exclude commented-out entries, bullets, skills, and metrics from generated resumes and verified facts.
- Treat projects as selectable; removing one from an application never removes it from the master resume.
- Require explicit review before accepting rewritten content.
- Produce exactly one A4 page for every tailored resume.
- Never commit or push without explicit permission.

See [AGENTS.md](AGENTS.md) for repository rules and [SPEC.md](SPEC.md) for the detailed workflow contract.

## License

No open-source license is included. The repository may be visible and forkable on GitHub, but reuse rights remain reserved until the owner chooses a license.
