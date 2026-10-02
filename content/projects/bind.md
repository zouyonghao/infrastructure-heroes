+++
dependencies = ["OpenSSL", "Linux Kernel"]
date = '2025-06-08T15:30:11+08:00'
title = 'BIND'
logo = "/images/logos/bind.webp"
description = 'Most widely used DNS server software'

[health]
  score = 82
  funding = "unknown"
  maintenance = "active"
  contributors = "healthy"
  bus_factor = "low"
  methodology_version = "2.1"
  assessment = "automated"
[links]
  github = "isc-projects/bind9"
[metrics]
  updated_at = "2026-10-02"
  stars = 778
  forks = 186
  contributors = 60
  commits_30d = 304
  commits_90d = 1035
  bus_factor_people = 3
  contributors_90d = 13
  commits_sample_truncated = true
  contributors_unavailable = false
[successor]
  project = "CoreDNS"
  relation = "alternative"
  reason = "CoreDNS is a modern, cloud-native DNS server written in Go. It is the default DNS for Kubernetes and may be preferred for containerized environments."
+++

### Overview

BIND (Berkeley Internet Name Domain) is the most widely used DNS server software on the Internet. It provides a complete implementation of DNS protocols.

### Importance

- Powers most DNS infrastructure
- Foundation of Internet naming
- Critical for domain resolution
- Used by organizations worldwide

### Key Features

- Full DNS protocol support
- DNSSEC support
- Zone management
- Response rate limiting

### Sustainability

Financial sustainability and maintainer capacity have not yet been reviewed against current primary sources. See the evidence and support sections above for available information and a way to suggest corrections.
