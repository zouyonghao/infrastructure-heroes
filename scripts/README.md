# Infrastructure Heroes - Data Automation Scripts

This directory contains the scripts that collect, score, and maintain the site's project data.

## Quick start

### 1. Install dependencies

Requires **Python >= 3.11** (the scripts use the standard-library `tomllib` to parse TOML front matter).

```bash
pip install -r requirements.txt   # requests (check_urls.py), Pillow (localize-images.py)
```

All other scripts use only the Python standard library.

### 2. Environment variables

```bash
export GITHUB_TOKEN="ghp_your_token_here"
```

Unauthenticated GitHub API access is limited to 60 requests per hour; setting `GITHUB_TOKEN` raises it to 5,000. Scripts read the token only from the environment — there is deliberately no `--token` flag, so tokens cannot leak into process listings or shell history.

## Script overview

| Script | Purpose |
|--------|---------|
| `fetch-github-metrics.py` | Fetch one repository's metrics, compute health, write project front matter |
| `batch-update-health.py` | Refresh health metrics for every project |
| `update-historical-data.py` | Write monthly snapshots to `data/historical/YYYY-MM.json` |
| `check_urls.py` | Check logo URLs for HTTP 200 |
| `add-github-links.py` | Fill `[links] github` from the mapping file |
| `update_logos.py` | Fill empty `logo` fields |
| `link-maintainers-projects.py` | Create bidirectional maintainer ↔ project links |
| `localize-images.py` | Download remote avatars and logos into `static/images/` |

> `generate_projects.py` was removed: it had a syntax error, 51/85 stale slugs, and its output-writing logic was dead code.

## fetch-github-metrics.py

```bash
# Print a health report
python scripts/fetch-github-metrics.py --repo curl/curl

# Save a JSON report
python scripts/fetch-github-metrics.py --repo curl/curl --output curl-metrics.json

# Update Hugo project front matter
python scripts/fetch-github-metrics.py --repo curl/curl --frontmatter content/projects/curl.md

# Compute without writing
python scripts/fetch-github-metrics.py --repo curl/curl --frontmatter content/projects/curl.md --dry-run
```

CLI options: `--repo owner/repo`, `--output/-o`, `--frontmatter/-f`, `--dry-run`.

### Data integrity and API handling

- **Retries**: 5xx and 429 responses, plus 403 responses carrying `Retry-After` / `X-RateLimit-Remaining: 0` / rate-limit messages, are retried up to 4 times with exponential backoff (capped at 60 seconds), honouring `Retry-After` first.
- **Request budget**: the total contributor count comes from a single `per_page=1` request reading the `Link rel="last"` page number; commits are sampled from the newest 2 pages (200 commits) for author counts and bus factor.
- **Exact-count fallback**: if the commit sample does not reach the 90-day boundary, two more `per_page=1` requests (`since=<30d>` and `since=<90d>&until=<30d>`) produce exact 30/90-day commit counts; when the sample already covers the boundary no extra requests are made.
- **Never write failures**: any required endpoint failing raises an error and skips writing that project — a failure is never persisted as 0.
- **Very large repositories**: when GitHub returns 403 "contributor list is too large", contributors are marked unavailable and the existing front matter value is preserved (not zeroed, not treated as a failure).
- **Front matter rewriting**: the existing front matter is parsed with `tomllib` first; only the top-level `[health]` and `[metrics]` tables are replaced and every other byte is preserved. The result is validated with `tomllib` again before writing; invalid output is refused.

### Example output

```
============================================================
📋 Health Report: curl/curl
============================================================

📊 Basic Metrics:
  ⭐ Stars: 35,000
  🍴 Forks: 6,000
  🐛 Open Issues: 400
  👥 Total Contributors: 250

📈 Activity:
  📝 Commits (30d): 45
  📝 Commits (90d): 120
  👤 Active Contributors (90d): 8

🏥 Health Assessment:
  Overall Score: 78/100
  Funding: at-risk
  Maintenance: active
  Contributors: healthy
  Bus Factor: medium
============================================================
```

### Health scoring (Methodology v1.0)

```
Health Score = (Funding × 0.25) + (Maintenance × 0.30)
             + (Contributors × 0.25) + (Bus Factor × 0.20)
```

| Dimension | Scoring basis |
|-----------|---------------|
| maintenance | Time since the last commit (40) + latest release (30) + commits in the last 30 days (30) |
| contributors | Active contributors in the last 90 days × 8 (capped at 80) + 20 more when there are 10+ |
| bus_factor | People needed to cover 50% of recent commits: ≥5 → 100; 3–4 → 70; 2 → 40; 1 → 15 |
| funding | See the heuristic below |

