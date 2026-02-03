# Infrastructure Heroes

A website dedicated to celebrating, documenting, and tracking the health of critical open-source infrastructure projects that power modern software.

**Live Site:** [https://infrastructure-heroes.org/](https://infrastructure-heroes.org/)

## About

Infrastructure Heroes helps the community identify and support critical infrastructure projects that power modern software, particularly those at risk or underfunded. We track project health across four dimensions:

- **Funding** - Financial sustainability
- **Maintenance** - Development activity and release frequency
- **Contributors** - Community health and growth
- **Bus Factor** - Risk from key person dependency

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
│   ├── projects/            # Project profiles
│   └── maintainers/         # Maintainer profiles
├── layouts/
│   ├── projects/            # Project templates
│   ├── partials/            # Reusable components
│   └── shortcodes/          # Custom shortcodes
├── static/css/              # Stylesheets
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
     funding = "stable"        # stable | at-risk | critical
     maintenance = "active"    # active | moderate | inactive
     contributors = "healthy"  # healthy | declining | critical
     bus_factor = "low"        # low | medium | high
     score = 85               # 0-100
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
   project = "Project Name"
   avatar = "https://example.com/avatar.jpg"
   +++

   Bio and details about the maintainer...
   ```

## Health Score System

Projects are rated on a 0-100 scale based on four dimensions:

| Score Range | Status | Color |
|-------------|--------|-------|
| 70-100 | Healthy | Green |
| 40-69 | Warning | Yellow |
| 0-39 | Critical | Red |

See [HEALTH_METRICS.md](HEALTH_METRICS.md) for detailed methodology.

## Scripts

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

The site is automatically deployed to GitHub Pages on push to the `master` branch via GitHub Actions.

## License

This project is open source. See the repository for license details.

## Acknowledgments

- Built with [Hugo](https://gohugo.io/)
- Theme based on [Ananke](https://github.com/theNewDynamic/gohugo-theme-ananke)
- Inspired by the [Roads and Bridges](https://www.fordfoundation.org/work/learning/research-reports/roads-and-bridges-the-unseen-labor-behind-our-digital-infrastructure/) report
