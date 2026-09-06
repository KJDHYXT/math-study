#!/bin/bash
# 在 VPS 上一键部署：克隆仓库 -> 写 .env -> docker compose 构建并启动
# 用法: bash deploy-vps.sh   （需要已装 Docker + Docker Compose）
set -e

REPO="https://github.com/KJDHYXT/math-study.git"
APP="math-study"

echo "== pull repo =="
if [ -d "$APP/.git" ]; then
  (cd "$APP" && git pull --quiet)
else
  git clone --quiet "$REPO" "$APP"
fi
cd "$APP"

# 生成 .env（若不存在）
if [ ! -f .env ]; then
  cat > .env <<'EOF'
AUTH_ENABLED=true
UPLOAD_DIR=uploads
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-v4-flash-vision-exp
EOF
  echo ""
  echo "已生成 $PWD/.env，请现在打开它，补上这三项："
  echo "  DATABASE_URL=postgresql://neondb_owner:...@.../neondb?sslmode=require"
  echo "  ACCESS_TOKEN=你的登录口令"
  echo "  LLM_API_KEY=你的DeepSeek密钥"
  read -p "补好后按回车继续..." _
fi

echo "== build & up =="
docker compose up -d --build

IP=$(hostname -I 2>/dev/null | awk '{print $1}')
echo ""
echo "✅ 部署完成！"
echo "   访问:  http://${IP:-<服务器IP>}   登录口令 = ACCESS_TOKEN"
