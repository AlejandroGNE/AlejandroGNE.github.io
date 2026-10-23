# Alejandro Elenes's website

Repository: `https://github.com/AlejandroGNE/AlejandroGNE.github.io`
Live site: `https://alejandrogne.github.io/`
Publishing branch: `main` (GitHub Pages builds on push).

Read `docs/AUTHORING.md` for content and templates; read `docs/PUBLISHING.md` for validation, Git, and deployment. The reusable skill is `tools/website-publisher/SKILL.md`.

## Durable decisions

- Personal site for Alejandro Elenes, an energy systems researcher and engineer. Preserve the author's first-person voice and technical precision. Use supplied evidence for claims about his work; do not invent achievements, benchmarks, results, or sources.
- Jekyll on GitHub Pages, Markdown content, shared clean technical styling. Keep the shared header: name links Home, followed by Projects, Writing, Notes, About. Preserve the design during content-only tasks.
- Read the current `_config.yml`, relevant layout, index, and a comparable entry before deciding where new content belongs. Repository files supersede historical descriptions of implementation.
- Notes currently use `_notes/`, the `note` layout, and an automatic newest-first index. Projects and Writing currently have manual index pages; do not silently turn them into collections. `_layouts/entry.html` exists but is not configured as the default for published content.
- Content requests should use existing architecture. Broader site changes are appropriate when the user requests them.
- Keep established filenames/URLs stable when updating an article. Use the user's date for historical material; for new material use the current user-local date. Don't copy the template date or change the original publication date on routine edits.

## Working and publishing

- Verify the origin is this repository and inspect working changes before editing. Fetch current `origin/main`; preserve unrelated work. Use an isolated branch/worktree when necessary, especially for concurrent tasks.
- Draft/preview requests stay local unless the user requests a remote draft/PR. A request to publish authorizes a normal scoped commit and push to `main`; no redundant approval is needed. Skill invocation alone does not authorize publication.
- Run `ruby scripts/check_content.rb` (or pass the changed Markdown paths), `git diff --check`, and inspect the diff. Use the optional Jekyll build if the environment supports it; don't report a full build when only metadata checks ran.
- Stage only intended files. Never force-push or overwrite concurrent changes. If `main` advances, reconcile the new changes and recheck before retrying a normal push.
- Verify the GitHub Pages deployment for the pushed commit and fetch the changed live page. Report the commit and live URL, or the precise pending/failed verification. Cached HTML may remain for about ten minutes; use a fresh request before diagnosing a styling defect.
- Do not commit credentials or place machine-specific setup in this repository. Instruction files, tools, and templates must stay excluded from generated website pages.
