---
layout: default
title: Notes
permalink: /notes/
---

# Notes

Small things I've learned, figured out, or want to remember.

{% assign notes = site.notes | sort: "date" | reverse %}

{% for note in notes %}
## [{{ note.title }}]({{ note.url | relative_url }})

{{ note.date | date: "%B %-d, %Y" }}

{% endfor %}
