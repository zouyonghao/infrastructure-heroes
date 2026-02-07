#!/usr/bin/env python3
"""
Infrastructure Heroes - GitHub Metrics Fetcher
自动从 GitHub API 获取项目指标，计算健康度评分

Usage:
    python fetch-github-metrics.py --repo owner/repo [--output metrics.json]
    python fetch-github-metrics.py --repo owner/repo --frontmatter content/projects/project.md
    
Health Score Formula (Methodology v1.0):
    Health Score = (Funding × 0.25) + (Maintenance × 0.30) + (Contributors × 0.25) + (Bus Factor × 0.20)
    
Each dimension scored 0-100, weighted and combined for final 0-100 score.
"""

import argparse
import json
import os
import sys
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import urllib.request
import urllib.error


class GitHubMetricsFetcher:
    """GitHub 项目指标获取器 - Infrastructure Heroes Methodology v1.0"""
    
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
        """获取仓库基本指标和扩展指标"""
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
        
        # 获取最近100次提交（用于计算贡献者和巴士因子）
        commits = self._api_request(f"/repos/{owner}/{repo}/commits?per_page=100")
        metrics["commits_data"] = commits if commits else []
        
        # 计算时间维度指标
        today = datetime.now()
        
        # 最近30天提交和作者
        thirty_days_ago = today - timedelta(days=30)
        # 最近90天提交和作者
        ninety_days_ago = today - timedelta(days=90)
        
        recent_30d_commits = 0
        recent_90d_commits = 0
        authors_30d = set()
        authors_90d = set()
        all_commit_authors = []  # 用于计算巴士因子
        
        for commit in metrics["commits_data"]:
            if isinstance(commit, dict):
                commit_date_str = commit.get("commit", {}).get("committer", {}).get("date", "")
                if commit_date_str:
                    try:
                        commit_time = datetime.fromisoformat(commit_date_str.replace("Z", "+00:00"))
                        commit_time = commit_time.replace(tzinfo=None)
                        
                        author = commit.get("author", {}).get("login") if commit.get("author") else None
                        if not author:
                            # 使用 commit 中的作者名称
                            author = commit.get("commit", {}).get("author", {}).get("name", "unknown")
                        
                        all_commit_authors.append(author)
                        
                        if commit_time > thirty_days_ago:
                            recent_30d_commits += 1
                            authors_30d.add(author)
                        
                        if commit_time > ninety_days_ago:
                            recent_90d_commits += 1
                            authors_90d.add(author)
                    except Exception as e:
                        pass
        
        metrics["commits_last_30_days"] = recent_30d_commits
        metrics["commits_last_90_days"] = recent_90d_commits
        metrics["unique_contributors_last_30_days"] = len(authors_30d)
        metrics["unique_contributors_last_90_days"] = len(authors_90d)
        metrics["all_commit_authors"] = all_commit_authors
        
        # 获取最近更新时间（pushed_at）
        if metrics.get("pushed_at"):
            try:
                pushed_time = datetime.fromisoformat(metrics["pushed_at"].replace("Z", "+00:00"))
                metrics["days_since_last_push"] = (today - pushed_time.replace(tzinfo=None)).days
            except:
                metrics["days_since_last_push"] = 365
        else:
            metrics["days_since_last_push"] = 365
        
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
        
        # 计算最近一次发布时间
        if metrics["recent_releases"]:
            try:
                last_release = datetime.fromisoformat(
                    metrics["recent_releases"][0]["published_at"].replace("Z", "+00:00")
                )
                metrics["days_since_last_release"] = (today - last_release.replace(tzinfo=None)).days
            except:
                metrics["days_since_last_release"] = 365
        else:
            metrics["days_since_last_release"] = 365
        
        # Fetch funding information
        funding_info = self.fetch_funding_info(owner, repo)
        metrics["funding_info"] = funding_info
        
        return metrics
    
    def calculate_maintenance_score(self, metrics: dict) -> int:
        """
        计算维护活跃度分数 (0-100) - Methodology v1.0
        
        Criteria:
        - Last commit recency (40%)
        - Release frequency (30%)  
        - Issue management (30%)
        """
        score = 0
        
        # 1. 最近提交时间 (40分)
        days_since_push = metrics.get("days_since_last_push", 365)
        if days_since_push < 7:
            score += 40
        elif days_since_push < 30:
            score += 35
        elif days_since_push < 60:
            score += 25
        elif days_since_push < 90:
            score += 15
        elif days_since_push < 180:
            score += 10
        else:
            score += 5
        
        # 2. 发布频率 (30分)
        days_since_release = metrics.get("days_since_last_release", 365)
        if days_since_release < 30:
            score += 30
        elif days_since_release < 90:
            score += 25
        elif days_since_release < 180:
            score += 15
        elif days_since_release < 365:
            score += 10
        else:
            score += 5
        
        # 3. 活跃程度 (30分) - 基于最近30天提交数
        commits_30d = metrics.get("commits_last_30_days", 0)
        if commits_30d >= 50:
            score += 30
        elif commits_30d >= 20:
            score += 25
        elif commits_30d >= 10:
            score += 20
        elif commits_30d >= 5:
            score += 15
        elif commits_30d >= 1:
            score += 10
        else:
            score += 0
        
        return min(score, 100)
    
    def calculate_contributors_score(self, metrics: dict) -> int:
        """
        计算贡献者健康度分数 (0-100) - Methodology v1.0
        
        Criteria:
        - Active contributors in last 90 days (80%)
        - Contributor trend bonus (20%)
        """
        # 基于最近90天活跃贡献者
        contributors_90d = metrics.get("unique_contributors_last_90_days", 0)
        
        # 基础分数：每个贡献者8分，最高80分
        base_score = min(contributors_90d * 8, 80)
        
        # 趋势奖励：如果有10+贡献者，加20分
        trend_bonus = 20 if contributors_90d >= 10 else 0
        
        return min(base_score + trend_bonus, 100)
    
    def calculate_bus_factor_score(self, metrics: dict) -> int:
        """
        计算巴士因子风险分数 (0-100) - Methodology v1.0
        
        Higher score = lower risk
        
        Criteria:
        - Number of people accounting for 50% of recent commits
        - 5+ people = low risk (100)
        - 3-4 people = medium risk (70)
        - 2 people = high risk (40)
        - 1 person = critical risk (15)
        """
        authors = metrics.get("all_commit_authors", [])
        if not authors:
            return 50  # Unknown
        
        # 统计每个作者的提交数
        from collections import Counter
        author_counts = Counter(authors)
        total_commits = len(authors)
        
        if total_commits == 0:
            return 50
        
        # 计算需要多少人覆盖50%的提交
        sorted_authors = author_counts.most_common()
        cumulative = 0
        people_for_50_percent = 0
        
        for author, count in sorted_authors:
            cumulative += count
            people_for_50_percent += 1
            if cumulative >= total_commits * 0.5:
                break
        
        metrics["bus_factor_people"] = people_for_50_percent
        
        # 根据巴士因子人数评分
        if people_for_50_percent >= 5:
            return 100  # Low risk
        elif people_for_50_percent >= 3:
            return 70   # Medium risk
        elif people_for_50_percent >= 2:
            return 40   # High risk
        else:
            return 15   # Critical risk
    
    def fetch_funding_info(self, owner: str, repo: str) -> dict:
        """
        Fetch funding information from GitHub API
        
        Returns dict with funding sources found
        """
        funding_info = {
            "has_funding_file": False,
            "funding_sources": [],
            "has_sponsors": False,
            "sponsor_count": 0
        }
        
        # Check for FUNDING.yml file
        funding_content = self._api_request(f"/repos/{owner}/{repo}/contents/.github/FUNDING.yml")
        if funding_content and funding_content.get("content"):
            import base64
            try:
                content = base64.b64decode(funding_content["content"]).decode('utf-8')
                funding_info["has_funding_file"] = True
                
                # Parse funding sources
                if 'github:' in content:
                    funding_info["funding_sources"].append("github_sponsors")
                if 'open_collective:' in content or 'opencollective:' in content:
                    funding_info["funding_sources"].append("open_collective")
                if 'patreon:' in content:
                    funding_info["funding_sources"].append("patreon")
                if 'tidelift:' in content:
                    funding_info["funding_sources"].append("tidelift")
                if 'ko_fi:' in content or 'ko-fi:' in content:
                    funding_info["funding_sources"].append("ko-fi")
                if 'liberapay:' in content:
                    funding_info["funding_sources"].append("liberapay")
                if 'custom:' in content:
                    funding_info["funding_sources"].append("custom")
            except Exception:
                pass
        
        # Check repository topics for funding-related tags
        topics_data = self._api_request(f"/repos/{owner}/{repo}/topics")
        if topics_data and "names" in topics_data:
            funding_topics = [t for t in topics_data["names"] if t in 
                            ['funding', 'sponsors', 'donate', 'sustainability', 'open-collective']]
            if funding_topics:
                funding_info["funding_sources"].extend(funding_topics)
        
        return funding_info
    
    def calculate_funding_score(self, metrics: dict, funding_info: dict = None) -> Tuple[int, str]:
        """
        估算资金状况分数 (0-100) - Methodology v1.0 Enhanced
        
        Uses both popularity metrics and actual funding sources detected.
        Manual verification is always recommended.
        
        Returns: (score, status)
        """
        stars = metrics.get("stars", 0)
        contributors = metrics.get("total_contributors", 0)
        
        # Base score from popularity (as before)
        if stars >= 10000 or contributors >= 100:
            base_score = 70  # 大型项目通常有资助基础
        elif stars >= 1000 or contributors >= 20:
            base_score = 50  # 中型项目可能资助不稳定
        else:
            base_score = 25  # 小型项目很可能缺乏资助
        
        # Boost score based on detected funding sources
        funding_boost = 0
        if funding_info:
            sources = funding_info.get("funding_sources", [])
            
            # Having a FUNDING.yml shows intent
            if funding_info.get("has_funding_file"):
                funding_boost += 10
            
            # Multiple funding sources is good
            unique_sources = len(set(sources))
            funding_boost += min(unique_sources * 5, 15)  # Max 15 points for diversity
            
            # Specific platforms indicate active fundraising
            platform_scores = {
                "github_sponsors": 10,  # GitHub sponsors is reliable
                "open_collective": 8,   # Open Collective is transparent
                "tidelift": 8,          # Tidelift is professional
                "patreon": 5,           # Patreon is common
                "ko-fi": 3,
                "liberapay": 3,
                "custom": 2
            }
            
            for source in sources:
                if source in platform_scores:
                    funding_boost += platform_scores[source]
        
        final_score = min(100, base_score + funding_boost)
        
        # Determine status
        if final_score >= 80:
            return final_score, "stable"
        elif final_score >= 50:
            return final_score, "at-risk"
        else:
            return final_score, "critical"
    
    def assess_health(self, metrics: dict) -> dict:
        """
        基于方法论 v1.0 评估项目健康度
        
        Formula: (Funding × 0.25) + (Maintenance × 0.30) + (Contributors × 0.25) + (Bus Factor × 0.20)
        """
        if not metrics:
            return {}
        
        # 计算各维度分数
        maintenance_score = self.calculate_maintenance_score(metrics)
        contributors_score = self.calculate_contributors_score(metrics)
        bus_factor_score = self.calculate_bus_factor_score(metrics)
        funding_info = metrics.get("funding_info")
        funding_score, funding_status = self.calculate_funding_score(metrics, funding_info)
        
        # 计算总体分数（加权平均）
        overall_score = int(
            funding_score * 0.25 +
            maintenance_score * 0.30 +
            contributors_score * 0.25 +
            bus_factor_score * 0.20
        )
        
        # 确定各维度状态
        def get_maintenance_status(score):
            if score >= 70: return "active"
            elif score >= 40: return "moderate"
            else: return "inactive"
        
        def get_contributors_status(score):
            if score >= 70: return "healthy"
            elif score >= 40: return "declining"
            else: return "critical"
        
        def get_bus_factor_status(score):
            if score >= 70: return "low"
            elif score >= 40: return "medium"
            else: return "high"
        
        assessment = {
            "overall_score": overall_score,
            "funding": funding_status,
            "funding_score": funding_score,
            "maintenance": get_maintenance_status(maintenance_score),
            "maintenance_score": maintenance_score,
            "contributors": get_contributors_status(contributors_score),
            "contributors_score": contributors_score,
            "bus_factor": get_bus_factor_status(bus_factor_score),
            "bus_factor_score": bus_factor_score,
            "calculated_at": datetime.now().isoformat(),
            "methodology_version": "1.0",
            "recommendations": []
        }
        
        # 生成建议
        if maintenance_score < 40:
            assessment["recommendations"].append("⚠️ Low maintenance activity - consider contributing code or documentation")
        
        if contributors_score < 40:
            assessment["recommendations"].append("🚨 Few active contributors - high community risk")
        
        if bus_factor_score < 40:
            assessment["recommendations"].append(f"🚌 High bus factor risk - only {metrics.get('bus_factor_people', 1)} person(s) handle 50% of work")
        
        if funding_status == "critical":
            assessment["recommendations"].append("💰 Project likely lacks funding - consider sponsorship")
        
        return assessment


