# newsletter-ai

newsletter-ai 是一个本地优先、安全默认、可回归测试的个人 newsletter / RSS 信息摄入引擎。它可以从 fixture、RSS、replay source 中读取内容，经过归一化、排序、主题分区、质量检查和用户反馈，生成可持续优化的每日 digest。

## 1. 项目简介

每天面对大量信息源，手动筛选成本高、容易遗漏。newsletter-ai 希望解决以下问题：

- 信息源太多，需要一个统一入口；
- RSS / 新闻 / 技术博客 / link digest 需要结构化处理；
- 默认离线、安全、可测试，不依赖真实网络；
- 通过 feedback 逐渐学习个人偏好，越用越准；
- 真实 RSS 抓取可被 replay，避免测试依赖网络。

## 2. 当前能力概览

| 能力 | 状态 | 说明 |
|---|---|---|
| dry-run daily | 已支持 | 默认使用 fixture，不联网、不发送 Telegram |
| source registry | 已支持 | 管理 rss_fixture / rss_url / rss_replay |
| RSS parser | 已支持 | 解析本地 RSS XML 和受控 RSS URL |
| normalize | 已支持 | 统一 item schema |
| ranking | 已支持 | 根据 source/topic/style/preference 排序 |
| sectioned digest | 已支持 | 按 topic section 输出 digest |
| current-run quality report | 已支持 | sections / sources / duplicates |
| feedback preferences | 已支持 | like/save/dislike/source_up 等 |
| replay capture | 已支持 | 真实 RSS 抓取后保存为离线 replay |
| replay governance | 已支持 | list / inspect / validate / promote |
| run artifact index | 已支持 | runs list/latest/inspect |
| safe publisher / Telegram dry-run | 已支持 | 默认 DryRunPublisher，真实发送需额外配置 |

## 3. 核心流程

```
source registry / fixture / rss_url / replay
→ fetch / parse / normalize
→ ranking
→ snapshot
→ sectioned digest
→ current-run quality report
→ feedback
→ preferences history
→ run artifact index
```

**各步骤说明：**

- **source registry / fixture / rss_url / replay**：数据来源。fixture 和 replay 完全离线；rss_url 需要显式 `--allow-network`。
- **fetch / parse / normalize**：统一 item schema，生成稳定的 item_id，处理缺失字段。
- **ranking**：根据 source 权重、topic 偏好、style 偏好、用户反馈历史排序。
- **snapshot**：保存当前 run 的 items，支持历史回溯。
- **sectioned digest**：按 topic section（如 ai / business / media）分组输出 markdown 和 telegram 文本。
- **current-run quality report**：分析 section 分布、source 质量、重复项。
- **feedback**：用户对 item 打分，更新偏好。
- **preferences history**：保存偏好变更历史，支持审计和回滚。
- **run artifact index**：记录每次运行的产物路径，支持 `runs list/latest/inspect`。

## 4. 安装与初始化

```bash
# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate

# 安装
pip install -e .
# 或
make install

# 验证
python -m pytest
make release-check
make validate
```

## 5. 快速开始

```bash
# 默认离线运行，使用 fixture 数据
newsletter-ai daily --dry-run

# 查看当前 items
newsletter-ai items show

# 解释第 1 条
newsletter-ai items explain 1

# 查看 quality report
newsletter-ai quality sections
newsletter-ai quality sources
newsletter-ai quality duplicates

# 反馈（默认 --dry-run 不写入）
newsletter-ai feedback like 1 --dry-run
newsletter-ai feedback save 2 --note "值得深挖" --dry-run

# 查看最新运行记录
newsletter-ai runs latest
```

**说明：**
- `daily --dry-run` 默认不联网；
- 不会发送 Telegram；
- 会生成 snapshot / digest / quality / run record；
- `output/` 是运行产物，不提交到 Git。

## 6. Source Registry 使用说明

### rss_fixture

本地 RSS XML fixture，不联网。

### rss_url

真实 RSS URL，必须显式 `--allow-network` 才会联网。

### rss_replay

已捕获的 RSS replay 文件，不联网，适合测试和离线回放。

**常用命令：**

```bash
newsletter-ai sources validate
newsletter-ai sources ingest-fixtures
newsletter-ai sources report
newsletter-ai sources fetch --registry data/fixtures/source_registry.json
newsletter-ai sources fetch --registry data/fixtures/source_registry.json --allow-network
```

**注意：**
- 无 `--allow-network` 时 rss_url 会被跳过；
- 单个 source 失败不会拖垮整体；
- ingestion report 会记录 success / failed / disabled / skipped。

## 7. Replay 工作流

真实 RSS 抓一次，保存为 replay fixture，之后离线测试和开发都用 replay。

```bash
# 抓取并保存 replay
newsletter-ai sources fetch --registry data/fixtures/source_registry.json --allow-network --capture-replay

# 查看 replay 列表
newsletter-ai replay list

# 验证 replay 完整性
newsletter-ai replay validate

# 查看 replay 详情
newsletter-ai replay inspect <xml_path>

# 生成 registry entry 建议（dry-run，不直接改 registry）
newsletter-ai replay promote <xml_path> --source-id <id> --name "<name>"

# 使用 replay registry 离线运行
newsletter-ai daily --dry-run --source-registry data/fixtures/replay_source_registry.json
```

