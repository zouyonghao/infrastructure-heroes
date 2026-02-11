+++
date = '{{ .Date }}'
draft = true
title = '{{ replace .Name "-" " " | title }}'
logo = ''
description = ''
maintainers = []

[health]
  funding = "unknown"      # stable | at-risk | critical | unknown
  maintenance = "unknown"  # active | moderate | inactive | unknown
  contributors = "unknown" # healthy | declining | critical | unknown
  bus_factor = "unknown"   # low | medium | high | unknown
  score = 0               # 0-100 health score

# Optional: Track project succession for continuity
# [successor]
#   project = "New Project Name"  # Name of successor project
#   relation = "superseded"       # superseded | forked | merged | alternative
#   reason = "Project archived, use X instead"
+++

### Overview

Brief description of what this project does and its importance to the infrastructure ecosystem.

### Importance

- Key point about why this project matters
- Another important aspect
- Impact on the broader ecosystem

### Key Features

- Feature 1
- Feature 2
- Feature 3

### Health Assessment

Summary of the project's current health status and any concerns.

### How to Help

- Ways to contribute
- Funding/sponsorship information
- Links to project resources
