# Bohrium (玻尔) Skill

通过 Edge 浏览器自动访问 Bohrium AI 学术助手，填入问题并收集 AI 回复。

## 功能

- **自动打开玻尔**：通过 Edge 浏览器访问 https://www.bohrium.com
- **自动填入问题**：定位输入框，填入用户消息
- **自动发送**：点击发送按钮
- **收集回复**：等待 AI 生成完成，提取最新回复内容
- **复用登录态**：自动复用 Edge 浏览器的登录状态，无需额外 Token

## 前置条件

1. **Edge 浏览器**：已安装并登录过 Bohrium (https://www.bohrium.com)
2. **Python 3.8+**
3. **Python 依赖**：
   ```bash
   pip install playwright mcp
   python -m playwright install chromium
   ```

## 安装

### 方式 1：自动安装（Windows）

```bash
skill-boer\install.bat
```

### 方式 2：手动注册到 mcporter

```bash
mcporter config add skill-boer --stdio "python C:\Users\wuton\Desktop\deepsearch-boer\skill-boer\server.py"
```

## 可用工具

| 工具 | 说明 |
|------|------|
| `bohr_chat` | 发送消息到 Bohrium AI，返回 AI 回复 |

### bohr_chat 参数

```json
{
  "message": "量子计算最新进展"  // 必填，要问的问题
}
```

## 触发词

- "问玻尔"
- "Bohrium 搜索"
- "查文献"
- "学术问答"
- "用玻尔查"

## 使用示例

### 命令行调用

```bash
mcporter call skill-boer.bohr_chat --message "量子计算最新进展"
```

### 作为 MCP Server

在支持 MCP 的客户端中直接调用：

```json
{
  "name": "bohr_chat",
  "arguments": {
    "message": "介绍一下 Transformer 架构"
  }
}
```

## 输出格式

返回 JSON 结构：

```json
{
  "success": true,
  "message": "量子计算最新进展",
  "response": "量子计算是..."
}
```

如果失败：

```json
{
  "success": false,
  "error": "错误信息",
  "traceback": "详细堆栈..."
}
```

## 工作原理

1. **强制关闭 Edge**：调用 `taskkill /F /IM msedge.exe` 确保 User Data 不被占用
2. **复用 User Data**：通过 Playwright 的 `launch_persistent_context` 启动 Edge，复用已有登录态
3. **访问页面**：打开 https://www.bohrium.com
4. **填入问题**：查找 `contenteditable` 输入框，填入消息
5. **点击发送**：定位右下角发送按钮并点击
6. **等待回复**：
   - 最少等待 10 秒
   - 检测 loading/spinner 元素是否消失
   - 连续 2 次内容稳定视为生成完成
7. **提取回复**：
   - 对比发送前后的页面文本
   - 提取新增的行内容
   - 过滤噪声（用户服务协议、隐私政策等）
8. **关闭浏览器**：清理资源

## 注意事项

1. **Edge 会被强制关闭**：调用时会关闭所有 Edge 进程，请提前保存工作
2. **首次使用**：确保 Edge 已登录 Bohrium，且保持登录态
3. **超时设置**：默认 180 秒，复杂问题可能需要更长时间
4. **网络要求**：需要能访问 https://www.bohrium.com
5. **窗口大小**：视口固定为 1456x819，确保页面元素位置稳定

## 故障排除

| 问题 | 解决方案 |
|------|---------|
| "找不到输入框" | 页面结构可能已更新，需要更新 `bohrium_client.py` 中的选择器 |
| "Playwright not installed" | 运行 `pip install playwright` 并安装 Chromium |
| Edge 未关闭导致错误 | 手动关闭 Edge 后重试 |
| 返回内容为空 | AI 可能还在生成中，检查网络连接或增加 timeout |
| 发送按钮点错 | 检查视口大小是否为 1456x819 |

## 文件结构

```
skill-boer/
├── bohrium_client.py   # 核心浏览器控制逻辑
├── server.py           # MCP stdio server
├── requirements.txt    # Python 依赖
├── install.bat         # Windows 安装脚本
└── SKILL.md            # 本文件
```

## 技术细节

- **浏览器**：Microsoft Edge (Chromium)
- **浏览器路径**：`C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe`
- **User Data**：`%LOCALAPPDATA%\Microsoft\Edge\User Data`
- **自动化框架**：Playwright (sync API)
- **通信协议**：MCP (Model Context Protocol) stdio
