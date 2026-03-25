# Startup Prompt for New Session

> Copy-paste this into the new Claude Code session at `~/workspaces/pactkit-codex/`.

---

我在开发 pactkit-codex，一个独立项目，目标是把 PactKit（PDCA 工作流框架）适配到 OpenAI Codex CLI。

## 背景
- PactKit 是 AI 编码助手的 PDCA 项目管理框架（Plan-Act-Check-Done）
- 已支持 Claude Code 和 OpenCode，现在要支持 Codex CLI
- 主仓库 `~/workspaces/pactkit/` 有完整的 prompt 模板和集成清单
- 本项目是独立的，不修改 pactkit 主仓库

## 本项目的参考文档（先全部读一遍）
1. `docs/reference/pactkit-architecture.md` — PactKit 组件清单和架构概览
2. `docs/reference/pactkit-prompts-inventory.md` — 所有 prompt 模块的内容摘要
3. `docs/reference/tool-integration-checklist.md` — 10 维度集成清单（从 OpenCode 集成教训提炼）
4. `docs/reference/codex-integration-preresearch.md` — Codex CLI 调研模板（大量"待填写"）
5. `docs/reference/pactkit-profiles.py` — FormatProfile 数据结构

## Codex CLI 特征
- 单 agent（无 multi-role）、无 custom commands、无 @import
- 用 `AGENTS.md` 作为项目指令文件
- `.codex/skills/` 放 skills
- OpenAI models only (GPT-4o, o3, o4-mini)
- Sandbox 权限模式
- GitHub repo: https://github.com/openai/codex

## PactKit 源码位置（只读参考）
- `~/workspaces/pactkit/src/pactkit/prompts/` — 所有 prompt 模板源码
- `~/workspaces/pactkit/src/pactkit/skills/` — standalone skill 脚本
- `~/workspaces/pactkit/src/pactkit/profiles.py` — FormatProfile 定义
- `~/workspaces/pactkit/src/pactkit/config.py` — VALID_AGENTS/COMMANDS/SKILLS/RULES

## 第一步
请先读完本项目 `docs/reference/` 下的所有文档，然后：
1. 用 WebFetch 抓 Codex CLI 的 GitHub repo（https://github.com/openai/codex）和文档
2. 完成 Dimension 1（Tool Research）调研 — 填完 `codex-integration-preresearch.md` 里的所有"待填写"项
3. 基于调研结果，决定每个能力的集成策略（Full Deploy vs Degraded Fallback）
4. 输出一个初步的项目计划
