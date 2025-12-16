# PRD 目录说明

本目录包含项目特定的文档和规范索引。

## 目录结构

### 规范文档索引
- **`openspec.md`** - OpenSpec 主规格索引文档
  - 包含所有核心模块规范的索引和链接
  - 规范文档的实际位置：`../openspec/specs/[capability]/spec.md`

### 项目特定文档
- **`开发范式文档.md`** - 项目开发范式说明
  - 说明如何按照 OpenSpec 标准进行开发
  - OpenSpec 交互入口与规范约定

- **`审查报告.md`** - OpenSpec 文档审查与评审记录
  - 记录文档审查时间、发现问题、兼容性评估等

- **`spec_example.md`** - OpenSpec 结构示例文档
  - 展示完整的 OpenSpec 结构作为参考模板

## 规范文档位置

**重要**：所有规范文档已迁移到 OpenSpec 标准结构：

```
openspec/specs/
├── strategy-engine/spec.md  # 策略执行引擎规范
├── account/spec.md          # 账户与持仓规范
├── order/spec.md            # 订单管理规范
├── market-data/spec.md      # 行情数据规范
└── python-sdk/spec.md       # Python SDK 规范
```

这些是**权威来源**，请使用这些位置的文档。

## 查看规范

使用 OpenSpec CLI 工具查看规范：

```bash
# 列出所有规范
openspec list --specs

# 查看具体规范
openspec show <capability> --type spec

# 例如
openspec show strategy-engine --type spec
openspec show account --type spec
```

## 工作流程

1. **查看现有规范**：使用 `openspec list --specs` 或查看 `openspec/specs/` 目录
2. **创建变更提案**：使用 `/openspec-proposal` 命令
3. **实现变更**：使用 `/openspec-apply` 命令
4. **归档变更**：使用 `/openspec-archive` 命令

## 快速参考

- **[如何提需求](./如何提需求.md)** - 详细的需求提交流程指南（**推荐先看这个**）
- [开发范式文档](./开发范式文档.md) - 项目开发规范
- [OpenSpec 工作流程](../openspec/AGENTS.md) - 详细的工作流程说明