def print_report(metrics: dict, assessment: dict):
    """打印评估报告"""
    print("\n" + "="*70)
    print(f"📋 Health Report: {metrics.get('full_name')}")
    print(f"   Methodology: v{assessment.get('methodology_version', '1.0')}")
    print("="*70)
    
    print(f"\n📊 Basic Metrics:")
    print(f"  ⭐ Stars: {metrics.get('stars', 0):,}")
    print(f"  🍴 Forks: {metrics.get('forks', 0):,}")
    print(f"  🐛 Open Issues: {metrics.get('open_issues', 0):,}")
    print(f"  👥 Total Contributors: {metrics.get('total_contributors', 0)}")
    
    print(f"\n📈 Activity:")
    print(f"  📝 Commits (30d): {metrics.get('commits_last_30_days', 0)}")
    print(f"  📝 Commits (90d): {metrics.get('commits_last_90_days', 0)}")
    print(f"  👤 Active Contributors (90d): {metrics.get('unique_contributors_last_90_days', 0)}")
    print(f"  📅 Days Since Last Push: {metrics.get('days_since_last_push', 'N/A')}")
    print(f"  📅 Days Since Last Release: {metrics.get('days_since_last_release', 'N/A')}")
    
    print(f"\n🏥 Health Assessment:")
    print(f"  ┌──────────────────┬────────┬──────────────┐")
    print(f"  │ Dimension        │ Score  │ Status       │")
    print(f"  ├──────────────────┼────────┼──────────────┤")
    print(f"  │ 💰 Funding       │ {assessment.get('funding_score', 0):>3}/100 │ {assessment.get('funding', 'unknown'):>12} │")
    print(f"  │ 🔧 Maintenance   │ {assessment.get('maintenance_score', 0):>3}/100 │ {assessment.get('maintenance', 'unknown'):>12} │")
    print(f"  │ 👥 Contributors  │ {assessment.get('contributors_score', 0):>3}/100 │ {assessment.get('contributors', 'unknown'):>12} │")
    print(f"  │ 🚌 Bus Factor    │ {assessment.get('bus_factor_score', 0):>3}/100 │ {assessment.get('bus_factor', 'unknown'):>12} │")
    print(f"  ├──────────────────┼────────┼──────────────┤")
    print(f"  │ 📊 OVERALL       │ {assessment.get('overall_score', 0):>3}/100 │ {'🟢' if assessment.get('overall_score', 0) >= 80 else '🟡' if assessment.get('overall_score', 0) >= 60 else '🔴'} {assessment.get('overall_score', 0):>8} │")
    print(f"  └──────────────────┴────────┴──────────────┘")
    
    # Show funding sources if detected
    funding_info = metrics.get('funding_info', {})
    if funding_info and funding_info.get('funding_sources'):
        print(f"\n💰 Funding Sources Detected:")
        if funding_info.get('has_funding_file'):
            print(f"  ✅ FUNDING.yml file present")
        sources = funding_info.get('funding_sources', [])
        for source in set(sources):
            print(f"  • {source.replace('_', ' ').title()}")
    
    if assessment.get('recommendations'):
        print(f"\n⚠️  Recommendations:")
        for rec in assessment['recommendations']:
            print(f"  • {rec}")
    
    print("\n" + "="*70)
    if funding_info and funding_info.get('funding_sources'):
        print("💡 Funding sources detected automatically. Score may still need manual verification.")
    else:
        print("💡 Note: Funding status is estimated. Please verify manually.")
    print("="*70)


