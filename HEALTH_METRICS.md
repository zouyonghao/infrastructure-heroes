# Project activity and evidence

The authoritative methodology is [content/methodology.md](content/methodology.md), published at `/methodology/`.

Methodology v2.1 restores Healthy (80–100), Warning (60–79), and Critical (0–59) using an activity-based estimate: `(maintenance × 30 + contributors × 25 + concentration × 20) / 75`, rounded to the nearest integer. Unknown concentration is omitted and the remaining weights divide by 55. Missing required activity data stays unrated. Funding is unknown; stars and donation links do not establish financial sustainability. Historical v1.0 scores remain archived.

Project front matter uses TOML:

```toml
[health]
  funding = "unknown"
  maintenance = "unknown"
  contributors = "unknown"
  bus_factor = "unknown"
  methodology_version = "2.1"
  assessment = "automated"
```

The automation fills the activity fields. `contributors` retains legacy internal values (`healthy`, `declining`, `critical`), displayed as observed author-count bands. `bus_factor` retains legacy values (`low`, `medium`, `high`), displayed as Bus Factor risk. Neither describes a verified human-maintainer assessment. Automation writes `score` when sufficient activity data exists. Funding contributes neither points nor weight.

Checked support information lives in `data/project_support.json`, keyed by project filename without `.md`. Each entry requires `checked_at`, `context`, `actions` (label, URL, description), and `sources` (label, URL). Use official project sources and distinguish public participation routes from confirmed requests. Automation leaves these editorial records untouched.

Follow the editorial scope and correction process in the methodology when adding profiles, funding statements, current roles, or quotations.
