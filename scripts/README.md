# Infrastructure Heroes - 数据采集脚本

本目录包含站点项目数据的采集、评分与维护脚本。

## 快速开始

### 1. 安装依赖

需要 **Python >= 3.11**（脚本使用标准库 `tomllib` 解析 TOML front matter）。

```bash
pip install -r requirements.txt   # 仅 check_urls.py 需要 requests
```

其余脚本只依赖 Python 标准库。

### 2. 环境变量

```bash
export GITHUB_TOKEN="ghp_your_token_here"
```

GitHub API 未认证时每小时仅 60 次请求；设置 `GITHUB_TOKEN` 后可提高到 5000 次。脚本只从环境变量读取 Token，命令行不提供 `--token` 参数（避免 Token 出现在进程列表与 shell 历史中）。

## 脚本一览

| 脚本 | 用途 |
|------|------|
| `fetch-github-metrics.py` | 获取单个仓库指标、计算健康度、写入项目 front matter |
| `batch-update-health.py` | 批量刷新所有项目的健康度 |
| `update-historical-data.py` | 生成历史快照 `data/historical/YYYY-MM.json` |
| `check_urls.py` | 检查 logo URL 是否可访问（HTTP 200） |
| `add-github-links.py` | 按映射补全项目 `[links] github` |
| `update_logos.py` | 补全空的 `logo` 字段 |
| `link-maintainers-projects.py` | 在维护者与项目之间建立双向关联 |

> 已删除 `generate_projects.py`：它存在语法错误、使用 51/85 个过期 slug，且其输出写入逻辑已失效。

## fetch-github-metrics.py

```bash
# 打印健康度报告
python scripts/fetch-github-metrics.py --repo curl/curl

# 保存 JSON 报告
python scripts/fetch-github-metrics.py --repo curl/curl --output curl-metrics.json

# 更新 Hugo 项目 front matter
python scripts/fetch-github-metrics.py --repo curl/curl --frontmatter content/projects/curl.md

# 只计算不写入
python scripts/fetch-github-metrics.py --repo curl/curl --frontmatter content/projects/curl.md --dry-run
```

CLI 参数：`--repo owner/repo`、`--output/-o`、`--frontmatter/-f`、`--dry-run`。

### 数据完整性与 API 处理

- **重试**：5xx、429 以及带有 `Retry-After` / `X-RateLimit-Remaining: 0` / 限流信息的 403 会重试，最多 4 次，指数退避（单次最长 60 秒），优先遵循 `Retry-After`。
- **请求预算**：贡献者总数只用一次 `per_page=1` 请求读取 `Link rel="last"` 页号得到精确值；提交只采样最新 2 页（200 条）用于作者数与巴士因子。
- **精确计数回退**：若提交采样未覆盖到 90 天边界，再用两次 `per_page=1` 请求（`since=<30d>` 与 `since=<90d>&until=<30d>`）精确统计 30/90 天提交数；采样已覆盖边界时直接由采样得出，不发起额外请求。
- **失败不写入**：任一必需接口失败会抛错并跳过该项目的写入，绝不把失败当作 0 写入。
- **超大仓库贡献者**：GitHub 对超大仓库返回 403「contributor list is too large」时，标记贡献者不可用，保留 front matter 中已有的值（不记为 0，也不视为失败）。
- **front matter 重写**：先用 `tomllib` 解析现有 front matter，仅替换顶层 `[health]` 与 `[metrics]` 两个表，其余字节原样保留；写入前再次用 `tomllib` 校验，解析失败则拒绝写入。

### 输出示例

```
============================================================
📋 Health Report: curl/curl
============================================================

📊 Basic Metrics:
  ⭐ Stars: 35,000
  🍴 Forks: 6,000
  🐛 Open Issues: 400
  👥 Total Contributors: 250

📈 Activity:
  📝 Commits (30d): 45
  📝 Commits (90d): 120
  👤 Active Contributors (90d): 8

🏥 Health Assessment:
  Overall Score: 78/100
  Funding: at-risk
  Maintenance: active
  Contributors: healthy
  Bus Factor: medium
============================================================
```

### 健康度算法（Methodology v1.0）

```
Health Score = (Funding × 0.25) + (Maintenance × 0.30)
             + (Contributors × 0.25) + (Bus Factor × 0.20)
```

