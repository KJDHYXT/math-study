# 免费云端部署 · Koyeb 版（免绑卡）

> 原理：**Neon** 存数据（线上 Postgres），**Koyeb** 免费档托管后端+前端（用仓库根 `Dockerfile` 同源构建，免卡）。
> 全程 0 元、不用家里电脑在线。访问 `https://你的服务.koyeb.app` → 登录 → 云端共享库。

## 0. 已就绪
- GitHub 仓库 `KJDHYXT/math-study`（已推送，含 `Dockerfile`、`render.yaml`、`DEPLOY.md`）。
- Neon 数据库 `math-stud` 已建好并初始化（上文已测通 `postgresql://…`）。

## 1. 注册 Koyeb（免费、免绑卡）
- 打开 https://app.koyeb.com 注册（推荐用 **GitHub** 直接登录）。

## 2. 从 GitHub 建服务
1. Dashboard → **Create Service**。
2. **Source** 选 **GitHub** → 授权并连接你的 `math-study` 仓库。
3. **Builder**：选 **Dockerfile**（自动用仓库根 `Dockerfile`：先 `npm run build` 构建前端，再跑 FastAPI）。
4. 服务名：`math-study`（任意）。
5. 端口：Koyeb 会注入 `PORT` 环境变量，Dockerfile 里已用 `${PORT:-8000}` 监听，无需手动改。

## 3. 环境变量（必填）
在服务配置的 **Environment variables** 添加：
| KEY | VALUE |
|---|---|
| `DATABASE_URL` | `postgresql://neondb_owner:npg_JyAbaSx9OC1n@ep-square-flower-ae9km8ch-pooler.c-2.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require` |
| `AUTH_ENABLED` | `true` |
| `ACCESS_TOKEN` | 你的登录口令（自定义，如 `Mathyx2026@study`，登录用） |
| `LLM_API_KEY` | `sk-42b7d433c741451ebbb4dcd6959a4bca`（图片提取） |
| `UPLOAD_DIR` | `uploads` |

## 4. 部署
- 点 **Create Service** → 构建（几分钟）→ 完成后会得到公网地址：
  ```
  https://math-study-你的koyeb用户名.koyeb.app
  ```

## 5. 使用
- 其它设备打开上面的 URL → 登录页输入 **`ACCESS_TOKEN`** → 使用。
- 数据在 **Neon**（云端），多处登录共享同一份、改动即同步。

## 注意事项
- Koyeb Hobby（免费）服务在闲置后会**休眠**，访问时**冷启动几秒**正常。
- 上传的**题目图片**（`uploads/`）在免费档是临时磁盘，重启/重部署会丢图片文件（**数据库内容不丢**）。
- 连接串/密钥只放 Koyeb 环境变量与本地 `.env`，**别提交仓库**（已 `.gitignore`）。

## 其它
- 若想用 GitHub Actions 每次 push 自动部署，可再加 `koyeb-action`（可选，更进阶）。
- 之前 Cloudflare/ngrok 的本地隧道是"本机在线"方案，仍可用作临时演示；云端部署是长期方案。
