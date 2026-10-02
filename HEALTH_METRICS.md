# Project Health Metrics

This document describes the health assessment criteria and metric definitions used by the "Infrastructure Heroes" website.

## Purpose

To help identify infrastructure projects that need community support and attention, improving the stability of the software supply chain.

---

## Health metrics

### Overall score

Range: 0-100

| Score range | Status | Meaning |
|-------------|--------|---------|
| 80-100 | 🟢 Healthy | The project is in good shape |
| 60-79 | 🟡 Warning | The project has potential risks |
| 0-59 | 🔴 Critical | The project urgently needs support |

---

### The four core dimensions

#### 1. 💰 Funding

| Value | Meaning | Description |
|-------|---------|-------------|
| `stable` | Stable | The project has sustainable funding (corporate sponsorship, foundation support, etc.) |
| `at-risk` | At risk | Funding is unstable or expiring |
| `critical` | Critical | The project urgently needs funding |

#### 2. 🔧 Maintenance

| Value | Meaning | Description |
|-------|---------|-------------|
| `active` | Active | Regular releases; bugs and security issues fixed promptly |
| `moderate` | Moderate | Occasional updates, slower responses |
| `inactive` | Inactive | No maintenance activity for a long time |

#### 3. 👥 Contributors

| Value | Meaning | Description |
|-------|---------|-------------|
| `healthy` | Healthy | An active and diverse contributor community |
| `declining` | Declining | The number of contributors is shrinking |
| `critical` | Critical | Very few active contributors |

#### 4. 🚌 Bus Factor (key-person risk)

How much a project would suffer if its core maintainer suddenly became unavailable.

| Value | Meaning | Description |
|-------|---------|-------------|
| `low` | Low risk | Knowledge is spread across several people |
| `medium` | Medium risk | Some degree of single-person dependency |
| `high` | High risk | Heavy reliance on 1-2 key people |

---

## Usage

### Adding health data to a project

Add a `health` section to the front matter of the project Markdown file:

```markdown
+++
title = 'My Project'
logo = 'https://example.com/logo.png'

[health]
  funding = "stable"      # stable | at-risk | critical
  maintenance = "active"  # active | moderate | inactive
  contributors = "healthy" # healthy | declining | critical
  bus_factor = "low"      # low | medium | high
  score = 85              # overall score, 0-100
+++
```

### Where it appears

- **Project list page**: each project card shows a health score bar and overall score
- **Project detail page**: a full health dashboard with per-dimension explanations

---

## Assessment guidelines

1. **Update regularly**: refresh health data every quarter
2. **Data sources**:
   - Contributor statistics from GitHub/GitLab APIs
   - Public project funding information
   - Maintainer interviews
3. **Community participation**: invite maintainers to self-assess
4. **Transparency**: explain the basis for assessments and stay objective

---

## How to help critical projects

When you find a project with a low score, the community can:

- **Contribute code**: submit PRs and fix bugs
- **Contribute documentation**: improve docs and lower the barrier to entry
- **Donate**: support through Open Collective, GitHub Sponsors, etc.
- **Spread the word**: raise awareness and attract new contributors
- **Corporate sponsorship**: encourage companies to fund the critical projects they depend on
