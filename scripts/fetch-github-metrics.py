#!/usr/bin/env python3
"""
Infrastructure Heroes - GitHub Metrics Fetcher
自动从 GitHub API 获取项目指标，辅助评估项目健康度

Usage:
    python fetch-github-metrics.py --repo owner/repo [--output metrics.json]
    python fetch-github-metrics.py --config projects.yaml [--output-dir data/]
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import urllib.request
import urllib.error


class GitHubMetricsFetcher:
    """GitHub 项目指标获取器"""
    
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.environ.get('GITHUB_TOKEN')
        self.base_url = "https://api.github.com"
        
    def _api_request(self, endpoint: str) -> dict:
        """发送 GitHub API 请求"""
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Infrastructure-Heroes-Metrics"
        }
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        
        req = urllib.request.Request(url, headers=headers)
        
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                print(f"❌ Repository not found: {endpoint}")
            elif e.code == 403:
                print(f"❌ API rate limit exceeded. Consider using GITHUB_TOKEN.")
            else:
                print(f"❌ HTTP Error {e.code}: {e.reason}")
            return {}
        except Exception as e:
            print(f"❌ Error fetching {url}: {e}")
            return {}
    
    def fetch_repo_metrics(self, owner: str, repo: str) -> dict:
        """获取仓库基本指标"""
        print(f"📊 Fetching metrics for {owner}/{repo}...")
        
        # 基本信息
        repo_data = self._api_request(f"/repos/{owner}/{repo}")
        if not repo_data:
            return {}
        
        metrics = {
            "name": repo_data.get("name"),
            "full_name": repo_data.get("full_name"),
            "description": repo_data.get("description"),
            "url": repo_data.get("html_url"),
            "stars": repo_data.get("stargazers_count", 0),
            "forks": repo_data.get("forks_count", 0),
            "open_issues": repo_data.get("open_issues_count", 0),
            "created_at": repo_data.get("created_at"),
            "updated_at": repo_data.get("updated_at"),
            "pushed_at": repo_data.get("pushed_at"),
            "language": repo_data.get("language"),
            "license": repo_data.get("license", {}).get("spdx_id") if repo_data.get("license") else None,
            "archived": repo_data.get("archived", False),
            "disabled": repo_data.get("disabled", False),
        }
        
        # 获取最近提交活动
        commits = self._api_request(f"/repos/{owner}/{repo}/commits?per_page=100")
        metrics["recent_commits"] = len(commits)
        
        # 计算最近30天的提交数
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_commits = 0
        unique_authors = set()
        
        for commit in commits:
            if isinstance(commit, dict):
                commit_date = commit.get("commit", {}).get("committer", {}).get("date", "")
                if commit_date:
                    try:
                        commit_time = datetime.fromisoformat(commit_date.replace("Z", "+00:00"))
                        if commit_time > thirty_days_ago:
                            recent_commits += 1
                            author = commit.get("author", {}).get("login") if commit.get("author") else None
                            if author:
                                unique_authors.add(author)
                    except:
                        pass
        
        metrics["commits_last_30_days"] = recent_commits
        metrics["unique_contributors_last_30_days"] = len(unique_authors)
        
        # 获取贡献者统计 (需要 token 才能访问)
        contributors = self._api_request(f"/repos/{owner}/{repo}/contributors?per_page=100")
        metrics["total_contributors"] = len(contributors) if contributors else 0
        
        # 获取最近发布
        releases = self._api_request(f"/repos/{owner}/{repo}/releases?per_page=5")
        metrics["recent_releases"] = [
            {
                "tag": r.get("tag_name"),
                "published_at": r.get("published_at"),
                "prerelease": r.get("prerelease", False)
            }
            for r in (releases if releases else [])
        ]
        
        # 计算维护活跃度分数
        metrics["maintenance_score"] = self._calculate_maintenance_score(metrics)
        metrics["community_score"] = self._calculate_community_score(metrics)
        
        return metrics
    
    def _calculate_maintenance_score(self, metrics: dict) -> int:
        """计算维护活跃度分数 (0-100)"""
        score = 0
        
        # 最近30天提交数 (0-40分)
        commits = metrics.get("commits_last_30_days", 0)
        score += min(commits * 2, 40)
        
        # 最近发布时间 (0-30分)
        releases = metrics.get("recent_releases", [])
        if releases:
            try:
                last_release = datetime.fromisoformat(releases[0]["published_at"].replace("Z", "+00:00"))
                days_since_release = (datetime.now() - last_release.replace(tzinfo=None)).days
                if days_since_release < 30:
                    score += 30
                elif days_since_release < 90:
                    score += 20
                elif days_since_release < 180:
                    score += 10
            except:
                pass
        
        # Issues 处理情况 (0-30分)
        open_issues = metrics.get("open_issues", 0)
        if open_issues < 50:
            score += 30
        elif open_issues < 200:
            score += 20
        elif open_issues < 500:
            score += 10
        
        return min(score, 100)
    
    def _calculate_community_score(self, metrics: dict) -> int:
        """计算社区健康度分数 (0-100)"""
        score = 0
        
        # 总贡献者数 (0-40分)
        contributors = metrics.get("total_contributors", 0)
        score += min(contributors, 40)
        
        # 最近30天活跃贡献者 (0-40分)
        recent = metrics.get("unique_contributors_last_30_days", 0)
        score += min(recent * 8, 40)
        
        # Stars 受欢迎程度 (0-20分)
        stars = metrics.get("stars", 0)
        score += min(stars // 1000, 20)
        
        return min(score, 100)
    
    def assess_health(self, metrics: dict) -> dict:
        """基于指标评估项目健康度"""
        if not metrics:
            return {}
        
        assessment = {
            "overall_score": 0,
            "funding": "unknown",
            "maintenance": "unknown",
            "contributors": "unknown",
            "bus_factor": "unknown",
            "recommendations": []
        }
        
        # 维护活跃度评估
        maint_score = metrics.get("maintenance_score", 0)
        if maint_score >= 70:
            assessment["maintenance"] = "active"
        elif maint_score >= 40:
            assessment["maintenance"] = "moderate"
        else:
            assessment["maintenance"] = "inactive"
            assessment["recommendations"].append("⚠️ Maintenance activity is low")
        
        # 贡献者评估
        comm_score = metrics.get("community_score", 0)
        total_contrib = metrics.get("total_contributors", 0)
        recent_contrib = metrics.get("unique_contributors_last_30_days", 0)
        
        if comm_score >= 70 and total_contrib > 50:
            assessment["contributors"] = "healthy"
        elif comm_score >= 40 or total_contrib > 20:
            assessment["contributors"] = "declining" if recent_contrib < 3 else "healthy"
        else:
            assessment["contributors"] = "critical"
            assessment["recommendations"].append("🚨 Very few contributors - high risk")
        
        # 巴士因子评估 (简化版)
        if recent_contrib >= 5:
            assessment["bus_factor"] = "low"
        elif recent_contrib >= 2:
            assessment["bus_factor"] = "medium"
        else:
            assessment["bus_factor"] = "high"
            assessment["recommendations"].append("🚌 Bus factor is high - knowledge concentrated in few people")
        
        # 资金状况 (无法自动判断，需要人工输入)
        assessment["funding"] = "unknown"  # 需要人工调研
        
        # 总体分数
        assessment["overall_score"] = (maint_score + comm_score) // 2
        
        return assessment


def print_report(metrics: dict, assessment: dict):
    """打印评估报告"""
    print("\n" + "="*60)
    print(f"📋 Health Report: {metrics.get('full_name')}")
    print("="*60)
    
    print(f"\n📊 Basic Metrics:")
    print(f"  ⭐ Stars: {metrics.get('stars', 0):,}")
    print(f"  🍴 Forks: {metrics.get('forks', 0):,}")
    print(f"  🐛 Open Issues: {metrics.get('open_issues', 0):,}")
    print(f"  👥 Total Contributors: {metrics.get('total_contributors', 0)}")
    
    print(f"\n📈 Activity (Last 30 Days):")
    print(f"  📝 Commits: {metrics.get('commits_last_30_days', 0)}")
    print(f"  👤 Active Contributors: {metrics.get('unique_contributors_last_30_days', 0)}")
    
    print(f"\n🏥 Health Assessment:")
    print(f"  Overall Score: {assessment.get('overall_score', 0)}/100")
    print(f"  Funding: {assessment.get('funding', 'unknown')}")
    print(f"  Maintenance: {assessment.get('maintenance', 'unknown')}")
    print(f"  Contributors: {assessment.get('contributors', 'unknown')}")
    print(f"  Bus Factor: {assessment.get('bus_factor', 'unknown')}")
    
    if assessment.get('recommendations'):
        print(f"\n⚠️  Recommendations:")
        for rec in assessment['recommendations']:
            print(f"  • {rec}")
    
    print("\n" + "="*60)


def generate_hugo_frontmatter(project_name: str, metrics: dict, assessment: dict) -> str:
    """生成 Hugo front matter"""
    return f"""+++
