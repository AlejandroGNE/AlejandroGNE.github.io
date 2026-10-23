---
name: website-publisher
description: Draft, revise, or publish content and scoped site updates for Alejandro Elenes's GitHub Pages website, AlejandroGNE/AlejandroGNE.github.io. Use when the user refers to their personal website, its Notes, Writing, Projects, or publishing there; not for unrelated websites.
---

# Website publisher

Target repository: `https://github.com/AlejandroGNE/AlejandroGNE.github.io.git`
Live site: `https://alejandrogne.github.io/`

## Find the source of truth

Use the current checkout if its Git origin is the target repository. Otherwise, check `WEBSITE_REPO` if the user configured it, then `$HOME/Documents/Codex/Projects/AlejandroGNE.github.io`. Verify the origin, not just the folder name. If no clone exists, clone the target into a suitable writable workspace; do not overwrite an existing folder. Shell and file access are required for the normal workflow; if unavailable, explain the missing capability rather than claiming files were updated.

Read the repository's `AGENTS.md`, `docs/AUTHORING.md`, and `docs/PUBLISHING.md`. These hold the maintained conventions; do not assume this skill carries all site context. Inspect the latest configuration, relevant layout/index, and an existing comparable entry. Fetch `origin/main`, preserve local changes, and work from current source in a clean checkout or isolated worktree. Avoid stale copies and simultaneous edits to another task's worktree.

## Complete the requested task

Determine whether the user requested a draft, revision, or publication. Turn supplied material into the appropriate content type using `_templates/`. Preserve the author's voice and factual evidence, request missing material facts, and verify current technical claims against primary sources where needed. Use current repository conventions rather than silently building new content infrastructure. Content-only tasks should preserve the shared design.

Run the documented checks, inspect the diff, and review the rendered result when relevant. Update the appropriate index according to its current implementation. For a draft, deliver a reviewable draft without pushing. For an explicit publishing or site-update request, proceed with its authorized scope; skill invocation alone does not authorize publication.

Publish using existing authorized GitHub access. Follow `docs/PUBLISHING.md` for normal commits/pushes, concurrency handling, Pages build checks, and live verification. Don't store credentials in this skill or repo. If access is missing, complete the local work and explain what needs authenticating; do not repeatedly attempt pushes or claim the site is updated.

Finish with the draft location or commit and live URL, checks actually performed, and any pending deployment. No new theme, taxonomy, automation, or unrelated rewrite is implied by a publishing request.
