# Infrastructure Heroes - Agent Guide

This document provides essential information for AI coding agents working on the Infrastructure Heroes project.

## Project Overview

**Infrastructure Heroes** is a static website built with [Hugo](https://gohugo.io/) that tracks and celebrates critical open-source infrastructure projects. It monitors project health across four dimensions: funding, maintenance, contributors, and bus factor risk.

- **Live Site**: https://infrastructure-heroes.org/
- **Repository**: https://github.com/zouyonghao/infrastructure-heroes
- **Primary Language**: English (content), Chinese (some documentation)

## Technology Stack

| Component | Technology |
|-----------|------------|
| Static Site Generator | Hugo (Extended version recommended) |
| Base Theme | Ananke (Git submodule) |
| Templating | Go HTML Templates |
| Styling | Custom CSS (`static/css/custom.css`) |
| Data Processing | Python 3 (standard library only) |
| Deployment | GitHub Pages via GitHub Actions |
| Content Format | Markdown with TOML frontmatter |

## Project Structure

```
infrastructure-heroes/
├── config.toml              # Hugo site configuration
├── content/                 # Website content (Markdown)
│   ├── _index.md           # Homepage
│   ├── about.md            # About page
│   ├── thanks.md           # Thank wall page
│   ├── categories.md       # Projects grouped by primary purpose
│   ├── methodology.md      # Health scoring methodology
│   ├── projects/           # Project profiles (*.md)
│   └── maintainers/        # Maintainer profiles (*.md)
├── data/                    # Data files
│   ├── dependencies.yaml   # Dependency graph data (no category tiers)
│   ├── project_categories.json # Category names and scope descriptions
│   └── historical/         # Health score snapshots (JSON)
├── layouts/                 # Hugo templates
│   ├── _default/           # Base templates
│   ├── projects/           # Project page templates
│   ├── maintainers/        # Maintainer page templates
│   ├── partials/           # Reusable components
│   └── shortcodes/         # Custom Hugo shortcodes
├── static/                  # Static assets
│   ├── css/custom.css      # Custom styles (large file ~140KB)
│   ├── js/trends.js        # JavaScript for trends visualization
│   └── favicon.svg         # Site favicon
├── scripts/                 # Python automation utilities
│   ├── fetch-github-metrics.py      # GitHub API data fetcher
│   ├── batch-update-health.py       # Batch update all projects
│   ├── update-historical-data.py    # Historical data tracking
│   ├── check_urls.py                # URL validation
│   └── project-github-mapping.json  # Project-to-repo mappings
├── archetypes/              # Content templates for `hugo new`
│   ├── default.md
│   ├── projects.md
│   └── maintainers.md
└── themes/ananke/           # Base theme (Git submodule)
```

## Build and Development Commands

### Prerequisites
- Hugo Extended (latest version recommended)
- Git with submodule support
- Python 3.11+ (for scripts)

### Local Development
```bash
# Clone with submodules
git clone --recurse-submodules https://github.com/zouyonghao/infrastructure-heroes.git

# Or initialize submodules after clone
git submodule update --init --recursive

# Start development server
hugo server -D

# Open http://localhost:1313
```

### Build for Production
```bash
# Build site (output to ./public)
hugo --minify

# Build with specific base URL
hugo --minify --baseURL "https://example.com/"
```

## Content Management

### Adding a New Project
```bash
# Create project from archetype
hugo new projects/project-name.md
```

Project frontmatter structure:
```toml
+++
title = 'Project Name'
logo = 'https://example.com/logo.svg'
description = 'Brief description'
date = '2025-01-01T00:00:00+08:00'
maintainers = ["Maintainer Name"]  # Links to maintainer profiles
category = "networking"   # Key from data/project_categories.json

[health]
  funding = "stable"        # stable | at-risk | critical | unknown
  maintenance = "active"    # active | moderate | inactive | unknown
  contributors = "healthy"  # healthy | declining | critical | unknown
  bus_factor = "low"        # low | medium | high | unknown
  score = 85               # 0-100 calculated score

[links]
  github = "owner/repo"

[metrics]
  updated_at = "2025-01-01"
  stars = 10000
  forks = 1000
  contributors = 50
  commits_30d = 20
  commits_90d = 60
  bus_factor_people = 3

# Optional: Track project succession
# [successor]
#   project = "New Project"     # Name of successor/alternative
#   relation = "alternative"    # superseded | forked | merged | alternative
#   reason = "Why migrate..."
+++
```

### Adding a Maintainer
```bash
hugo new maintainers/maintainer-name.md
```

Maintainer frontmatter structure:
```toml
+++
title = "Maintainer Name"
role = "Project Lead"
projects = ["Project Name"]
status = 'active'  # active | stepped-back | retired | deceased
[links]
  github = 'username'
  twitter = 'username'
  website = 'https://example.com'

# Optional: Track maintainer succession
# [successor]
#   name = "New Maintainer"
#   relation = "succeeded"  # succeeded | co-maintainer | interim
#   date = "2024-01-01"
#   reason = "Stepped back to focus on..."
+++
```

### Updating Metrics via Scripts
```bash
# Single project update
python scripts/fetch-github-metrics.py --repo owner/repo --frontmatter content/projects/project.md

# Batch update all projects (requires GITHUB_TOKEN)
python scripts/batch-update-health.py

# Dry run to preview changes
python scripts/batch-update-health.py --dry-run --limit 5

# Update historical snapshots
python scripts/update-historical-data.py
```

## Health Score Methodology

Projects are scored on a 0-100 scale based on four weighted dimensions:

```
Health Score = (Funding × 0.25) + (Maintenance × 0.30) + (Contributors × 0.25) + (Bus Factor × 0.20)
```

| Dimension | Values | Description |
|-----------|--------|-------------|
| **Funding** | stable / at-risk / critical | Financial sustainability |
| **Maintenance** | active / moderate / inactive | Development activity |
| **Contributors** | healthy / declining / critical | Community health |
| **Bus Factor** | low / medium / high | Key person dependency risk |

| Score Range | Status | Color |
|-------------|--------|-------|
| 80-100 | 🟢 Healthy | Green |
| 60-79 | 🟡 Warning | Yellow |
| 0-59 | 🔴 Critical | Red |

See `HEALTH_METRICS.md` (in Chinese) for detailed methodology.

## Code Style Guidelines

### Markdown Content
- Use TOML frontmatter format (`+++` delimiters)
- Include date in ISO 8601 format with timezone
- Always fill in `[health]` section for projects
- Include `[links]` section with GitHub repo when applicable
- Use `[metrics]` section for automated data

### Python Scripts
- Use Python 3 standard library only (no external dependencies)
- Include docstrings with usage examples
- Support `GITHUB_TOKEN` environment variable for API authentication
- Handle API rate limits gracefully
- Print progress messages in Chinese (matching existing style)

### Hugo Templates
- Use semantic HTML5 elements
- Follow Go template syntax conventions
- Use partials for reusable components
- Shortcodes for content embedding

### CSS
- Custom styles in `static/css/custom.css`
- Uses CSS custom properties (variables) for theming
- Mobile-first responsive design

## Testing

### Manual Testing
```bash
# Verify Hugo build
hugo --minify

# Check for broken links (requires running site)
python scripts/check_urls.py
```

### URL Checking
```bash
# Validate all URLs in the built site
python scripts/check_urls.py
```

## Deployment

The site deploys automatically via GitHub Actions:

1. **Trigger**: Push to `master` branch
2. **Workflow**: `.github/workflows/hugo.yml`
3. **Process**:
   - Checkout with submodules
   - Setup Hugo Extended
   - Build with minification
   - Deploy to GitHub Pages

## Automated Updates

**Weekly Metrics Update** (`.github/workflows/update-metrics.yml`):
- Schedule: Every Sunday at 00:00 UTC
- Fetches GitHub metrics for all projects
- Recalculates health scores
- Records historical snapshots
- Commits changes automatically

**Manual trigger options**:
- `dry_run`: Preview changes without committing
- `limit`: Update only first N projects

## Security Considerations

1. **GitHub Token**: Store `GITHUB_TOKEN` as repository secret for API access
2. **API Rate Limits**: 
   - Unauthenticated: 60 requests/hour
   - Authenticated: 5,000 requests/hour
3. **Unsafe HTML**: Hugo config enables `unsafe = true` for markup.goldmark.renderer
4. **Dependencies**: Theme is loaded from external Git submodule

## Git Submodules

The project uses one submodule:
```
themes/ananke -> https://github.com/theNewDynamic/gohugo-theme-ananke.git
```

**Operations**:
```bash
# Initialize
git submodule update --init --recursive

# Update to latest
git submodule update --remote
```

## Key Files Reference

| File | Purpose |
|------|---------|
| `config.toml` | Hugo configuration, menu structure, site params |
| `data/dependencies.yaml` | Dependency graph between projects |
| `data/historical/*.json` | Historical health data snapshots |
| `scripts/project-github-mapping.json` | Maps project names to GitHub repos |
| `archetypes/*.md` | Templates for `hugo new` command |
| `layouts/shortcodes/*.html` | Reusable content components |

## Common Tasks

### Update a Project's Health Data
```bash
export GITHUB_TOKEN="ghp_xxx"
python scripts/fetch-github-metrics.py --repo owner/repo --frontmatter content/projects/name.md
```

### Add New Dependency Relationship
Edit `data/dependencies.yaml` and add:
```yaml
Project Name:
  depends_on: ["Dependency1", "Dependency2"]
```

Choose the project's top-level `category` in `content/projects/*.md` separately, using a key from `data/project_categories.json`. Categories describe primary purpose, not dependency layers. The per-project dependency view reads the project's `dependencies` front matter; update that when changing a displayed relationship.

### Create Custom Shortcode
Add HTML file to `layouts/shortcodes/`, use in content:
```markdown
{{</* shortcode-name param="value" */>}}
```

## Contact & Resources

- **Live Site**: https://infrastructure-heroes.org/
- **README**: See `README.md` for detailed user documentation
- **Health Metrics**: See `HEALTH_METRICS.md` (Chinese) for scoring details
- **Scripts**: See `scripts/README.md` for automation details
