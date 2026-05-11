# Bohrium AI Chat Skill

玻尔（Bohrium）科研空间站 AI 聊天技能，让 AI Agent 可以直接调用玻尔平台的 AI 学术助手进行学术问答、文献对话、学者查询等。

## 前置条件

1. 注册 Bohrium 账号：https://bohrium.dp.tech
2. 登录玻尔网页版，从浏览器 Local Storage 获取 `brm-token`
3. 设置环境变量 `BRM_TOKEN`

```powershell
setx BRM_TOKEN "your-brm-token-here"
```

## 可用脚本

### `bohrium_chat.py` - 玻尔 AI 聊天

```bash
# 列出所有可用 AI Agent（无需 token，公开 API）
python bohrium_chat.py list_agents

# 学术搜索（收费）
python bohrium_chat.py chat --agent sn --scene paper --message "量子计算最新进展"

# 通用问答（免费，5次）
python bohrium_chat.py chat --agent default --scene general --message "你好"

# 对话学者（免费）
python bohrium_chat.py chat --agent scholar_clone --scene scholar_QA --message "薛定谔的贡献"

# 综述写作（免费）
python bohrium_chat.py chat --agent writing_assistant --scene writing --message "量子计算综述大纲"

# 专利搜索（免费）
python bohrium_chat.py chat --agent sn_patent --scene patent --message "量子计算专利"
```

## API 端点

| 功能 | 方法 | 路径 |
|---|---|---|
| 列出 Agent | GET | `/bohrapi/v1/sigma-search/api/v3/agent/list` |
| 创建会话 | POST | `/bohrapi/v1/square/question/create` |
| 发送消息 | POST | `/bohrapi/v1/sigma-search/api/v3/session/chat_agent` |
| SSE 流 | GET | `/bohrapi/v1/sigma-search/api/v3/sse/ai_search/v1/{sessionId}/stream` |

- **Base URL**: `https://www.bohrium.com/bohrapi/v1`
- **Auth**: `Authorization: Bearer <brm-token>`

## 可用 Agent 模式

| Agent ID | 名称 | 用途 | 消耗 |
|---|---|---|---|
| `science_navigator` / `sn` | 学术搜索 | 学术文献问答 | 收费 |
| `sn_deep_research` | 深度研究 | 深度调研分析 | 1000光子 |
| `default` | 通用问答 | 日常科研问答 | 免费(5次) |
| `multi_turn` | 文献对话(LitTalk) | 对文献提问 | 收费 |
| `scholar_clone` | 对话学者(ScholarTalk) | 模拟学者对话 | 免费 |
| `knowledge_base` | 知识库对话 | 对知识库提问 | 收费 |
| `writing_assistant` | 帮我写综述 | 综述写作 | 免费 |
| `sn_patent` | 专利搜索 | 专利问答 | 免费 |
| `drawing` | 论文配图助手 | 科研绘图 | 收费 |
| `chemistry_navigator` | 化学导航 | 化学问答 | 1000光子 |

## 模型选择

| 模型 | 说明 | 价格 |
|---|---|---|
| `Auto` | 适合日常科研问答 | 0光子 |
| `Pro` | 比4o更专业的科研模型 | 0光子 |
| `DeepThink` | 推理模型（带思考过程） | 0光子 |

## 消耗说明

- **光子(Photon)**：玻尔平台的虚拟货币单位
- 免费用户有初始额度，超出后需充值
- 收费 Agent 每次对话消耗光子
- 会员可享受更多免费额度

## 触发词

- "列出玻尔Agent" / "玻尔有哪些助手"
- "玻尔学术搜索" / "玻尔查文献"
- "玻尔对话学者" / "玻尔学者问答"
- "玻尔写综述" / "玻尔综述"
- "玻尔专利搜索" / "玻尔查专利"
- "玻尔通用问答" / "玻尔问答"