| 维度 | 评分依据 |
|------|----------|
| maintenance | 最近提交时间（40）+ 最近发布（30）+ 近 30 天提交数（30） |
| contributors | 近 90 天活跃贡献者 × 8（上限 80）+ 达到 10 人再 +20 |
| bus_factor | 覆盖 50% 近期提交所需人数：≥5 人 100；3–4 人 70；2 人 40；1 人 15 |
| funding | 见下方启发式 |

维度状态阈值：maintenance ≥70 active / ≥40 moderate / 否则 inactive；contributors ≥70 healthy / ≥40 declining / 否则 critical；bus_factor ≥70 low / ≥40 medium / 否则 high。

### 资金状况启发式（自动计算）

脚本会读取 `.github/FUNDING.yml` 与仓库 topics，在“热度”基础分上叠加资助来源加分：

- **基础分**：stars ≥ 10000 或贡献者 ≥ 100 → 70；stars ≥ 1000 或贡献者 ≥ 20 → 50；否则 25。
- **加分**：存在 FUNDING.yml +10；来源数量 ×5（上限 15）；各平台再加分（github_sponsors 10、open_collective 8、tidelift 8、patreon 5、ko-fi 3、liberapay 3、custom 2）。
- **状态**：最终分 ≥80 stable；≥50 at-risk；否则 critical。

> 资金分数仍是自动估算，建议人工复核；但并非“无法自动获取”。

## batch-update-health.py

```bash
python scripts/batch-update-health.py                 # 全部项目
python scripts/batch-update-health.py --limit 10      # 仅前 10 个（调试）
python scripts/batch-update-health.py --filter rust   # 仅名称匹配者
python scripts/batch-update-health.py --dry-run --limit 5
```

- 从项目 front matter 的 `[links] github` 读取仓库地址；没有链接的项目跳过。
- 单个项目失败时跳过并记录，最后汇总失败列表。
- **系统性失败**：超过一半的项目失败时以非零状态退出，便于 CI 告警；`--dry-run` 不会写入也不会失败退出。
- 只读取 `GITHUB_TOKEN` 环境变量。

## update-historical-data.py

```bash
python scripts/update-historical-data.py
```

读取所有项目的健康度，生成 `data/historical/YYYY-MM.json` 月度快照并更新 `summary.json`，供站点趋势图使用。

## check_urls.py

```bash
python scripts/check_urls.py
```

按 `scripts/logo_urls.json` 中的 slug → URL 映射逐个请求，检查是否返回 HTTP 200。为避免 CDN 对默认 User-Agent 的 403 误判，使用浏览器 UA。需要 `requests`。

## add-github-links.py

```bash
python scripts/add-github-links.py
```

按 `scripts/project-github-mapping.json` 为缺少 `[links] github` 的项目补全该字段；仅当 `[links]` 已存在于 front matter 内部时跳过。路径均相对仓库根目录解析。

## update_logos.py

```bash
python scripts/update_logos.py
```

按 `scripts/logo_urls.json` 补全项目的 `logo` 字段，只填充为空的 `logo = ''`，不会覆盖已有 Logo。

## link-maintainers-projects.py

```bash
python scripts/link-maintainers-projects.py            # 默认 dry-run
python scripts/link-maintainers-projects.py --apply    # 实际写入
python scripts/link-maintainers-projects.py --clean    # 仅报告无法匹配的项目（不删除）
```

在维护者文件与项目的顶层 `maintainers` 字段之间建立双向关联。默认只预览，`--apply` 才写入。

## 工作流集成

`.github/workflows/update-metrics.yml` 每周日 00:00 UTC 定时运行（也支持手动触发 `dry_run` 与 `limit` 输入），在 Python 3.11 上：

1. 使用 `GITHUB_TOKEN` 运行 `python scripts/batch-update-health.py --limit N`；
2. 运行 `python scripts/update-historical-data.py`；
3. 提交 `content/projects/` 与 `data/historical/` 的变更。

手动触发时若 `dry_run=true`，则只执行 `batch-update-health.py --dry-run --limit N`，不提交。

## 注意事项

1. **GitHub API 限制**：未认证每小时 60 次；请设置 `GITHUB_TOKEN`。
2. **数据完整性**：接口失败时脚本不会写入，避免把失败误记为 0；超大仓库的贡献者数量会保留旧值。
3. **建议**：定期运行脚本（工作流已每周执行）以追踪项目健康度变化。
