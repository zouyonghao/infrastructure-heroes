---
title: "Health Score Methodology"
description: "How we calculate and evaluate the health of open source infrastructure projects"
---

## Overview

The Infrastructure Heroes health scoring system provides a standardized way to assess the sustainability and risk level of critical open source infrastructure projects. Our methodology combines quantitative metrics from GitHub with qualitative assessments to produce a comprehensive 0-100 health score.

## Scoring Formula

The overall health score is calculated using a weighted formula:

```
Health Score = (Funding × 0.25) + (Maintenance × 0.30) + (Contributors × 0.25) + (Bus Factor × 0.20)
```

Each dimension is scored on a 0-100 scale, then weighted and combined for the final score.

---

## The Four Dimensions

### 1. 💰 Funding (25% weight)

Financial sustainability ensures a project can continue development, security audits, and infrastructure costs.

| Status | Score | Criteria |
|--------|-------|----------|
| **Stable** | 90-100 | Multiple funding sources (corporate sponsors, foundations, donations) with 2+ year runway |
| **At-Risk** | 40-89 | Limited funding, single source, or < 2 year runway |
| **Critical** | 0-39 | No funding, unsustainable burn rate, or maintainer working unpaid |

**Indicators we track:**
- GitHub Sponsors status
- Open Collective funding
- Corporate backing
- Foundation support (Linux Foundation, Apache, etc.)
- Recent funding announcements

---

### 2. 🔧 Maintenance (30% weight)

Active maintenance ensures bugs are fixed, security vulnerabilities are patched, and the project keeps up with dependencies.

| Status | Score | Criteria |
|--------|-------|----------|
| **Active** | 90-100 | Commit within 30 days, regular releases, < 50 open issues per maintainer |
| **Moderate** | 40-89 | Commit within 90 days, releases within 6 months |
| **Inactive** | 0-39 | No commits for 90+ days, stale issues/PRs |

**Automated metrics:**
- Last commit date
- Release frequency (average days between releases)
- Issue response time
- PR merge rate
- Dependency update frequency

**Score calculation:**
```
Maintenance Score = (Recency × 0.4) + (Release Health × 0.3) + (Issue Velocity × 0.3)
```

---

### 3. 👥 Contributors (25% weight)

A diverse contributor base reduces risk and brings varied perspectives to the project.

| Status | Score | Criteria |
|--------|-------|----------|
| **Healthy** | 90-100 | 10+ active contributors, diverse companies, growing community |
| **Declining** | 40-89 | < 10 active contributors, or decreasing trend over 12 months |
| **Critical** | 0-39 | < 3 active contributors, or single-company dominated |

**Automated metrics:**
- Unique contributors (last 90 days)
- Contributor trend (6 month comparison)
- First-time contributors (last 90 days)
- Organizational diversity (companies represented)
- Core team size

**Score calculation:**
```
Contributors Score = min(100, (Active Contributors × 8) + (Diversity Bonus × 10))
```

---

### 4. 🚌 Bus Factor (20% weight)

Bus factor measures how many people would need to be unavailable before the project stalls. A high bus factor is a significant risk.

| Status | Score | Risk Level | Criteria |
|--------|-------|------------|----------|
| **Low** | 90-100 | Low | 5+ people with deep knowledge, documented processes |
| **Medium** | 40-89 | Medium | 2-4 people with critical knowledge |
| **High** | 0-39 | High | Single point of failure, tribal knowledge |

**Assessment criteria:**
- Number of core maintainers with merge rights
- Documentation completeness
- Onboarding process existence
- Code review coverage
- Domain expertise distribution

**Automated indicators:**
- Commit distribution (Gini coefficient of commits per author)
- Code review participants
- Documentation presence (README, CONTRIBUTING, etc.)

---

## Automated Data Collection

### GitHub API Metrics

Our `fetch-github-metrics.py` script collects:

```python
metrics = {
    "stars": repository stargazers count,
    "forks": repository forks count,
    "open_issues": open issues count,
    "open_prs": open pull requests count,
    "last_commit_date": date of most recent commit,
    "last_release_date": date of most recent release,
    "contributors_90d": unique contributors in last 90 days,
    "commit_frequency": commits per week (average),
    "issue_response_time_days": median days to first response,
    "pr_merge_rate": percentage of PRs merged vs closed,
    "bus_factor": number of contributors accounting for 50% of commits
}
```

