# 免费云端部署指南（Neon 数据库 + Render 托管，前后端同源）

> 目标：后端+数据库跑在免费云上，公网稳定访问、数据在云端共享、不依赖本机在线。
> 全程 **0 元**（Neon / Render / GitHub 免费档）。

## 0. 原理
- **数据库**：Neon 免费 **Postgres**（线上共享库）。后端只需 `DATABASE_URL` 指向它。
- **后端 + 前端**：Render 免费 **Web Service**，用项目根 `Dockerfile`（多阶段：先 `npm run build` 构建前端，再跑 FastAPI），**同一服务同源托管**前端与 `/api`，无需 CORS / 无需 VITE_API_BASE。
- 访问：其它设备开 `https://你的服务.onrender.com` → 登录（`ACCESS_TOKEN`）。

---

## 1. 推项目到 GitHub（一次性）
在项目根目录 `D:\deepseek sh\analysis` 打开终端：
```powershell
git init
git add .
git commit -m "init"
# 在 github.com 新建一个私有仓库，然后：
git remote add origin https://github.com/你的用户名/math-study.git
git push -u origin main
```
> `.gitignore` 已排除 `.env`（含密钥）、`math_study.db`、`node_modules`、`dist`、`.venv`、`uploads`，不会上传敏感信息。

## 2. 建 Neon 数据库（免费）
1. 打开 https://neon.tech 注册（免费）。
2. 创建 **Postgres** 项目（地区随意），建好数据库。
3. 复制 **Connection string**，形如：
   ```
   postgresql://user:xxxx@ep-xxx.region.aws.neon.tech/neondb?sslmode=require
   ```
   这就是 `DATABASE_URL`（后端会自动补 `+psycopg` 驱动）。

## 3. 部署到 Render（免费）
1. 打开 https://render.com 注册（免费）。
2. **New → Web Service** → 连接你的 GitHub 仓库。
3. **Environment: Docker**（它会自动用仓库根目录的 `Dockerfile`）。
4. **Instance Type: Free**。
5. **Environment Variables**（在部署前加好）：
   | Key | Value |
   |---|---|
   | `DATABASE_URL` | 上面 Neon 的连接串 |
   | `AUTH_ENABLED` | `true` |
   | `ACCESS_TOKEN` | 你的访问口令（自定义，务必改） |
   | `LLM_API_KEY` | 你的 DeepSeek 密钥（图片提取用；`sk-42…`） |
   | `UPLOAD_DIR` | `uploads` |
   > 可选：`LLM_BASE_URL=https://api.deepseek.com`、`LLM_MODEL=deepseek-v4-flash-vision-exp`。
6. 点 **Create/Deploy**，等构建完成（首次约几分钟）。
7. 部署成功后，服务地址形如 `https://math-study.onrender.com`。

## 4. 使用
- 本机 / 另一台设备：浏览器打开 **`https://math-study.onrender.com`** → 登录页输入 **`ACCESS_TOKEN`** → 使用。
- 数据都在 Neon（云端），多处登录共享同一份，改动即同步。

---

## 注意事项
- **免费档休眠**：Render 免费服务闲置 15 分钟后休眠，访问时**冷启动几秒**，属正常。
- **上传的图片**：`uploads/` 在免费 Render 上是**临时磁盘**，重启/重新部署会丢失图片文件（数据库内容不丢）。如要长期保存图片，后续可改用云存储（超出本版范围）。
- **已有本地数据**：如需把本地 SQLite 数据搬到云端，需额外迁移脚本（本版每次全新部署会重新建表+示例数据）。可后续做。
- **安全**：`ACCESS_TOKEN` 直接用你自己的口令；公网开启鉴权。
- **成本**：Neon 免费档（0.5GB）/ Render 免费 Web Service / GitHub 免费，均 0 元。

## 还可以
- 若想彻底不管"免费档冷启动"，可换成 Render 付费档（非必须）。
- 也可把前端单独放 Vercel/Netlify 免费静态托管、后端在 Render，用 `VITE_API_BASE` 指向后端（需开 CORS）。当前方案已同源，最省事。
