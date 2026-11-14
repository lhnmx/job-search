---
name: tailor-resume
description: Tailor, review, and build a verified one-page resume for a supplied job description, or review resume entries and numbered bullets in this repository.
---

# Tailor Resume

Use the active assistant conversation. Read `AGENTS.md` and, when present, the gitignored `.resume/preferences.md`. Do not require a particular model, provider, skill loader, or another model session. Instructions can be loaded by path when automatic skill discovery is unavailable.

## Sources and decisions

- Verified facts come only from active, uncommented `master/resume.md` content and explicit user confirmations. Read the complete job description and master before starting.
- Select an available `pre-made/<track>/resume.md` baseline when useful; otherwise use the master. Never invent a baseline or browse `applications/` for references.
- Create the new tailored Markdown in `applications/<company-role>/resume.md`. Read an existing application only when the user explicitly selects it for updates. The main agent and reviewer may read the exact artifacts created in the current task for review and verification; never browse other applications.
- Preserve employers, official titles, dates, contact details, and verified outcomes. Keep every work position with at least one substantive bullet; prefer more coverage for relevant roles. A technologies line is not substantive coverage.
- Keep at most two project and academic research entries combined across the entire tailored resume. Count academic research even when it appears under Experience. Reserve slots for entries required by local preferences before considering optional entries. Check the combined count before saving and after each revision, including entry-by-entry review.
- Honor local academic-research placement rules before applying experience coverage or optional-project limits. A research entry stored under projects may move into experience only for the application tracks explicitly allowed by those rules; use its verified affiliation, `**Historical Role:**` metadata, and dates. Do not duplicate it across sections or discard required research as an optional extra project.
- Prioritize relevant work experience while maintaining a balanced portfolio across the page. Default to two relevant projects (or academic research entries) to avoid excessive white space and fill the single-page layout cleanly. Ensure substantive coverage (at least one bullet plus technologies) for every work position, balancing bullets across experience and the two projects to strictly fit exactly one A4 page without overflowing or leaving awkward gaps.
- Use Self-Improving Computer Use / MongoDB's Harness Engineering Hackathon (3rd Place) as the default project, using only its active verified facts from master/resume.md. Select another project only when there is a strong, specific reason tied to the target job: it demonstrates essential relevant evidence that work experience and the MongoDB project do not cover. Explain that reason before substituting the project; a closer keyword or technology match alone is insufficient. Honor any explicit user project selection.
- Select projects and coursework from the actual applicant's verified inventory. Never assume the public example's employers, education, projects, skills, or metrics belong to the applicant.
- Follow the applicant's baseline and local layout preferences. Default to Jake, exactly one A4 page. Condense repetition before reducing substantive experience; Vmock is unavailable.
- Tailored edits do not change the master. Append accepted facts to the master only on an explicit source-of-truth request; never replace or delete master content automatically.

## Default: tailor, build, and review

1. Explain the selected baseline and intended changes before writing. Tailor only from verified material; ask for confirmation of any new fact.
2. Save the tailored Markdown and immediately build and validate. If using a baseline, run:
   ```bash
   uv run python scripts/prepare_application.py applications/<company-role> --base pre-made/<track>
   ```
   Use `--base master/resume.md` when no premade exists. Alternatively run the converter with `--template jake --build` and the validator below.
3. Run `uv run python .agents/skills/tailor-resume/scripts/validate_resume.py applications/<company-role>` before visual QA. Inspect the rendered page for clipping, overlap, glyphs, and awkward wraps. Automated checks do not substitute for visual inspection. Never present a failed or stale build as verified.
4. Run the independent recruiter-perspective review below. Apply justified changes using verified facts, then rebuild, validate, and visually inspect any revised output.
5. Present the verified PDF alongside the complete, unabbreviated Markdown diff against the saved baseline, including unchanged context. Explain the job-specific emphasis briefly. Resolve page overflow using verified wording and rebuild after each requested tweak.
6. Read the output filename from `.resume/settings.json` when present; defaults are `Resume.pdf` and `Cover_Letter.pdf`. Respect an explicit request to defer building or provide Markdown only.

## Independent recruiter-perspective review

For each newly tailored resume, delegate one review pass after the initial build and QA when subagents are available. Use a fresh context without the drafting rationale (for Codex, use `fork_turns="none"`; for Antigravity, use `invoke_subagent` with a clean prompt). Keep this within the active task; no separate user chat, terminal model session, or API key is needed. If delegation is unavailable, disclose that and perform a clearly labeled self-review.

Give the reviewer the full job description, current resume text and exact PDF/render paths, and applicable repository rules and local preferences. Assign this brief: "Review this resume from a recruiter's perspective for this specific job, and justify each suggested change." This is a simulated perspective, not recruiting credentials or knowledge of internal hiring criteria.

- First assess immediate clarity of relevant experience, concrete evidence for requested skills, and vague, repetitive, overstated, or confusing wording. Distinguish explicit job requirements from editorial judgment. Do not invent a company rubric, ATS score, or interview probability.
- After the first-impression assessment, consult active, uncommented `master/resume.md` content and supplied user-confirmed facts for stronger omitted evidence and factual checks. Never browse `applications/`; inspect only exact current-task artifacts supplied. Commented content is not applicant evidence.
- Return strengths and prioritized actionable findings. Identify each affected bullet or section, the relevant job requirement or labeled readability concern, and a concrete suggestion. Cite verified source evidence for additions; flag missing evidence as a question, not an invented claim. Return no findings when none are justified.
- Provide feedback only; do not edit files. Respect factual accuracy, all-position coverage, project limits, local preferences, and the one-page Jake layout. Review does not replace PDF validation or visual QA.
- The main agent evaluates suggestions, applies supported improvements, and asks the user before treating new facts as verified. Include a brief review summary and accepted/rejected suggestions with reasons alongside the final verified PDF and complete diff.
- Default to one pass, with at most one targeted follow-up if substantial issues remain after revision. Report unresolved concerns rather than looping. Minor user tweaks need no additional pass unless they introduce a substantive concern or the user requests it.

## Optional entry-by-entry review

Use `.agents/skills/tailor-resume/scripts/session_ledger.py` when the user requests detailed review. Persist explicit bullet/project decisions in atomic batches; employer, historical title, and date lines remain locked. Retain all jobs while selecting projects.

## Assistants without local tools

Read `docs/PORTABLE_WORKFLOW.md`. Ask the user to supply the active master, selected baseline, and job description. Return complete Markdown and the full diff in chat so the user can save and build locally. Report PDF verification as pending until the build and visual checks actually occur. No JSON handoff or separate application is required.
