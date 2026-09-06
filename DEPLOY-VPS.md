# 免费云端部署 · VPS 版（自托管，最稳）

> 原理：**Neon** 存数据（线上 Postgres），**VPS** 用 Docker 跑这个应用（前后端同源），绑定公网 IP 可跨公网访问。
> 你已接受的**低价 VPS**（几元/月）能彻底避免"免费托管要卡/被墙/坏"的问题。

## 0. 已就绪
- GitHub 仓库 `KJDHYXT/math-study`（含 `Dockerfile`、`docker-compose.yml`、`deploy-vps.sh`、`render.yaml`、`DEPLOY*.md`）。
- Neon 数据库 `math-stud` 已建好并初始化（`DATABASE_URL` 已测通）。

## 1. 买一台便宜 VPS
给你几张免卡、国内能访问、便宜的选择（价格供参考）：
| 服务商 | 参考价 | 说明 |
|---|---|---|
| **RackNerd** | ~$10–15/年(≈¥6–9/月) | 最便宜，美国加州节点；国内可访问，但延迟略高 |
| **搬瓦工(BandwagonHost)** | ~$15–30/年 | CN2/香港线路对国内友好，延迟低（稍贵） |
| **Vultr / DigitalOcean** | ~$3.5–6/月 | 香港/东京节点，延迟低，价格偏高 |

买最低配（1 核/1GB RAM/20GB）即可，**系统选 Ubuntu 22.04/24.04**。买完记下：**IP、root 密码**。

## 2. 连上 VPS
用 **SSH**（Windows 自带 `ssh`）：
```powershell
ssh root@你的VPS_IP
```
输入密码登录。

## 3. 装 Docker（一条命令）
```bash
curl -fsSL https://get.docker.com | sh
```

## 4. 部署
在 VPS 上运行（会用仓库里的 `deploy-vps.sh`）：
```bash
bash deploy-vps.sh
```
它会：克隆仓库 → 生成 `.env` → 让你补 `DATABASE_URL / ACCESS_TOKEN / LLM_API_KEY` → `docker compose up -d --build`（构建前端+后端，端口 80→8000）。完成后打印 **公网 IP 地址**。

> 若 `.env` 补过想重新应用，再跑一次 `bash deploy-vps.sh` 即可（会拉取最新代码并重建）。

## 5. 使用
- 其它设备打开 **`http://你的VPS_IP`** → 登录页输入 **`ACCESS_TOKEN`** → 使用。
- 数据在 **Neon**（云端），多处登录共享同一份、改动即同步。

## 常用（VPS 上）
```bash
docker compose logs -f      # 看日志
docker compose down         # 停
docker compose up -d        # 起
```

## 注意事项
- **防火墙**：VPS 服务商的安全组/防火墙要放行 **80** 端口，否则访问不通。
- **HTTPS**：先用 `http://IP`；后续想 https 可加域名+Let's Encrypt（我用 Caddy/Nginx 可帮你配）。
- **备份**：数据都在 Neon（自带备份）；VPS 只是应用层，坏了大不了重建。
- `.env`（含 DATABASE_URL/密钥）只留在 VPS 上，**别提交仓库**（已 `.gitignore`）。
