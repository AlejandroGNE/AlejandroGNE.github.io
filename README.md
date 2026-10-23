# Alejandro Elenes's personal website

[Live site](https://alejandrogne.github.io/) · [Authoring guide](docs/AUTHORING.md) · [Publishing guide](docs/PUBLISHING.md)

This is a Markdown/Jekyll site published by GitHub Pages from `main`.

Start a new coding-agent task in this repository and read [AGENTS.md](AGENTS.md), or use the personal `website-publisher` skill from another workspace. The reusable [skill source](tools/website-publisher/SKILL.md) lives here so its workflow travels with the repository.

Notes are currently configured as a collection with automatic listings. Projects and Writing use regular pages and manual indexes. Copy an appropriate file from [_templates](_templates), replace its placeholders, and follow the authoring guide. Documentation and templates are excluded from generated website pages.

Run metadata checks with:

```sh
ruby scripts/check_content.rb
```

A skill supplies instructions, not GitHub credentials. See the publishing guide for authentication, validation, and deployment verification.
