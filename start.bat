@echo off
set "ROOT=%~dp0"
echo [1/2] 启动后端 (FastAPI @ 127.0.0.1:8000) ...
start "math-backend" /D "%ROOT%backend" cmd /k ".venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
echo [2/2] 启动前端 (Vite @ localhost:5173) ...
start "math-frontend" /D "%ROOT%frontend" cmd /k "npm run dev"
timeout /t 6 >nul
start "" "http://localhost:5173"