**说明：**
- replay 保存 XML + metadata JSON；
- `sanitize_replay_xml` 会移除常见 tracking query（如 utm_*、fbclid、gclid、mc_*）；
- `replay promote` 默认只输出建议 registry entry，不直接改 registry；
- `data/fixtures/replay/` 中已有 HN frontpage replay 作为真实世界离线回归样例。

## 8. Digest 与 Quality Report

`daily` 会生成：
- `latest_items.json`
- sectioned markdown digest
- telegram text
- `latest_quality.json`
- `last-run-status.json`
- run record

**查看 quality：**

```bash
newsletter-ai quality sections
newsletter-ai quality sources
newsletter-ai quality duplicates
```

**说明：**
- quality 命令读取当前 run 的 `latest_quality.json`；
- 如果没有 quality report，需要先运行 `daily --dry-run`；
- section_distribution / source_quality / duplicate_report 用于评估 digest 质量。

## 9. Feedback 与偏好学习

| 命令 | 作用 |
|---|---|
| `newsletter-ai feedback like 1` | 喜欢第 1 条 |
| `newsletter-ai feedback dislike 2` | 不喜欢第 2 条 |
| `newsletter-ai feedback save 3 --note "..."` | 收藏并记录备注 |
| `newsletter-ai feedback skip 4` | 跳过 |
| `newsletter-ai feedback source_up Stratechery` | 提升来源权重 |
| `newsletter-ai feedback source_down Example` | 降低来源权重 |
| `newsletter-ai feedback topic_up ai` | 提升主题权重 |
| `newsletter-ai feedback style_up analysis` | 提升风格权重 |

**说明：**
- item index 来自 `latest_items.json`；
- section 展示不改变全局 item_index；
- feedback 会写入 `feedback_events.jsonl`、`preferences.json`、`preferences_history.jsonl`；
- note 会写入 feedback event；
- `--dry-run` 用于预览，不应污染真实状态。

## 10. Runs 历史与产物索引

```bash
newsletter-ai runs list
newsletter-ai runs latest
newsletter-ai runs inspect <run_id>
```

run record 关联：
- snapshot_path
- digest_path
- telegram_path
- quality_report_path
- last_run_status_path
- ingestion_report_summary

## 11. 安全边界

- **默认不联网**：所有命令默认离线，rss_url 需要 `--allow-network`；
- **默认不发送 Telegram**：Publisher 默认为 DryRunPublisher；
- **Telegram token 只从环境变量读取**：`TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID`；
- **敏感文件不提交**：`output/`、`data/state/`、`.env`、`auth.json`、token 文件已加入 `.gitignore`；
- **replay 不保存敏感信息**：replay metadata 不保存 auth headers、cookies、tokens；
- **测试不依赖真实网络**：所有测试使用 fixture 和 mock。

## 12. 目录结构

```
src/newsletter_ai/          # 核心模块（21 个模块）
data/fixtures/              # 可提交的 fixture 数据
data/fixtures/replay/       # replay fixture
data/state/                 # 本地偏好和状态（不提交）
output/                     # 运行产物（不提交）
docs/                       # 文档
tests/                      # 测试（219 个测试）
legacy/v0.1/                # 旧脚本归档
```

## 13. 常用命令速查

### 日常运行
```bash
newsletter-ai daily --dry-run
newsletter-ai daily --dry-run --source-registry data/fixtures/source_registry.json
newsletter-ai daily --dry-run --source-registry data/fixtures/replay_source_registry.json
```

### 来源管理
```bash
newsletter-ai sources list
newsletter-ai sources validate
newsletter-ai sources ingest-fixtures
newsletter-ai sources report
newsletter-ai sources fetch --registry data/fixtures/source_registry.json
newsletter-ai sources fetch --registry data/fixtures/source_registry.json --allow-network
```

### Replay
```bash
newsletter-ai replay list
newsletter-ai replay validate
newsletter-ai replay inspect <xml_path>
newsletter-ai replay promote <xml_path> --source-id <id> --name "<name>"
```

### Quality
```bash
newsletter-ai quality sections
newsletter-ai quality sources
newsletter-ai quality duplicates
```

### Feedback
```bash
newsletter-ai feedback like 1 --dry-run
newsletter-ai feedback save 2 --note "值得深挖" --dry-run
newsletter-ai feedback source_up Stratechery --dry-run
newsletter-ai prefs explain
```

### Runs
```bash
newsletter-ai runs list
newsletter-ai runs latest
newsletter-ai runs inspect <run_id>
```

### 验证
```bash
python -m pytest
make release-check
make validate
```

## 14. 当前状态

- v0.3 已合并到 main；
- 当前 release gate 为 `pytest` / `make release-check` / `make validate`；
- 测试数以本地运行为准，当前审计时为 219 passed，后续新增测试以本地输出为准。

## 15. 后续计划

- 小规模真实 RSS 源长期试运行；
- Telegram 真发布验证；
- cron / 定时任务；
- Hermes wiki / Obsidian 接入；
- GitHub Pages digest archive；
- 更强摘要生成。
