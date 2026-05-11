# -*- coding: utf-8 -*-
"""
Bohrium Edge Browser Client - 极简稳定版
只负责：填入问题 → 点击发送 → 提取最新回复
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import json
import os
import time
import subprocess
from typing import Dict, Any

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
EDGE_USER_DATA = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\User Data")
BOHRIUM_URL = "https://www.bohrium.com"


class BohriumClient:
    def __init__(self, timeout: int = 180, headless: bool = True):
        self.timeout = timeout
        self.headless = headless
        self._playwright = None
        self._context = None
        self._page = None

    @staticmethod
    def _kill_edge():
        try:
            subprocess.run(["taskkill", "/F", "/IM", "msedge.exe"], capture_output=True, timeout=10)
            time.sleep(2)
        except:
            pass

    def _launch_browser(self):
        if not sync_playwright:
            raise RuntimeError("Playwright not installed")
        self._playwright = sync_playwright().start()
        if os.path.exists(EDGE_USER_DATA):
            self._context = self._playwright.chromium.launch_persistent_context(
                EDGE_USER_DATA,
                executable_path=EDGE_PATH,
                headless=self.headless,
                viewport={"width": 1456, "height": 819},
                args=["--disable-blink-features=AutomationControlled", "--no-first-run", "--disable-infobars"]
            )
        else:
            browser = self._playwright.chromium.launch(executable_path=EDGE_PATH, headless=self.headless)
            self._context = browser.new_context(viewport={"width": 1456, "height": 819})
        self._page = self._context.new_page()

    def _close_browser(self):
        if self._page:
            self._page.close()
        if self._context:
            self._context.close()
        if self._playwright:
            self._playwright.stop()
        self._page = None
        self._context = None
        self._playwright = None

    def _get_page_text(self) -> str:
        try:
            return self._page.evaluate("() => document.body.innerText")
        except:
            return ""

    def chat(self, message: str) -> Dict[str, Any]:
        try:
            self._kill_edge()
            self._launch_browser()
            self._page.goto(BOHRIUM_URL, timeout=self.timeout * 1000, wait_until="domcontentloaded")
            time.sleep(5)

            before_text = self._get_page_text()

            input_found = False
            for selector in ["span[contenteditable='true']", "div[contenteditable='true']", "[contenteditable='true']"]:
                elements = self._page.query_selector_all(selector)
                for inp in elements:
                    try:
                        if inp.is_visible():
                            inp.click()
                            time.sleep(0.5)
                            inp.fill(message)
                            input_found = True
                            break
                    except:
                        continue
                if input_found:
                    break

            if not input_found:
                return {"success": False, "error": "找不到输入框"}

            sent = False
            buttons = self._page.query_selector_all("button")
            for btn in buttons:
                try:
                    box = btn.bounding_box()
                    if box and box['x'] > 1100 and box['y'] > 450:
                        btn.click()
                        sent = True
                        break
                except:
                    continue

            if not sent:
                self._page.keyboard.press("Enter")

            time.sleep(10)
            check_interval = 3
            waited = 10
            last_text = ""
            stable_count = 0

            while waited < self.timeout:
                try:
                    loading = self._page.query_selector("[class*='loading'], [class*='spinner']")
                    if not loading:
                        current_text = self._get_page_text()
                        if current_text == last_text:
                            stable_count += 1
                            if stable_count >= 2:
                                break
                        else:
                            stable_count = 0
                            last_text = current_text
                except:
                    pass
                time.sleep(check_interval)
                waited += check_interval

            after_text = self._get_page_text()
            response = ""
            
            if after_text and before_text:
                if len(after_text) > len(before_text):
                    before_lines = set(before_text.split('\n'))
                    after_lines = after_text.split('\n')
                    new_lines = []
                    for line in after_lines:
                        line = line.strip()
                        if line and line not in before_lines and len(line) > 20:
                            new_lines.append(line)
                    response = '\n'.join(new_lines)
                else:
                    response = after_text
            else:
                response = after_text

            if response:
                lines = response.split('\n')
                cleaned = []
                for line in lines:
                    line = line.strip()
                    if len(line) < 10:
                        continue
                    if any(kw in line for kw in ['用户服务协议', '隐私政策', '京公网安备', '营业执照', '新对话', '站内搜索']):
                        continue
                    cleaned.append(line)
                response = '\n'.join(cleaned)

            return {
                "success": True,
                "message": message,
                "response": response,
            }

        except Exception as e:
            import traceback
            return {"success": False, "error": str(e), "traceback": traceback.format_exc()}
        finally:
            self._close_browser()


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["chat"])
    parser.add_argument("--message", "-m", required=True)
    parser.add_argument("--headless", action="store_true")
    args = parser.parse_args()

    client = BohriumClient(headless=args.headless)
    result = client.chat(args.message)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
