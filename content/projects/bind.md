+++
dependencies = ["OpenSSL", "Linux Kernel"]
date = '2025-06-08T15:30:11+08:00'
title = 'BIND'
logo = 'https://www.isc.org/images/bind9.png'
description = 'Most widely used DNS server software'

[health]
  funding = "at-risk"
  maintenance = "inactive"
  contributors = "critical"
  bus_factor = "medium"
  score = 23
[links]
  github = "isc-projects/bind9"
[metrics]
  updated_at = "2026-02-15"
  stars = 728
  forks = 170
  contributors = 53
  commits_30d = 0
  commits_90d = 0
  bus_factor_people = 2
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

BIND is maintained by ISC with limited funding. This critical internet infrastructure relies on grants and donations.
