import json
import os
import re
import time
from typing import Optional, Dict, Any

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    sync_playwright = None
    PlaywrightTimeout = Exception

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
EDGE_USER_DATA = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\User Data")


class BohriumBrowserChat:
    """通过 Playwright 直接控制 Edge 浏览器访问 Bohrium AI"""

    def __init__(self, timeout: int = 120, headless: bool = False):
        self.timeout = timeout
        self.headless = headless
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None

    def _launch_browser(self):
        """启动 Edge 浏览器"""
        if not sync_playwright:
            raise RuntimeError("Playwright not installed. Run: pip install playwright")
        
        self._playwright = sync_playwright().start()
        
        # 使用 Edge 的可执行文件和用户数据目录
        # 这样可以保持登录态
        launch_options = {
            "executable_path": EDGE_PATH,
            "headless": self.headless,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--no-first-run",
                "--no-default-browser-check",
            ]
        }
        
        # 如果有 Edge 用户数据，使用 persistent context 保持登录态
        if os.path.exists(EDGE_USER_DATA):
            self._context = self._playwright.chromium.launch_persistent_context(
                EDGE_USER_DATA,
                **launch_options
            )
            self._browser = None  # persistent_context 返回的就是 browser context
        else:
            self._browser = self._playwright.chromium.launch(**launch_options)
            self._context = self._browser.new_context(
                viewport={"width": 1456, "height": 819},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.0 Edg/120.0.0.0"
            )
        
        self._page = self._context.new_page()

    def _close_browser(self):
        """关闭浏览器"""
        if self._context:
            self._context.close()
            self._context = None
        if self._browser:
            self._browser.close()
            self._browser = None
        if self._playwright:
            self._playwright.stop()
            self._playwright = None
        self._page = None

    def _navigate(self, url: str):
        """导航到指定页面"""
        if not self._page:
            self._launch_browser()
        self._page.goto(url, timeout=self.timeout * 1000, wait_until="networkidle")

    def _wait_for_response(self, timeout: int = None):
        """等待 AI 回复完成"""
        if not timeout:
            timeout = self.timeout
        
        # Bohrium 的 AI 回复通常有特定的 DOM 变化
        # 等待加载指示器消失或回复内容稳定
        try:
            # 等待一段时间让 AI 开始回复
            time.sleep(2)
            
            # 检查是否有加载中的指示器
            max_wait = timeout
            waited = 0
            check_interval = 2
            
            while waited < max_wait:
                # 检查页面是否有 loading 指示器
                loading = self._page.query_selector("[class*='loading'], [class*='spinner'], [class*='skeleton']")
                if not loading:
                    # 再等待一下确保内容已完全渲染
                    time.sleep(3)
                    break
                time.sleep(check_interval)
                waited += check_interval
            
            return True
        except Exception as e:
            return False

    def _extract_content(self) -> str:
        """从页面提取 Markdown 格式的回复内容"""
        if not self._page:
            return ""
        
        # 尝试多种可能的 DOM 结构
        # Bohrium 的聊天界面可能使用不同的类名
        selectors = [
            # Markdown 内容区域
            ".markdown-body",
            "[class*='markdown']",
            "[class*='message-content']",
            "[class*='chat-message']",
            "[class*='answer']",
            "[class*='response']",
            # 更通用的选择器
            "article",
            ".prose",
            # 最后的兜底
            "main",
        ]
        
        for selector in selectors:
            try:
                elements = self._page.query_selector_all(selector)
                if elements:
                    # 获取最后一个元素的文本（通常是最新的回复）
                    texts = []
                    for el in elements:
                        text = el.inner_text()
                        if text and len(text.strip()) > 50:  # 过滤掉太短的片段
                            texts.append(text.strip())
                    if texts:
                        # 返回最长的文本（最可能是完整回复）
                        return max(texts, key=len)
            except:
                continue
        
        # 如果都找不到，返回页面可见文本
        try:
            return self._page.inner_text("body")
        except:
            return ""

    def _switch_mode(self, mode: str):
        """切换快速/专业模式"""
        if not self._page:
            return
        
        mode_map = {
            "fast": ["Auto", "快速", "auto"],
            "pro": ["Pro", "专业", "pro"],
        }
        keywords = mode_map.get(mode, [mode])
        
        # 查找模式切换按钮
        buttons = self._page.query_selector_all("button, [role='button'], .tab, [class*='mode']")
        for btn in buttons:
            try:
                text = btn.inner_text().strip()
                for kw in keywords:
                    if kw.lower() in text.lower():
                        btn.click()
                        time.sleep(1)
                        return True
            except:
                continue
        
        return False

    def chat(self, message: str, mode: str = "fast",
             agent_id: str = "sn", scene: str = "paper") -> Dict[str, Any]:
        """
        通过 Edge 浏览器与 Bohrium AI 对话

        Args:
            message: 用户消息
            mode: "fast" (Auto/快速) 或 "pro" (Pro/专业)
        """
        try:
            # 1. 导航到 Bohrium
            self._navigate("https://www.bohrium.com")
            time.sleep(3)  # 等待页面加载
            
            # 2. 查找输入框并输入消息
            input_selectors = [
                "textarea[placeholder]",
                "input[placeholder]",
                "[contenteditable]",
                "textarea",
                "input[type='text']",
            ]
            
            input_found = False
            for selector in input_selectors:
                try:
                    input_el = self._page.query_selector(selector)
                    if input_el:
                        input_el.fill(message)
                        input_found = True
                        break
                except:
                    continue
            
            if not input_found:
                return {
                    "success": False,
                    "error": "Could not find input element on the page",
                    "url": self._page.url if self._page else "",
                }
            
            # 3. 切换模式（如果需要）
            if mode != "fast":
                self._switch_mode(mode)
            
            # 4. 发送消息
            # 尝试点击发送按钮或按 Enter
            send_selectors = [
                "button[type='submit']",
                "[class*='send']",
                "[class*='submit']",
            ]
            
            sent = False
            for selector in send_selectors:
                try:
                    btn = self._page.query_selector(selector)
                    if btn:
                        btn.click()
                        sent = True
                        break
                except:
                    continue
            
            if not sent:
                # 尝试按 Enter
                self._page.keyboard.press("Enter")
                sent = True
            
            # 5. 等待回复
            self._wait_for_response()
            
            # 6. 提取内容
            content = self._extract_content()
            
            return {
                "success": True,
                "mode": mode,
                "message": message,
                "response": content,
                "url": self._page.url if self._page else "",
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "mode": mode,
                "message": message,
            }
        finally:
            self._close_browser()

    def deep_research(self, topic: str, mode: str = "pro") -> Dict[str, Any]:
        """深度研究模式"""
        return self.chat(topic, mode=mode)

    def list_agents(self) -> Dict[str, Any]:
        """列出可用的 AI Agent"""
        try:
            self._navigate("https://www.bohrium.com")
            time.sleep(3)
            content = self._extract_content()
            return {
                "success": True,
                "response": content,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
        finally:
            self._close_browser()


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Bohrium Edge Browser AI Chat")
    parser.add_argument("action", choices=["chat", "research", "list"],
                        help="Action to perform")
    parser.add_argument("--message", "-m", help="Message to send")
    parser.add_argument("--mode", choices=["fast", "pro"], default="fast",
                        help="Mode: fast(Auto) or pro(Pro)")
    parser.add_argument("--topic", "-t", help="Research topic")
    parser.add_argument("--headless", action="store_true",
                        help="Run in headless mode")
    parser.add_argument("--timeout", type=int, default=120,
                        help="Browser automation timeout in seconds")
    args = parser.parse_args()

    chat = BohriumBrowserChat(timeout=args.timeout, headless=args.headless)

    if args.action == "chat":
        if not args.message:
            print("Error: --message is required for chat")
            return
        result = chat.chat(args.message, args.mode)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.action == "research":
        if not args.topic:
            print("Error: --topic is required for research")
            return
        result = chat.deep_research(args.topic, args.mode)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.action == "list":
        result = chat.list_agents()
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
