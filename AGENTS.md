# Resume Repository Instructions


## Portable entry point and local preferences

Any assistant with repository access can follow these rules by reading this file and the applicable `SKILL.md` directly. Automatic skill discovery and provider-specific metadata are optional. See `docs/PORTABLE_WORKFLOW.md` for local commands and manual Markdown handoff.

If `.resume/preferences.md` exists, read it for applicant-specific writing and formatting preferences. Preserve it locally; never publish it or assume it exists on another clone. Default PDF names are `Resume.pdf` and `Cover_Letter.pdf`; `.resume/settings.json` may set `resume_pdf` and `cover_letter_pdf` to plain PDF filenames. Wherever the rules mention default output names, use the configured filename when present. Existing private materials stay untouched.

## Purpose

This repository maintains one comprehensive resume reference and multiple application-specific resume versions.

## Public repository boundary

- `public/` is the only tracked resume publication folder. It contains the approved public Markdown resume and one-page PDF.
- `master/`, `pre-made/`, and `applications/` are private local workspace directories. Keep them on disk, but never stage or commit them.
- Personalized cover letters and compiled cover-letter PDFs are private. Public cover-letter templates and tooling must use fictional example details only.
- Never copy private material into a tracked location unless the user explicitly approves that exact artifact for publication.

Before editing, identify which of these the user is requesting:

1. A change to the comprehensive reference in `master/resume.md`.
2. A change to an existing tailored version (only when the user explicitly points to a specific file or folder).
3. A new tailored version for a job, company, or discipline.
4. Discovering or scraping a job/internship posting with Firecrawl and staging it into `applications/<company-role>/job_description.md` (see `scripts/fetch_job.py` and `.agents/skills/find-jobs/SKILL.md`).

Do not treat these as interchangeable.

### Do Not Inspect `applications/`

The `applications/` directory contains ephemeral, transient tailored resumes that the user periodically deletes.
- **NEVER** inspect, read, search, grep, list, or examine the `applications/` directory when asked to tailor a resume. Inspecting it is a waste of time.
- `applications/` is strictly a write destination for generated outputs (e.g., `applications/<company-role>/`), never an input, example catalog, or reference source.
- Reference facts, projects, and skills come **exclusively** from `master/resume.md`, and starting track baselines come **exclusively** from `pre-made/`.
- Never look for past applications or base a new resume on a past tailored version in `applications/`.
- Narrow exception to the restrictions above: the main agent and its reviewer may read the exact resume artifacts created in the current task for review, revision, and verification. This does not authorize directory browsing or reading other applications.
- Use one independent recruiter-perspective subagent review for a newly tailored resume when delegation is available, following `tailor-resume/SKILL.md`. This review delegation is allowed within the active task despite the nested-chat restrictions below; do not launch terminal model chats or require another API key. The main agent retains responsibility for tailoring and verification.

## Canonical Reference: `master/resume.md`

`master/resume.md` is the canonical content library and source of truth for verified resume facts. It is maintained as a format-neutral Markdown collection of all verified experiences, projects, and skills (no `.tex` or `.pdf` resides in `master/`).

Only active, uncommented resume content is verified as the user's. Commented-out resume entries, bullets, projects, awards, skills, and examples are not the user's claims and must never be activated, proposed, or used in any resume version.

- It should accumulate all verified positions, bullet points, projects, skills, awards, and education details.
- It may be arbitrarily long. Do not shorten it merely to meet a one-page resume convention.
- Do not remove content from it to make a tailored application stronger.
- Preserve unrelated reference content whenever adding or updating material.
- Build new tailored versions from the latest `master/resume.md` unless the user explicitly names another starting point.

### Interactive assistant source rules

The repo-specific `tailor-resume` skill is the interactive workflow. It follows a stricter append-only policy for the master source of truth:

