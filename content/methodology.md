+++
title = "Methodology and Editorial Criteria"
description = "What our activity indicators measure, what remains unknown, and how we review sources"
+++

## What the site can tell you

Infrastructure Heroes uses **Healthy (80–100), Warning (60–79), and Critical (0–59)** to summarize automated repository activity estimates. Use these categories to decide what to investigate. They do not establish financial sustainability, security, or maintainer capacity. Mature projects can need few changes.

This is methodology **v2.1**, introduced on October 2, 2026. Funding remains unknown and is excluded from the score. Support-link checks are separate from health status.

## Score and categories

The score combines the maintenance, contributor, and commit-concentration points described below:

`score = round((maintenance × 30 + contributors × 25 + concentration × 20) / 75)`

When no recent author evidence is available, concentration is unknown and omitted; the remaining weights are normalized by dividing by 55. Missing required activity data leaves the project **Unrated**, rather than treating it as critical. An observed absence of recent commits can still produce a low activity score.

| Score | Status |
|---|---|
| 80–100 | Healthy |
| 60–79 | Warning |
| 0–59 | Critical |
| Insufficient activity data | Unrated |

These thresholds preserve the familiar navigation categories. Scores from different methodology versions are not directly comparable. Historical charts show a single scoring version at a time.

## Funding

Funding is **unknown** unless financial evidence has been reviewed separately. A donation button shows a way to give; it does not show income, expenses, paid maintenance time, or runway. Popularity and corporate affiliation are not funding measurements.

The automation may detect donation platforms in a repository's `FUNDING.yml` or topics. It does not assign funding points or a funding status from those signals. Official funding statements can be described with attribution in a project's support section; they are not independently audited financial ratings.

## Automated activity indicators

The weekly GitHub job reads public repository metadata, recent commits, contributor counts, and GitHub releases. The collection date and repository link appear on each project page. An update to these metrics is not an editorial review of the profile.

### Maintenance

The maintenance indicator adds three components, up to 100 internal points:

| Component | Observations → points |
|---|---|
| Days since repository push | <7 → 40; <30 → 35; <60 → 25; <90 → 15; <180 → 10; otherwise → 5 |
| Days since latest GitHub release | <30 → 30; <90 → 25; <180 → 15; <365 → 10; otherwise → 5 |
| Commits in 30 days | ≥50 → 30; ≥20 → 25; ≥10 → 20; ≥5 → 15; ≥1 → 10; none → 0 |

Totals of 70 or more display as **active**, 40–69 as **moderate**, and below 40 as **inactive**. These labels describe the automation's activity estimate. Missing release or push dates use the oldest recency bucket. Releases outside GitHub may be missed, and push time is not necessarily the time of a code change. Mature software may need few changes.

### Contributors

We sample up to the newest 200 commits and count distinct author identities observed within 90 days. The internal indicator is eight points per observed author, capped at 80, plus 20 points at ten or more authors. It is displayed as **many observed** (70+ points), **some observed** (40–69), or **few observed** (below 40).

This does not measure growth, decline, company diversity, review work, or community health. Author identities can include bots or duplicate names. The separate all-time contributor count is not an active-maintainer count.

### Commit concentration

We count how many authors account for half the sampled commits within 90 days. One author displays as **high** concentration, two as **moderate**, and three or more as **lower**. No recent author evidence means **unknown**.

The field is historically named `bus_factor`, but it is only a commit-concentration proxy. It does not establish how many people understand the software, hold release credentials, or can maintain it. A higher actual bus factor means more people can sustain a project and generally lower key-person risk.

### Sampling and missing data

If 200 commits do not reach the 90-day boundary, additional count queries obtain the window's commit totals. Author counts and concentration still describe only the sample. The sample-coverage flag is stored with new collections; older records without it explicitly show that coverage is unverified.

A required API failure prevents updating the affected project. If GitHub cannot provide the all-time contributor count for a large repository, the previous value is retained and flagged as unavailable. A GitHub mirror may omit development happening elsewhere. Funding and missing author evidence are never replaced by a zero health score.

## Support information

Checked support entries contain a specific action, its destination, official source links, and the date those pages were checked. Checking a public page does not mean a maintainer confirmed an urgent need. We do not infer urgent requests from activity indicators.

For projects without checked entries, the site says so and links to their repository guidance. Contributors can suggest an official funding page, contribution guide, or a dated public request in an issue or pull request. Confirm the intended recipient of donations and respect each project's contribution and security-reporting instructions.

## Editorial scope

We focus on reusable software infrastructure: libraries, runtimes, operating-system components, protocols, build tools, deployment tools, and services that other software depends on. A project's inclusion should explain that dependency role.

People profiles should document a concrete role in creating, maintaining, or contributing to that infrastructure. Being a technology celebrity, company founder, author, or educator alone is not enough. Profiles without a documented infrastructure connection are held as drafts for review.

A creator, current maintainer, former maintainer, and contributor are different roles. Use the specific role supported by project documentation; do not treat a project's linked profiles as its complete current team. Existing profiles remain subject to source review. New or revised claims about current roles need a primary source and review date. Quotations require a traceable source.

## Corrections and review

Each project page links to an assessment-correction issue. Please include the claim, proposed correction, primary source, and the date the evidence applies to. Project maintainers are welcome to clarify roles and support needs; being listed does not imply endorsement.

There is no claim that all profiles receive quarterly human review. Automated collection and editorial source checking are separate processes. Financial ratings will require a documented evidence standard before they return.

## Historical estimates

Methodology v1.0 combined funding, maintenance, contributor, and commit-concentration estimates with weights of 25%, 30%, 25%, and 20%. Its funding heuristic used popularity and donation-link detection. Those scores remain archived for transparency. Version 2.0 temporarily withheld composite scores; version 2.1 restores the familiar categories using activity estimates and excluding unknown funding.

{{< health-trends >}}



## 📈 Health Trends

_Last collection: 2026-10-02_

Projects collected: 108. Projects without an overall rating: 0.

36 snapshots recorded from 2026-02-08 to 2026-10-02.

Charts use methodology v2.1. Earlier scoring versions remain archived and are not mixed into the current trend.

