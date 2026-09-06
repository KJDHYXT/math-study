# 多阶段构建：前端(Vite) + 后端(FastAPI)，由同一服务同源托管
# ============ 阶段1：构建前端 ============
FROM node:20-alpine AS frontend
WORKDIR /fe
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# ============ 阶段2：Python 运行环境 ============
FROM python:3.13-slim
WORKDIR /app
COPY backend/ /app/backend
RUN pip install --no-cache-dir -r /app/backend/requirements.txt
COPY --from=frontend /fe/dist /app/frontend/dist
WORKDIR /app/backend
ENV PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