- Automated skill operations may append accepted bullets, projects, or facts to `master/resume.md`.
- The skill must never replace or delete existing master content.
- Tailored versions may replace or remove their own content without changing the master source.
- A tailored proposal is appended to the master only after the user explicitly selects `/source`.
- A new metric, responsibility, technology, or outcome requires explicit user confirmation before the skill may treat it as verified.
- Tailoring must happen directly in the active assistant conversation. Do not create a nested model chat, terminal chat interface, or require a separate API key.
- **Primary Tailoring Workflow (Fast Markdown Diff)**:
  - Do NOT inspect, read, or search the `applications/` folder (it contains transient files and is never a reference source).
  - Select the closest base `resume.md` directly from `pre-made/` (or `master/resume.md`).
  - Create the tailored version in `applications/<company-role>/resume.md`.
  - **Always show the complete full diff**: Present the full, unabbreviated in-chat Markdown diff across the entire resume (never truncate, summarize, or omit sections) alongside a concise bullet/skill rationale against the base resume. Whenever tweaks are made, always output the complete updated full diff.
  - Present the verified PDF alongside the complete diff for review. The user reviews the full diff directly in chat or using `uv run python scripts/diff_resume.py <base> <target>` / native IDE diff viewers.
  - Immediately after tailoring and after each requested tweak, compile to PDF without waiting for separate build approval using `uv run python scripts/md_to_latex.py <target>/resume.md --template jake --build` and verify 1-page A4 compliance (never use `vmock` — it is discontinued; condense content if space is tight).
- **Detailed Entry-by-Entry Mode (Ledger)**:
  - If the user explicitly asks for step-by-step entry-by-entry review, use the ledger workflow under `.resume/sessions/`. Employer, historical title, and date lines remain locked context.

These interactive-tool rules take precedence over the default manual merge semantics below whenever the skill is applying a change.

### Default merge semantics

When the user supplies new content for the general reference, apply these defaults unless the user explicitly says otherwise:

- **Position bullet points:** Replace the active bullets for the named position with the newly supplied bullets. Do not delete the position or unrelated positions.
- **Projects:** Append new projects. Do not replace, hide, comment out, or delete existing projects.
- **Awards, skills, education, and other sections:** Append new entries or update only the explicitly named entry. Preserve unrelated entries.
- **Metrics, dates, technologies, and employer names:** Treat user-provided facts as authoritative. Do not silently weaken, normalize, or reinterpret them.
- **Layout and contact information:** Preserve them unless the user explicitly requests a layout or contact change.

If a supplied attachment contains a full LaTeX document but the user asks to use its bullets or content, merge the requested content into the current source. Do not blindly replace the entire file or reintroduce previously fixed LaTeX problems.

## Tailored Versions

Tailored versions live in folders named `<purpose>` or `<company-role>`.

Examples:

- `finance-consulting/`
- `macquarie-asset-management/`

For a new tailored version:

1. Create a descriptive internal folder (e.g. `<company-role>/`).
2. Adapt from the closest `pre-made/<track>/resume.md` (or `master/resume.md`).
3. Select, reorder, condense, or align the most relevant verified content to the job description.
4. Preserve factual accuracy and quantified outcomes.
5. Immediately compile and verify the tailored version using `uv run python scripts/md_to_latex.py <target>/resume.md --template jake --build`, ensuring exactly 1 A4 page (never use `vmock`). Do not wait for separate build approval.
6. Present the verified PDF alongside the complete, unabbreviated in-chat diff for review. After requested tweaks, rebuild, verify, and show the updated PDF and complete diff in the same turn.

Tailored versions are selective snapshots. They do not replace the reference and do not automatically update existing variants unless the user asks for synchronization.

### Reusable premade formats

Reusable variants under `pre-made/<purpose>/` each contain:

- `resume.md` as the format-neutral content source.
- `_resume.tex` as the standalone compiled LaTeX source (using the default Jake layout).
- `Resume.pdf` as the built, normalized 1-page A4 PDF.

