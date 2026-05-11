# Bohrium Skill

通过 Edge 浏览器直接访问 Bohrium (玻尔) AI 学术助手，支持快速(Auto)和专业(Pro)模式。

## 特点

- **无需 Token**：复用 Edge 浏览器登录态，自动保持会话
- **模式切换**：支持 Auto（快速）和 Pro（专业）两种模式
- **无损输出**：保留完整 Markdown、LaTeX 公式、代码块
- **自动管理**：自动关闭/启动 Edge，无需手动干预

## 前置条件

1. **Edge 浏览器**：已安装并登录过 Bohrium (https://www.bohrium.com)
2. **Python 依赖**：
   ```bash
   pip install playwright mcp
   python -m playwright install chromium
   ```

## 安装

### 方式 1：自动安装（推荐）

```bash
# Windows
skill-boer\install.bat

# macOS/Linux
bash skill-boer/install.sh
```

### 方式 2：手动注册到 mcporter

```bash
mcporter config add skill-boer --stdio "python C:\Users\wuton\Desktop\deepsearch-boer\skill-boer\server.py"
```

## 可用 Tools

| Tool | 说明 |
|------|------|
| `bohr_chat` | 发送消息到 Bohrium AI，支持模式选择 |
| `bohr_health` | 健康检查 |

### bohr_chat 参数

```json
{
  "message": "量子计算最新进展",  // 必填
  "mode": "pro",                // 可选: "auto"(默认) 或 "pro"
  "agent": "sn"                 // 可选: Agent ID，默认 "sn"
}
```

## 触发词

- "问玻尔"
- "Bohrium 搜索"
- "查文献"
- "学术问答"
- "用 Edge 问 Bohrium"

## 使用示例

### 快速模式（Auto）

```
问玻尔：量子计算最新进展
```

### 专业模式（Pro）

```
用专业模式问玻尔：量子计算最新进展
```

### 深度研究

```
深度研究：大语言模型在材料科学中的应用
```

## 输出格式

返回 JSON 结构：

```json
{
  "success": true,
  "mode": "pro",
  "message": "量子计算最新进展",
  "response": "# 量子计算最新进展\n\n## 1. 超导量子比特\n...\n$$H = \\sum_i \\omega_i \\sigma_z^i$$\n...",
  "url": "https://www.bohrium.com/chat/..."
}
```

## 注意事项

1. **Edge 会被关闭**：调用时会强制关闭所有 Edge 进程，请提前保存工作
2. **首次使用**：确保 Edge 已登录 Bohrium，且保持登录态
3. **超时设置**：默认 180 秒，复杂问题可能需要更长时间
4. **网络要求**：需要能访问 https://www.bohrium.com

## 故障排除

| 问题 | 解决方案 |
|------|---------|
| "Could not find input element" | 页面结构可能已更新，需要更新选择器 |
| "Playwright not installed" | 运行 `pip install playwright` 并安装 Chromium |
| Edge 未关闭导致错误 | 手动关闭 Edge 后重试 |
| 返回内容为空 | AI 可能还在生成中，增加 timeout 参数 |
