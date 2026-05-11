@echo off
chcp 65001 >nul
echo ======================================
echo   Bohrium Skill 安装脚本
echo ======================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.8+
    exit /b 1
)

echo [1/4] 安装 Python 依赖...
pip install -r requirements.txt
if errorlevel 1 (
    echo [错误] 依赖安装失败
    exit /b 1
)

echo [2/4] 安装 Playwright Chromium...
python -m playwright install chromium
if errorlevel 1 (
    echo [警告] Chromium 安装可能失败，稍后请手动运行: python -m playwright install chromium
)

echo [3/4] 注册 MCP Server...
mcporter config add skill-boer --stdio "python %~dp0server.py"
if errorlevel 1 (
    echo [警告] mcporter 注册失败，请检查 mcporter 是否已安装
    echo 手动注册命令:
    echo   mcporter config add skill-boer --stdio "python %~dp0server.py"
) else (
    echo [成功] MCP Server 已注册
)

echo [4/4] 验证安装...
mcporter list skill-boer --schema >nul 2>&1
if errorlevel 1 (
    echo [警告] 无法验证，请手动运行: mcporter list skill-boer --schema
) else (
    echo [成功] 验证通过！
)

echo.
echo ======================================
echo   安装完成！
echo ======================================
echo.
echo 使用方法:
echo   mcporter call skill-boer.bohr_chat message="你的问题" mode="pro"
echo.
echo 或作为 MCP Server 使用
echo.
pause