Formatting templates live under `templates/`:
- `templates/Jake/` for the standard 11pt Jake template.
- `templates/Loc/` for the moderncv template.
- `templates/Vmock/` (discontinued — do not use).

Use `scripts/md_to_latex.py` to compile `resume.md` to supported templates (`jake`, `loc`).

### Tailoring rules

- Never invent experience, investment responsibilities, metrics, dates, technologies, or outcomes.
- Never change an official historical job title merely to match a job description.
- A targeted headline or section title may be adjusted when useful, as long as it is clearly positioning rather than a claimed past role.
- Prefer evidence from the reference that directly matches the job description.
- Flag material eligibility mismatches to the user, but do not alter truthful education or employment facts to hide them.
- Every tailored version must be exactly one A4 page. This is a hard submission rule, not a per-job preference.
- Preserve every verified work position with at least one substantive bullet. Allocate additional bullets to the roles most relevant to the job description, and consolidate repeated technology lists before removing a position.
- Treat work experience as mandatory coverage and projects as a selective portfolio. Never drop a work position through the project-selection workflow.
- Resume variants created by the interactive skill must be exactly one A4 page.
- **Never use Vmock template (discontinued)**: The Vmock template (`templates/Vmock/`, `--template vmock`) is discontinued. Agents must NEVER use, propose, or compile with Vmock. Always use the standard Jake template (`--template jake`). If content overflows one A4 page, condense bullet wording, tighten line wraps, or trim projects/bullets to fit within the 1-page Jake budget.
- **Do not inspect `applications/`**: Never look at, search, grep, or read files in `applications/` to find previous versions, context, or examples. They are transient and periodically deleted. All tailoring references come strictly from `pre-made/` and `master/resume.md`.

## Cover Letter Workflow

Cover letters follow the same principles as the resume tailoring workflow:

- **Do not inspect `applications/`**: Reference facts and accomplishments come strictly from `master/resume.md`, and baseline starting letters come from `pre-made/<track>/cover_letter.md`.
- **Target destination**: Tailored letters are written to `applications/<company-role>/cover_letter.md`.
- **4-Paragraph Narrative**:
  1. *The Hook & Trajectory*: Position, company, the applicant’s verified education or current work, and narrative career bridge.
  2. *Core Proof & Impact*: 1-2 relevant, verified accomplishments from `master/resume.md`, quantified when verified metrics exist. Never invent unverified metrics.
  3. *Technical & Builder Progression*: Real projects, hackathons, cloud systems, and coursework.
  4. *Company Alignment & Call to Action*: Specific interest in the company's product, team, or challenge + value proposition.
- **Zero Placeholders**: Placeholders like `[Company Name]`, `[Position Title]`, or `______` must be completely replaced with concrete target details before building.
- **Relevant Projects**: Select projects only from the applicant’s active master content. Honor explicit local preferences without treating sample projects as universal requirements.
- **No Location / Address**: Cover letters must not include applicant location or company address/location lines. The recipient block contains only the company name (and optional team).
- **Strict 1-Page A4 Budget**: The letter must fit on a single A4 page.
- **Build & Verification**:
  - Build and verify immediately after tailoring and after every requested tweak, without waiting for separate build approval. Present the verified PDF alongside the complete in-chat diff for review.
  - Compile and build: `uv run python scripts/md_to_cover_letter.py <target-folder>/cover_letter.md --build`
  - Or directly build an existing `_cover_letter.tex`: `./scripts/build_cover_letter.sh <target-folder>`
  - The build script normalizes output to PDF 1.5 at `<target-folder>/Cover_Letter.pdf`.
  - Compare changes with `uv run python scripts/diff_cover_letter.py <base-path> <target-path>`.
  - Use the repo-specific `$tailor-cover-letter` skill for the conversational workflow.

## Projects Are Additive

Projects in `master/resume.md` are a reference inventory.

