# rag-smart-qa

基于 RAG MCP 的智能问答：先查知识库列表再检索，检索知识库原文，尽量不修改原意回答，自动渲染图片。不预设默认知识库。

## 简介

纯 RAG MCP 驱动的智能问答技能。固定流程：先查当前用户可见的知识库列表，再检索知识库原文，基于原文回答、不编造、不预设默认知识库，支持图片自动渲染。适用于云枢、SylixOS、VSOA 等产品文档的知识库问答场景。

## 目录结构

```
rag-smart-qa/
└── SKILL.md
```

## 使用说明

本仓库为一个 Agent Skill（技能包）：根目录 `SKILL.md` 包含完整技能说明（frontmatter 元数据 + 执行流程与规则），
Agent 加载后按其流程执行；配套文件（`references/`、`scripts/` 等）在技能运行时按需读取。

## 来源

从本地 Hermes（AcoPilot 内置）技能库导出，同步至云枢 Gitea。
