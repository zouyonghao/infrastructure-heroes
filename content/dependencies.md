---
title: "Dependencies"
description: "Infrastructure dependency pyramid"
---

<div class="section-header">
  <h1 class="section-title">Infrastructure Dependencies</h1>
  <p class="section-subtitle">
    How critical infrastructure projects layer upon each other
  </p>
</div>

{{< dependency-pyramid >}}

<div class="dep-insight">
  <h3>💡 The Insight</h3>
  <p>
    Modern software stacks are like pyramids - <strong>wide at the top, narrow at the base</strong>.
    Hundreds of applications and frameworks depend on just a handful of foundation libraries.
  </p>
  <p>
    When a foundation project like <a href="/projects/zlib/">zlib</a> has a security issue,
    it affects <strong>15+ billion devices</strong>. Yet these critical projects often have
    just 1-3 maintainers.
  </p>
</div>

<div class="xkcd-quote">
  <p>"Every project eventually depends on a module maintained by someone in Nebraska who hasn't updated their website since 2003."</p>
  <cite>— <a href="https://xkcd.com/2347/">xkcd #2347</a></cite>
</div>

<div class="stack-explore">
  <a href="/projects/" class="btn btn-primary btn-large">Explore All Projects</a>
</div>