- Adding a project means placing it alongside existing projects.
- Do not infer that a newly supplied project should replace the currently visible project.
- Removing or commenting out a project requires an explicit user request.
- Length is not a reason to delete a project from the general reference.

## Build and Output Rules

Use the existing build script for tailored or pre-made folders containing `_resume.tex`:

```bash
./scripts/build_resume.sh "resume-folder-name"
```

- A folder argument builds that internal version (e.g. `./scripts/build_resume.sh pre-made/finance-consulting`).
- `master/` is maintained purely as Markdown (`master/resume.md`) and is not compiled into a PDF.
- To compile a markdown resume directly, use `uv run python scripts/md_to_latex.py <path/to/resume.md> --template jake --build`.
- A tailored build writes exactly `<selected-resume-folder>/Resume.pdf`.
- Every active tailored or premade resume folder contains `_resume.tex` and its independent `Resume.pdf`.
- Shared LaTeX classes, styles, and fonts belong only in `shared/latex/`.
- Do not duplicate shared support files inside resume folders.
- The build script must compile in a temporary directory containing the selected `_resume.tex` and copied `shared/latex/` files.
- Do not expose internal version names in the PDF filename.
- A build may overwrite only the PDF inside the selected tailored folder. It must never overwrite another version's PDF.
- Do not use a shared output PDF or a central `output/pdf/` directory.
- Tectonic is installed through Homebrew. Prefer the installed `tectonic` command.
- The build script must normalize Tectonic output to PDF 1.5 with a classic cross-reference table before publishing it, while preserving text, page geometry, and hyperlinks.
- Built resume text must not contain Unicode presentation-form ligatures such as `ﬀ`; the PDF normalizer expands their Unicode mappings for ATS compatibility without changing their visual rendering.
- The Jake-style source must use T1 encoding and Latin Modern's Type 1 fonts so legacy resume parsers do not have to interpret CID Type 0 `Identity-H` text fonts.
- Build intermediates must remain temporary and should be removed after verification.

## PDF Verification

After every resume build:

1. Confirm the PDF compiles successfully.
2. Check page count and A4 page size.
3. Render every page to PNG and inspect it visually.
4. Check for clipped text, overlap, broken glyphs, awkward page breaks, and orphaned headings.
5. Confirm important content is text-extractable for ATS use.
6. Confirm hyperlinks remain present.
7. Remove temporary QA files before completing the task.

For the master source of truth, multiple pages are acceptable. Use clean page boundaries rather than deleting content. Every tailored version must remain exactly one A4 page.

## Editing Workflow

Follow this sequence and explain changes step by step:

1. Read this file and inspect `git status`.
2. Identify whether the target is the general reference, an existing variant, or a new variant. For a new variant, do NOT inspect or search `applications/` (it is transient); select base content exclusively from `pre-made/` or `master/resume.md`.
3. Read all supplied attachments completely.
4. State the intended replace-versus-append behavior before editing.
5. Preserve unrelated user changes and resume content.
6. Edit the appropriate `_resume.tex` source, not the generated PDF.
7. Build the requested version.
8. Perform PDF and content verification.
9. Update `README.md` when adding a durable new workflow or named variant.
10. Report what changed, what remained untouched, and whether changes are committed or pushed.

## Git and Python

- Do not commit or push changes unless the user explicitly requests it.
- Do not stage unrelated worktree changes.
- Keep `.venv/`, caches, LaTeX intermediates, and temporary renders untracked.
- The validator uses uv with Python 3.12. Keep `pyproject.toml`, `.python-version`, and `uv.lock` tracked when its dependencies change.
- Interactive skill sessions belong under the gitignored `.resume/sessions/` directory.
- Use `uv run python -m unittest discover -v` for the validator test suite.
- Use the repo-specific `$tailor-resume` skill for the primary conversational workflow. After building, run `uv run python .agents/skills/tailor-resume/scripts/validate_resume.py "<target-folder>"` before visual PDF QA.
