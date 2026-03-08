# ChaosCode

一个基于 Python 的 AI 辅助编程 CLI 工具，借鉴 opencode、gemini-cli、ms-agent 三个优秀开源项目的精华设计。

## 项目定位

- **语言**: Python 3.10+
- **界面**: TUI (Terminal User Interface)
- **架构**: 模块化、可扩展
- **核心功能**: 代码编辑、文件操作、终端执行、LLM 集成、MCP 协议支持

## 项目结构

```
chaosCode/
├── docs/                       # 项目文档
│   └── 00_TODO/               # 任务规划文档
│       └── 0.1_ChaosCode_Development_Plan.md  # 详细开发计划
├── reference_projects/         # 参考项目（不包含在仓库中）
│   ├── opencode/              # TypeScript/Bun 实现
│   ├── gemini-cli/            # Google Gemini CLI
│   └── ms-agent/              # Python Agent 框架
└── README.md                  # 项目说明
```

## 开发阶段

- [x] 阶段零：项目初始化与规划文档
- [ ] 阶段一：MVP 核心功能（LLM集成、工具系统、Agent核心）
- [ ] 阶段二：权限与安全系统
- [ ] 阶段三：MCP 协议支持
- [ ] 阶段四：TUI 界面
- [ ] 阶段五：高级功能（会话管理、Memory系统、Subagent）

## 参考项目精华

| 项目 | 技术栈 | 借鉴要点 |
|------|--------|----------|
| OpenCode | TypeScript/Bun | Agent模式切换、权限控制、Client/Server架构 |
| Gemini CLI | TypeScript | 工具确认机制、Zod验证、Subagent架构 |
| MS-Agent | Python | MCP协议集成、多LLM后端、Callback生命周期 |

## 快速开始

```bash
# 安装（开发完成后）
pip install chaos-code

# 基本使用
chaos-code chat "帮我创建一个 Python 项目结构"

# 交互模式
chaos-code repl
```

## 文档

详细的开发计划请参阅: [开发计划文档](docs/00_TODO/0.1_ChaosCode_Development_Plan.md)

## 许可证

MIT