date = '{datetime.now().isoformat()}'
title = '{project_name}'
logo = ''
description = "{metrics.get('description', '')}"

[health]
  funding = "{assessment.get('funding', 'unknown')}"
  maintenance = "{assessment.get('maintenance', 'unknown')}"
  contributors = "{assessment.get('contributors', 'unknown')}"
  bus_factor = "{assessment.get('bus_factor', 'unknown')}"
  score = {assessment.get('overall_score', 0)}

[github]
  stars = {metrics.get('stars', 0)}
  forks = {metrics.get('forks', 0)}
  contributors = {metrics.get('total_contributors', 0)}
  url = "{metrics.get('url', '')}"
+++

### Overview

{metrics.get('description', 'No description available.')}

### GitHub Stats

- ⭐ **Stars**: {metrics.get('stars', 0):,}
- 🍴 **Forks**: {metrics.get('forks', 0):,}
- 👥 **Contributors**: {metrics.get('total_contributors', 0)}
- 📝 **Commits (30d)**: {metrics.get('commits_last_30_days', 0)}

### Auto-generated Assessment

This project's health metrics were automatically generated on {datetime.now().strftime('%Y-%m-%d')}.
Please review and adjust the funding status manually as it cannot be determined from public data.
"""


def main():
    parser = argparse.ArgumentParser(
        description="Fetch GitHub metrics for Infrastructure Heroes"
    )
    parser.add_argument(
        "--repo",
        help="Repository in format owner/repo (e.g., openssl/openssl)"
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output file for metrics JSON"
    )
    parser.add_argument(
        "--frontmatter",
        "-f",
        help="Generate Hugo front matter and save to file"
    )
    parser.add_argument(
        "--token",
        "-t",
        help="GitHub personal access token (or set GITHUB_TOKEN env var)"
    )
    
    args = parser.parse_args()
    
    if not args.repo:
        parser.print_help()
        print("\n❌ Please specify a repository with --repo owner/repo")
        sys.exit(1)
    
    # 解析 owner/repo
    try:
        owner, repo = args.repo.split("/")
    except ValueError:
        print("❌ Invalid repo format. Use: owner/repo")
        sys.exit(1)
    
    # 创建获取器并获取指标
    fetcher = GitHubMetricsFetcher(token=args.token)
    metrics = fetcher.fetch_repo_metrics(owner, repo)
    
    if not metrics:
        print("❌ Failed to fetch metrics")
        sys.exit(1)
    
    # 评估健康度
    assessment = fetcher.assess_health(metrics)
    
    # 打印报告
    print_report(metrics, assessment)
    
    # 保存 JSON
    if args.output:
        output_data = {
            "metrics": metrics,
            "assessment": assessment,
            "generated_at": datetime.now().isoformat()
        }
        with open(args.output, 'w') as f:
            json.dump(output_data, f, indent=2)
        print(f"\n💾 Metrics saved to: {args.output}")
    
    # 生成 Hugo front matter
    if args.frontmatter:
        frontmatter = generate_hugo_frontmatter(repo, metrics, assessment)
        with open(args.frontmatter, 'w') as f:
            f.write(frontmatter)
        print(f"💾 Hugo front matter saved to: {args.frontmatter}")
    
    print("\n✅ Done!")


if __name__ == "__main__":
    main()
