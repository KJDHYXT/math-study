@echo off
rem 一键(本机在线)跨公网访问 - ngrok 版
cd /d "%~dp0"

set "NGROK="
where ngrok >nul 2>nul && set "NGROK=ngrok"
if not defined NGROK if exist "ngrok.exe" set "NGROK=ngrok.exe"
if not defined NGROK if exist "ngrok-v3.exe" set "NGROK=ngrok-v3.exe"

netstat -ano | findstr ":8000 " | findstr "LISTENING" >nul 2>nul
if errorlevel 1 start "math-backend" cmd /k "cd /d backend && .venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000"

netstat -ano | findstr ":5173 " | findstr "LISTENING" >nul 2>nul
if errorlevel 1 start "math-frontend" cmd /k "cd /d frontend && npm run dev"

if not defined NGROK (
  echo [提示] 未找到 ngrok。请下载 ngrok.exe 放到本目录: https://ngrok.com/download
  echo 首次使用需配置令牌:  ngrok config add-authtoken 你的token
  pause
  exit /b 1
)

echo 等待就绪, 开启 ngrok 隧道 ...
timeout /t 8 >nul
echo ============================================================
echo  公网访问地址(发到其它设备浏览器打开):  形如 https://xxx.ngrok-free.app
echo.
"%NGROK%" http 5173
pause
