# Infrastructure Heroes - 数据采集脚本

## 快速开始

### 1. 安装依赖

脚本使用 Python 3 标准库，无需额外依赖。

### 2. 获取单个项目指标

```bash
# 基础用法
python fetch-github-metrics.py --repo curl/curl

# 保存 JSON 报告
python fetch-github-metrics.py --repo curl/curl --output curl-metrics.json

# 生成 Hugo 页面
python fetch-github-metrics.py --repo curl/curl --frontmatter ../content/projects/curl-autogen.md

# 使用 GitHub Token (避免 API 限制)
python fetch-github-metrics.py --repo openssl/openssl --token ghp_xxxxxxxx
```

### 3. 环境变量

```bash
export GITHUB_TOKEN="ghp_your_token_here"
python fetch-github-metrics.py --repo nginx/nginx
```

## 输出示例

```
============================================================
📋 Health Report: curl/curl
============================================================

📊 Basic Metrics:
  ⭐ Stars: 35,000
  🍴 Forks: 6,000
  🐛 Open Issues: 400
  👥 Total Contributors: 250

📈 Activity (Last 30 Days):
  📝 Commits: 45
  👤 Active Contributors: 8

🏥 Health Assessment:
  Overall Score: 78/100
  Funding: unknown
  Maintenance: active
  Contributors: healthy
  Bus Factor: medium

⚠️  Recommendations:
  • 🚌 Bus factor is high - knowledge concentrated in few people

============================================================
```

## 批量处理

你可以创建一个项目列表文件来批量处理：

```bash
#!/bin/bash
PROJECTS=(
    "curl/curl"
    "openssl/openssl"
    "nginx/nginx"
    "postgresql/postgresql"
)

for repo in "${PROJECTS[@]}"; do
    name=$(echo $repo | cut -d'/' -f2)
    python fetch-github-metrics.py --repo $repo --output "data/${name}.json"
done
```

## 指标说明

### 自动获取的指标

| 指标 | 说明 |
|------|------|
| stars | GitHub Stars 数量 |
| forks | Fork 数量 |
| open_issues | 开放的 Issue 数量 |
| total_contributors | 总贡献者数量 |
| commits_last_30_days | 最近30天提交数 |
| unique_contributors_last_30_days | 最近30天活跃贡献者数 |
| recent_releases | 最近发布版本 |

### 自动评估的维度

| 维度 | 评估依据 |
|------|----------|
| maintenance | 提交频率 + 发布时间 + Issue 处理 |
| contributors | 贡献者数量 + 活跃度 |
| bus_factor | 最近活跃贡献者数量 |
| funding | 需要人工判断 |

## 注意事项

1. **GitHub API 限制**: 未认证每小时 60 次请求，使用 Token 可提高到 5000 次
2. **资金状况**: 无法从 GitHub API 自动获取，需要人工调研
3. **建议**: 定期运行脚本（如每周）来追踪项目健康度变化