def update_hugo_frontmatter(filepath: str, assessment: dict, metrics: dict) -> bool:
    """更新 Hugo 项目文件的 front matter"""
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return False
    
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        # 解析 front matter (TOML format between +++)
        frontmatter_match = re.search(r'\+\+\+(.*?)\+\+\+', content, re.DOTALL)
        if not frontmatter_match:
            print("❌ Could not find front matter in file")
            return False
        
        frontmatter = frontmatter_match.group(1)
        
        # 更新 health section
        health_section = f"""[health]
  funding = "{assessment.get('funding', 'unknown')}"
  maintenance = "{assessment.get('maintenance', 'unknown')}"
  contributors = "{assessment.get('contributors', 'unknown')}"
  bus_factor = "{assessment.get('bus_factor', 'unknown')}"
  score = {assessment.get('overall_score', 0)}"""
        
        # 检查是否已有 [health] section
        if '[health]' in frontmatter:
            # 替换现有 section
            new_frontmatter = re.sub(
                r'\[health\].*?(?=\[|$)',
                health_section + "\n",
                frontmatter,
                flags=re.DOTALL
            )
        else:
            # 添加新 section
            new_frontmatter = frontmatter.rstrip() + "\n\n" + health_section + "\n"
        
        # 添加 metrics section
        metrics_section = f"""\n[metrics]
  updated_at = "{datetime.now().strftime('%Y-%m-%d')}"
  stars = {metrics.get('stars', 0)}
  forks = {metrics.get('forks', 0)}
  contributors = {metrics.get('total_contributors', 0)}
  commits_30d = {metrics.get('commits_last_30_days', 0)}
  commits_90d = {metrics.get('commits_last_90_days', 0)}
  bus_factor_people = {metrics.get('bus_factor_people', 0)}
"""
        
        if '[metrics]' in new_frontmatter:
            new_frontmatter = re.sub(
                r'\[metrics\].*?(?=\[|$)',
                metrics_section.strip() + "\n",
                new_frontmatter,
                flags=re.DOTALL
            )
        else:
            new_frontmatter = new_frontmatter.rstrip() + metrics_section
        
        # 重新组装文件
        new_content = content.replace(frontmatter_match.group(0), f"+++{new_frontmatter}+++")
        
        with open(filepath, 'w') as f:
            f.write(new_content)
        
        print(f"✅ Updated front matter in: {filepath}")
        return True
        
    except Exception as e:
        print(f"❌ Error updating front matter: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Fetch GitHub metrics and calculate health scores for Infrastructure Heroes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python fetch-github-metrics.py --repo openssl/openssl
    python fetch-github-metrics.py --repo torvalds/linux --output linux-metrics.json
    python fetch-github-metrics.py --repo python/cpython --frontmatter content/projects/python.md
        """
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
        help="Update Hugo front matter in specified file"
    )
    parser.add_argument(
        "--token",
        "-t",
        help="GitHub personal access token (or set GITHUB_TOKEN env var)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Calculate scores but don't write to file"
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
            json.dump(output_data, f, indent=2, default=str)
        print(f"\n💾 Metrics saved to: {args.output}")
    
    # 更新 Hugo front matter
    if args.frontmatter:
        if args.dry_run:
            print(f"\n🔍 Dry run - would update: {args.frontmatter}")
        else:
            success = update_hugo_frontmatter(args.frontmatter, assessment, metrics)
            if not success:
                sys.exit(1)
    
    print("\n✅ Done!")


if __name__ == "__main__":
    main()
