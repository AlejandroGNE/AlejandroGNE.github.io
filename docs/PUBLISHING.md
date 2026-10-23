# Publishing and handoff

## Repository and access

Use a clone of `https://github.com/AlejandroGNE/AlejandroGNE.github.io.git`. Validate its origin before any push. GitHub Pages publishes `main` at `https://alejandrogne.github.io/`.

Authenticate GitHub separately from the skill. Preferred local setup is GitHub CLI (`gh auth login`, then `gh auth setup-git`), or existing authorized SSH/HTTPS credentials. Use `gh auth status` to inspect access; don't print tokens or save credentials in the repo. A skill does not grant access. If authentication or permissions block publication, finish the local draft/checks and identify the precise action the user needs to complete. An already-authenticated GitHub browser session is a fallback, not a dependency of the skill.

## Before editing

1. Check `git remote -v`, `git status --short`, and fetch `origin/main`.
2. Start from current `origin/main` in a clean checkout or isolated worktree. Never discard another task's changes.
3. Read `AGENTS.md`, `docs/AUTHORING.md`, `_config.yml`, and the relevant layout/index.
4. Clarify only facts or decisions that affect the requested work. Preserve the user's distinction between drafting and publishing.

## Checks

- `ruby scripts/check_content.rb`: checks published content metadata, dates, configured collections/layouts, and duplicate explicit permalinks. Passing filenames limits content checks to those files; it still checks global duplicate URLs. It does not render Liquid, build Jekyll, or verify external links.
- `git diff --check` and review the exact diff, including newly added files.
- Review content accuracy, working links, asset paths, and code formatting. Inspect a rendered preview when layout or embedded media changes warrant it.
- Optional full build: in an environment with the GitHub Pages/Jekyll dependencies installed, run its configured Jekyll build. This repo does not yet pin a local build environment; do not install arbitrary dependency versions and describe them as production-equivalent. GitHub's Pages workflow is the deployment build.

## Commit and deploy

For a publishing request, stage only intended files, make a descriptive commit, and push normally to `main`. Do not force-push. A non-fast-forward failure means someone else updated the repository: fetch, review and reconcile their work, repeat affected checks, and retry. If branch protection requires a pull request, use a PR and report that publication is awaiting merge.

With GitHub CLI, inspect runs for the pushed commit:

```sh
gh run list --repo AlejandroGNE/AlejandroGNE.github.io --commit COMMIT_SHA
```

Inspect the actual Pages run and wait for its conclusion. A successful push is not proof of deployment. Once deployed, fetch the changed URL with a cache-busting query such as `?v=COMMIT_SHA`; check the actual title/body and links. The shared stylesheet URL currently includes the build commit and can help identify which version was served. If no matching run is visible, inspect the repository's Actions/deployments rather than guessing a run ID.

The site can serve cached HTML for roughly ten minutes. Fresh reads and matching deployment evidence are needed before treating a temporary mismatch as a code issue.

Report changed files, checks performed, commit, and live URL. If deployment is still pending or failed, say so rather than declaring the article live.

## A fresh chat

A chat working inside this repo reads `AGENTS.md`. A personal `website-publisher` skill can also locate the repository from another workspace. Its portable source is `tools/website-publisher/`; install that folder as a personal skill on each machine where needed. Authentication must be configured separately on each execution environment. Keep instructions in the repo current when the architecture changes.
