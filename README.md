# Infrastructure Heroes

A website dedicated to celebrating, documenting, and tracking the health of critical open-source infrastructure projects that power modern software.

**Live Site:** [https://infrastructure-heroes.org/](https://infrastructure-heroes.org/)

## About

Infrastructure Heroes helps the community identify and support critical infrastructure projects that power modern software, particularly those at risk or underfunded. We track project health across four dimensions:

- **Funding** - Evidence gaps and attributed public statements
- **Maintenance** - Development activity and release frequency
- **Contributors** - Authors observed in a recent commit sample
- **Commit concentration** - Distribution of sampled commits across authors

## Getting Started

### Prerequisites

- [Hugo](https://gohugo.io/installation/) (Extended version recommended)
- Git

### Local Development

1. Clone the repository with submodules:
   ```bash
   git clone --recurse-submodules https://github.com/zouyonghao/infrastructure-heroes.git
   cd infrastructure-heroes
   ```

2. If you already cloned without submodules, initialize them:
   ```bash
   git submodule update --init --recursive
   ```

3. Start the Hugo development server:
   ```bash
   hugo server -D
   ```

4. Open [http://localhost:1313](http://localhost:1313) in your browser.

## Project Structure

```
infrastructure-heroes/
├── config.toml              # Hugo configuration
├── content/
│   ├── _index.md            # Homepage
│   ├── about.md             # About page
│   ├── thanks.md            # Thank wall
│   ├── dependencies.md      # Dependency chains visualization
│   ├── projects/            # Project profiles
│   └── maintainers/         # Maintainer profiles
├── data/
│   ├── dependencies.yaml    # Dependency graph data
│   └── historical/          # Historical health snapshots
├── layouts/
│   ├── projects/            # Project templates
│   ├── partials/            # Reusable components
│   └── shortcodes/          # Custom shortcodes
├── static/css/              # Stylesheets
├── static/js/               # JavaScript
├── scripts/                 # Automation utilities
└── themes/ananke/           # Base theme (submodule)
```

## Adding a New Project

1. Create a new file in `content/projects/`:
   ```bash
   hugo new projects/project-name.md
   ```

2. Edit the file with the project details:
   ```toml
   +++
   title = 'Project Name'
   logo = 'https://example.com/logo.svg'
   description = 'Brief description of the project'

   [health]
     funding = "unknown"       # Requires separately reviewed financial evidence
     maintenance = "active"    # active | moderate | inactive
     contributors = "healthy"  # healthy | declining | critical
     bus_factor = "low"        # low | medium | high
     methodology_version = "2.0"
     assessment = "automated"
   +++

   ### Overview
   Project overview content here...
   ```

3. Use the GitHub metrics script to auto-populate some data:
   ```bash
   python scripts/fetch-github-metrics.py --repo owner/repo --frontmatter content/projects/project-name.md
   ```

## Adding a Maintainer Profile

1. Create a new file in `content/maintainers/`:
   ```bash
   hugo new maintainers/maintainer-name.md
   ```

2. Edit with maintainer details:
   ```toml
   +++
   title = "Maintainer Name"
   role = "Project Lead"
   projects = ["Project Name"]
   status = "active"  # active | stepped-back | retired
   
   # Optional: explicit avatar and photo credit (e.g. Wikimedia Commons)
   # avatar = "/images/maintainers/maintainer-name.jpg"
   # avatar_credit = "Jane Doe, CC BY-SA 4.0"
   # avatar_credit_url = "https://commons.wikimedia.org/wiki/File:Example.jpg"
   # avatar_style = "initials"  # skip the GitHub avatar, use branded initials
   
   [links]
     github = "username"
     twitter = "username"
     website = "https://example.com"
     # Optional: where people can support this maintainer
     # sponsors = "https://github.com/sponsors/username"
   
   # Optional: Track maintainer succession
   # [successor]
   #   name = "New Maintainer"
   #   relation = "succeeded"
   #   date = "2024-01-01"
   #   reason = "Stepped back to focus on..."
   +++

   Bio and details about the maintainer...
   ```

## Activity indicators and evidence

The site publishes repository activity indicators, evidence limitations, and sourced support actions. Funding remains unknown and no composite health rating is published. Earlier v1.0 scores are archived estimates.

See [the methodology and editorial criteria](content/methodology.md) for the exact collection rules, source requirements, and correction process. Checked support routes live in [data/project_support.json](data/project_support.json).

### Project Succession

When a project is deprecated, archived, or superseded, we track its successor to help users migrate:

```toml
[successor]
  project = "MariaDB"           # Name of successor project
  relation = "alternative"      # superseded | forked | merged | alternative
  reason = "More open governance"
```

Relation types:
- **superseded** - Original project archived, use successor instead
- **forked** - Community fork that became more active
- **merged** - Project incorporated into another
- **alternative** - Different approach, may be preferred for new deployments

This helps ensure infrastructure continuity by guiding users to actively maintained alternatives.

### Maintainer Succession

When a maintainer steps back, retires, or transfers responsibility, we track their successor:

```toml
[successor]
  name = "New Maintainer Name"
  relation = "succeeded"     # succeeded | co-maintainer | interim
  date = "2024-01-01"
  reason = "Stepped back to focus on other projects"
```

Relation types:
- **succeeded** - New maintainer took over primary responsibility
- **co-maintainer** - Responsibility shared with existing team member
- **interim** - Temporary maintenance while searching for permanent maintainer

Additionally, maintainers can have a `status` field:
- **active** - Currently maintaining projects
- **stepped-back** - Reduced involvement, advisory role
- **retired** - No longer involved in maintenance

This helps track the human continuity behind critical infrastructure.

## Scripts

Scripts require Python 3.11+ and the packages in [`requirements.txt`](requirements.txt):

```bash
pip install -r requirements.txt
```

See [`scripts/README.md`](scripts/README.md) for the full script reference.

### GitHub Metrics Fetcher

Automatically fetch project metrics from GitHub:

```bash
# Basic usage
python scripts/fetch-github-metrics.py --repo curl/curl

# Output to JSON
python scripts/fetch-github-metrics.py --repo curl/curl --output metrics.json

# Update Hugo frontmatter directly
python scripts/fetch-github-metrics.py --repo curl/curl --frontmatter content/projects/curl.md
```

Set `GITHUB_TOKEN` environment variable for higher API rate limits.

### Batch Update

Update all projects at once:

```bash
# Update all projects
python scripts/batch-update-health.py

# Dry run to preview changes
python scripts/batch-update-health.py --dry-run

# Limit to specific projects (for testing)
python scripts/batch-update-health.py --limit 5
```

### Historical Data Tracking

Record health trends over time:

```bash
# Create snapshot and update trends
python scripts/update-historical-data.py
```

Snapshots are stored in `data/historical/` for trend analysis.

## Contributing

Contributions are welcome! Here's how you can help:

1. **Add a project** - Know an important infrastructure project? Add it!
2. **Update health data** - Help keep project health assessments current
3. **Add maintainer profiles** - Highlight the people behind these projects
4. **Improve documentation** - Help make this project more accessible
5. **Fix bugs** - Found an issue? Submit a PR!

### Contribution Guidelines

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test locally with `hugo server`
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Deployment

The site is automatically deployed to GitHub Pages by [`.github/workflows/hugo.yml`](.github/workflows/hugo.yml) on every push to `master`, and after each successful run of the automated metrics update (commits pushed by `GITHUB_TOKEN` do not trigger the `push` event, so the metrics workflow completion is used as the deploy trigger).

Pull requests and topic branches are validated by [`.github/workflows/ci.yml`](.github/workflows/ci.yml) (Python unit tests plus a Hugo build) before merge.

## Automated Updates

Project metrics are automatically refreshed weekly via GitHub Actions:

- **Schedule**: Every Sunday at 00:00 UTC
- **Workflow**: `.github/workflows/update-metrics.yml`
- **Features**:
  - Fetches latest GitHub metrics for all projects
  - Refreshes activity indicators using Methodology v2.0
  - Records historical snapshots for trend analysis
  - Refreshes the Health Trends section of the Methodology page
  - Commits changes automatically and triggers a site deployment

### Manual Trigger

You can manually trigger an update from the Actions tab, with options for:
- **Dry run**: Preview changes without committing
- **Limit**: Update only first N projects

### Funding information

The metrics fetcher can detect donation platforms in `FUNDING.yml` and repository topics. These do not establish income or runway, so funding remains unknown. Public funding statements and participation routes are recorded separately with official sources and a checking date.

## Dependency Chain Visualization

Inspired by [xkcd #2347](https://xkcd.com/2347/), the site includes a **Dependencies** page that visualizes how modern software stacks depend on critical infrastructure:

- **Dependency Chains**: Explore curated relationships between applications and infrastructure libraries
- **Foundation Projects**: Identify load-bearing infrastructure with no dependencies but depended on by everything
- **Project Context**: Follow dependency links to activity evidence and support options

Edit `data/dependencies.yaml` to add new dependency relationships.

## License

Source code (scripts, templates, stylesheets, workflows, configuration) is licensed under the [MIT License](LICENSE). Website content (project profiles, maintainer profiles, and documentation under `content/`) is licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). See [LICENSE](LICENSE) for details.

## Acknowledgments

- Built with [Hugo](https://gohugo.io/)
- Theme based on [Ananke](https://github.com/theNewDynamic/gohugo-theme-ananke)
- Inspired by the [Roads and Bridges](https://www.fordfoundation.org/work/learning/research-reports/roads-and-bridges-the-unseen-labor-behind-our-digital-infrastructure/) report
