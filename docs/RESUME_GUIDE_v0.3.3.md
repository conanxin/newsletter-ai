# newsletter-ai v0.3.3 Resume Guide — Digest Sectioning by Topic

## v0.3.3 主题
Digest Sectioning by Topic

## 目标
把 digest 从单一列表升级为按主题分区输出。

推荐分区示例：
- AI / Models / Agents
- Strategy / Business / Platforms
- Culture / Media / Ideas
- Tools / Workflow
- Other

## v0.3.3 第一阶段建议文件
- src/newsletter_ai/sections.py
- tests/test_sections.py
- tests/test_render_sections.py
- tests/test_pipeline_sections_integration.py

## v0.3.3 核心要求
1. 根据 topic_tags / source / style_tags 给 item 分区。
2. digest markdown 按 section 输出。
3. telegram text 也按 section 输出，但保持简洁。
4. latest_items.json 仍保留全局 item_index，不能因分区破坏 feedback "like 1"。
5. items show 仍按全局编号展示。
6. quality report 增加 section_distribution。
7. 测试证明 section rendering 与 snapshot item_index 一致。

## v0.3.3 暂不做
- LLM 摘要生成
- 真实网络抓取
- Telegram 交互按钮
- Hermes wiki ingest
- GitHub Pages
- hosted backend

## 建议实现顺序
1. sections.py：定义分区规则 + 分区函数
2. 扩展 quality report：增加 section_distribution
3. 更新 pipeline：调用 sections 逻辑
4. 更新 CLI / render：支持分区输出
5. 补充测试：验证 item_index 不受分区影响

## 安全约束
- 所有测试使用 fixture-first
- 不请求真实外网
- 不真实发送 Telegram

---
**v0.3.2 已关闭**：6b6d413 add newsletter-ai v0.3.2 source scoring and fuzzy dedupe
**当前分支**：harden-v0.2-newsletter-ai

**v0.3.2.1 完成**：quality sources / quality duplicates 已注册，quality CLI 四个入口全部可用。
**准备状态**：v0.3.3 规划文档已生成，可开始第一阶段开发。