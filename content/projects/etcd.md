+++
dependencies = ["OpenSSL", "Go", "Linux Kernel"]
date = '2025-06-08T15:30:11+08:00'
title = 'etcd'
logo = 'https://avatars.githubusercontent.com/u/41972792?s=48&v=4'
description = 'Distributed key-value store'

[health]
  funding = "at-risk"
  maintenance = "active"
  contributors = "healthy"
  bus_factor = "medium"
  score = 80
[links]
  github = "etcd-io/etcd"
[metrics]
  updated_at = "2026-02-15"
  stars = 51511
  forks = 10319
  contributors = 100
  commits_30d = 100
  commits_90d = 100
  bus_factor_people = 2

+++

### Overview

etcd is a distributed, reliable key-value store for the most critical data of a distributed system. It is used for configuration management and service discovery.

### Importance

- Foundation of Kubernetes
- Powers service discovery
- Critical for distributed systems
- Used by CoreDNS, Rook, and more

### Key Features

- Strong consistency (Raft)
- Watch API for changes
- TTL for keys
- Distributed locking

### Sustainability

etcd is a CNCF graduated project with strong community support. It has solid governance and corporate backing.