Dimension status thresholds: maintenance ≥70 active / ≥40 moderate / otherwise inactive; contributors ≥70 healthy / ≥40 declining / otherwise critical; bus_factor ≥70 low / ≥40 medium / otherwise high.

### Funding heuristic (computed automatically)

The script reads `.github/FUNDING.yml` and repository topics, then adds funding-source points on top of a popularity-based base score:

- **Base score**: stars ≥ 10000 or contributors ≥ 100 → 70; stars ≥ 1000 or contributors ≥ 20 → 50; otherwise 25.
- **Bonuses**: FUNDING.yml present +10; number of sources ×5 (capped at 15); per-platform points (github_sponsors 10, open_collective 8, tidelift 8, patreon 5, ko-fi 3, liberapay 3, custom 2).
- **Status**: final score ≥80 stable; ≥50 at-risk; otherwise critical.

> The funding score remains an automatic estimate and should be reviewed manually — but it is not "impossible to obtain automatically".

## batch-update-health.py

```bash
python scripts/batch-update-health.py                 # all projects
python scripts/batch-update-health.py --limit 10      # first 10 only (debugging)
python scripts/batch-update-health.py --filter rust   # only name matches
python scripts/batch-update-health.py --dry-run --limit 5
```

- Reads each repository from the project's `[links] github` front matter; projects without a link are skipped.
- A failing project is skipped and recorded, and the failure list is summarised at the end.
- **Systemic failure**: when more than half of the projects fail, the script exits non-zero so CI alerts; `--dry-run` neither writes nor exits non-zero.
- Reads `GITHUB_TOKEN` from the environment only.

## update-historical-data.py

```bash
python scripts/update-historical-data.py
```

Reads every project's health data, writes a monthly snapshot to `data/historical/YYYY-MM.json`, and updates `summary.json` for the site's trend charts.

## check_urls.py

```bash
python scripts/check_urls.py
```

Requests each slug → URL entry in `scripts/logo_urls.json` and checks for HTTP 200. Uses a browser User-Agent to avoid false 403s from CDNs that block the default one. Requires `requests`.

## add-github-links.py

```bash
python scripts/add-github-links.py
```

Fills the `[links] github` field from `scripts/project-github-mapping.json` for projects that lack it; skips files whose front matter already contains `[links]`. All paths resolve relative to the repository root.

## update_logos.py

```bash
python scripts/update_logos.py
```

Fills project `logo` fields from `scripts/logo_urls.json`. Only empty `logo = ''` values are filled; existing logos are never overwritten.

## link-maintainers-projects.py

```bash
python scripts/link-maintainers-projects.py            # dry run (default)
python scripts/link-maintainers-projects.py --apply    # write changes
python scripts/link-maintainers-projects.py --clean    # report unmatchable projects only (no deletions)
```

Creates bidirectional links between maintainer profiles and the top-level `maintainers` field of projects. Preview by default; `--apply` writes.

## localize-images.py

```bash
python scripts/localize-images.py                 # dry run (report only)
python scripts/localize-images.py --apply         # download and rewrite front matter
python scripts/localize-images.py --apply --only avatars
python scripts/localize-images.py --apply --only logos
```

Localizes remote images to remove third-party requests and pre-size them for display:

- maintainer avatars (`links.github`, except those with `avatar_style = "initials"`) are downloaded to
  `static/images/maintainers/<slug>.webp` (240 px);
- existing local avatars are re-encoded to the same specification;
- project `logo` URLs are saved as `static/images/logos/<slug>.svg` (vector, kept verbatim)
  or `<slug>.webp` (raster, resized to 192 px);
- when a download fails the original remote URL is kept, so no data is broken.

Requires `Pillow` (see `requirements.txt`).

## Workflow integration

`.github/workflows/update-metrics.yml` runs every Sunday at 00:00 UTC (manual dispatch supports the `dry_run` and `limit` inputs) on Python 3.11:

1. runs `python scripts/batch-update-health.py --limit N` with `GITHUB_TOKEN`;
2. runs `python scripts/update-historical-data.py`;
3. commits changes under `content/projects/` and `data/historical/`.

For a manual run with `dry_run=true`, only `batch-update-health.py --dry-run --limit N` executes and nothing is committed.

## Notes

1. **GitHub API limits**: 60 requests/hour unauthenticated; set `GITHUB_TOKEN`.
2. **Data integrity**: scripts never write on API failure, so failures cannot be recorded as 0; contributor counts for very large repositories keep their previous value.
3. **Recommendation**: run the scripts regularly (the workflow already runs weekly) to track health changes.
