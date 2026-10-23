# Writing for the site

Choose the type by purpose, not length alone:

| Type | Purpose | Current implementation |
| --- | --- | --- |
| Note | A useful observation, troubleshooting recipe, or lesson learned | `_notes/slug.md`, automatically listed at `/notes/` |
| Writing | A substantial explanation, tutorial, or essay | `writing/slug.md`, add a link to `writing.md` |
| Project | What was built, the approach, results, and artifacts | `projects/slug.md`, add a link to `projects.md` |

The PLEXOS-to-S3 article is currently a Note. Preserve that classification and URL unless a move is requested.

## Start from a template

Copy the matching file from `_templates/`. Replace every `REPLACE_...` marker and `YYYY-MM-DD` with real values. Templates are examples, not factual content. A folder is created when its first content file is added.

- Note: title and publication date are required. Its layout supplies the heading and date, so start the body with prose or `##` sections rather than repeating a `#` title.
- Writing: set title, date, description, and an explicit `/writing/slug/` permalink. It uses the existing default layout, so keep the template's title/date markup.
- Project: set title, date, description, and an explicit `/projects/slug/` permalink. Replace suggested sections as appropriate. Link only actual artifacts; omit unavailable results or links.

Descriptions and tags are optional on Notes. Tags currently have no archive pages. Projects and Writing do not yet have automatic listings: add a Markdown link and a short factual description to the relevant root index when publishing a new page. Do not add a second top-level heading to an index.

Use lowercase hyphenated filenames. Keep names stable after publication. Dates use `YYYY-MM-DD`; retain the original publication date for edits. Quote YAML titles and descriptions, especially when they contain a colon.

## Voice and evidence

Write clearly in Alejandro's voice. Use the source material supplied in the task; ask for missing facts that materially affect the content. Distinguish personal experience from general advice. Verify current technical claims against primary documentation when needed and link sources in the article. Do not infer successful experiments from a proposed method.

Use fenced code blocks with a language label. Prefer `##` and `###` for body sections. Remove real keys, passwords, private endpoints, and private identifiers from code examples, using descriptive placeholders where relevant. Don't change unrelated published prose while adding a new entry.

Store article-specific images/downloads in `assets/<slug>/` and link using `/assets/<slug>/filename`. Use descriptive image alt text and verify referenced files exist. Avoid generic filenames that can overwrite another article's assets.

## Drafts and updates

For a local draft, use a scratch folder outside the Jekyll source checkout or an uncommitted content file. `published: false` prevents normal Jekyll publication, but a file committed to this public repository is still public on GitHub. Use local drafts when the user asks to review before sharing.

Update an existing article in place. If moving it is explicitly requested, consider links and redirects before changing the URL. New titles do not require new URLs.

See [Publishing](PUBLISHING.md) for checks and deployment verification.