### Score Auto-Calculation

For each project, we fetch the metrics and calculate:

```python
def calculate_maintenance_score(metrics):
    days_since_commit = (today - metrics['last_commit_date']).days
    recency_score = max(0, 100 - (days_since_commit * 1.5))
    
    if metrics['last_release_date']:
        days_since_release = (today - metrics['last_release_date']).days
        release_score = max(0, 100 - (days_since_release / 3))
    else:
        release_score = 0
    
    return (recency_score * 0.6) + (release_score * 0.4)

def calculate_contributor_score(metrics):
    base_score = min(100, metrics['contributors_90d'] * 8)
    trend_bonus = 10 if metrics['contributor_trend'] == 'growing' else 0
    return min(100, base_score + trend_bonus)

def calculate_bus_factor_score(metrics):
    if metrics['bus_factor'] >= 5:
        return 100
    elif metrics['bus_factor'] >= 3:
        return 70
    elif metrics['bus_factor'] >= 2:
        return 40
    else:
        return 15
```

---

## Manual Review Process

Automated scores are reviewed quarterly by maintainers for:

1. **Context accuracy** - Does the score reflect reality?
2. **Recent events** - Security incidents, funding changes, maintainer departures
3. **Qualitative factors** - Community health, governance quality, ecosystem importance

### Adjustment Guidelines

- **Maximum adjustment**: ±15 points from automated score
- **Documentation required**: All manual adjustments must include rationale
- **Review frequency**: Quarterly for scores < 60, annually for scores ≥ 60

---

## Score Categories

| Range | Status | Action Required |
|-------|--------|-----------------|
| 80-100 | 🟢 Healthy | Regular monitoring |
| 60-79 | 🟡 Warning | Quarterly review, support outreach |
| 0-59 | 🔴 Critical | Immediate attention, intervention planning |

---

## Limitations & Considerations

### What We Don't Capture

- **Code quality** - We measure activity, not code correctness
- **Security posture** - No automatic vulnerability scanning
- **User satisfaction** - No user surveys or NPS scores
- **Documentation quality** - Presence checked, not quality assessed

### Project Maturity

Mature, stable projects (like `zlib`) may have lower activity scores but are actually healthy. We manually adjust for:
- Feature-complete projects
- Maintenance-mode projects
- Spec/reference implementations

### GitHub Bias

Our metrics favor GitHub-hosted projects. For projects on GitLab, SourceHut, or self-hosted:
- We use available APIs where possible
- Manual assessment is weighted higher
- We encourage mirroring to GitHub for visibility

---

## Data Transparency

### Public Availability

All health score data is:
- ✅ Publicly visible on project pages
- ✅ Version controlled in this repository
- ✅ Available via API (planned)

### Privacy

We only collect:
- Public repository data
- Public contributor information
- Public funding information

No private data, emails, or non-public information is collected.

---

## Contributing to Assessments

### For Project Maintainers

If you maintain a project listed here:
1. Review your project's health data
2. Open a PR to update funding/contribution information
3. Contact us if automated metrics don't reflect reality

### For Community Members

Help improve our methodology:
- Suggest new metrics via GitHub issues
- Report inaccuracies
- Contribute to the assessment scripts

---

## Methodology Changelog

### v1.0 (Current)
- Initial four-dimension model
- GitHub API automation
- Quarterly review process

### Planned v1.1
- Security vulnerability tracking
- Dependency freshness metrics
- Community sentiment analysis

---

{{< health-trends >}}

---

## Questions?

If you have questions about our methodology or want to discuss a specific project's assessment:

- 🐛 [Open an issue on GitHub](https://github.com/zouyonghao/infrastructure-heroes/issues)
- 📧 Contact: See our [About page](/about/)

---

*Last updated: February 2026*



## 📈 Health Trends

_Last updated: 2026-02-08_

### Current Status

| Metric | Value |
|--------|-------|
| Total Projects | N/A |
| 🟢 Healthy (80-100) | 67 |
| 🟡 Warning (60-79) | 24 |
| 🔴 Critical (0-59) | 17 |
| Average Score | 78.5 |

### Historical Data Points

1 snapshots recorded from 2026-02-08 to 2026-02-08

