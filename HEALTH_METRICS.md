# Project activity and evidence

The authoritative methodology is [content/methodology.md](content/methodology.md), published at `/methodology/`.

Since methodology v2.0, the site shows activity indicators and sourced support routes. It does not publish a composite health score. Funding is unknown; stars and donation links do not establish financial sustainability. Historical v1.0 scores remain archived.

Project front matter uses TOML:

```toml
[health]
  funding = "unknown"
  maintenance = "unknown"
  contributors = "unknown"
  bus_factor = "unknown"
  methodology_version = "2.0"
  assessment = "automated"
```

The automation fills the activity fields. `contributors` retains legacy internal values (`healthy`, `declining`, `critical`), displayed as observed author-count bands. `bus_factor` retains legacy values (`low`, `medium`, `high`), displayed as commit concentration. Neither describes a verified human-maintainer assessment. Do not add a `score` field.

Checked support information lives in `data/project_support.json`, keyed by project filename without `.md`. Each entry requires `checked_at`, `context`, `actions` (label, URL, description), and `sources` (label, URL). Use official project sources and distinguish public participation routes from confirmed requests. Automation leaves these editorial records untouched.

Follow the editorial scope and correction process in the methodology when adding profiles, funding statements, current roles, or quotations.
