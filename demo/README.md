# 24 点 · 单人挑战（账号版）

单人 24 点：前端点牌作答，Java 后端权威判题、计时与结算，PostgreSQL 保存对局与成绩。
支持游客试玩、注册登录、游客成绩并入账号，以及 A/B × L1/L2 四个排行榜。

## 目录

```text
demo/server   Spring Boot 3 + Java 21 + Maven Wrapper
demo/web      Vite + TypeScript + fraction.js
compose.yaml  本地开发用 PostgreSQL 16
compose.prod.yaml / Dockerfile / deploy/   生产部署
docs/         规则、架构与部署手册
```

## 本机已有 PostgreSQL？两条路选一条

数据库连接默认 `jdbc:postgresql://127.0.0.1:55432/game24`，用户名 `game24`，
密码 `game24_local_only`。端口特意用 55432，避开本机其他 PostgreSQL 实例。

### 方式 A：用本机 PostgreSQL（本机已建好独立实例）

本机已有实例数据目录 `C:\Users\cx\pgdata-game24`，端口 55432。启动：

```powershell
$B = 'C:\Users\cx\.pg0\installation\18.1.0\bin'
& "$B\pg_ctl.exe" -D C:\Users\cx\pgdata-game24 -l C:\Users\cx\pgdata-game24\server.log start
```

### 方式 B：用 Docker Compose

```powershell
Copy-Item .env.example .env
docker compose up -d
```

## 启动后端

```powershell
cd demo/server
.\mvnw.cmd spring-boot:run
```

健康检查：<http://127.0.0.1:8080/api/health> 应返回 `{"status":"UP","db":"UP"}`。
首次启动 Flyway 自动执行 V1、V2 迁移。

## 启动前端

```powershell
cd demo/web
npm install
npm run dev
```

打开 <http://127.0.0.1:5173>。Vite 已把 `/api` 代理到 8080。

## 测试

```powershell
cd demo/server
.\mvnw.cmd test          # 规则、题池、求值器（不依赖数据库）
```

集成测试需要真实 PostgreSQL（账号、令牌、排行榜、游客合并）：

```powershell
# 1. 建独立 schema（只需一次）
$env:PGPASSWORD='game24_local_only'
& 'C:\Users\cx\.pg0\installation\18.1.0\bin\psql.exe' -h 127.0.0.1 -p 5432 -U game24 -d game24 \
  -c "CREATE SCHEMA IF NOT EXISTS game24_test AUTHORIZATION game24;"

# 2. 跑集成测试
cd demo/server
.\mvnw.cmd -Pintegration test
```

默认连接 `127.0.0.1:5432/game24?currentSchema=game24_test`；可用
`TEST_DB_URL` / `TEST_DB_USERNAME` / `TEST_DB_PASSWORD` 覆盖。

前端：

```powershell
cd demo/web
npx vitest run          # 合并逻辑 + DOM 点击测试
npm run build           # 类型检查 + 生产构建
```

## 账号与排行榜

- 游客打开即玩，用浏览器随机 `guestId`（请求头 `X-Guest-Id`）隔离数据。
- 注册/登录时前端带上 `guestId`，服务端在同一事务里把该游客的对局、历史、最佳并入账号。
- 只有账号成绩进入排行榜；游客成绩只在本机记录中可见。
- 排行榜四个榜：A/B × L1/L2；每账号每榜只保留一条最佳。A 榜按答对题数，再按第 N 题计榜用时；B 榜按总计榜用时；并列先取得者优先。
- 登录态：Access Token（JWT，30 分钟，`Authorization: Bearer`）+ Refresh Token（HttpOnly Cookie，30 天，每次刷新轮换）。

### API

| 方法与路径 | 说明 |
|---|---|
| `POST /api/auth/register` | 注册，body：username/password/nickname/guestId? |
| `POST /api/auth/login` | 登录，body：username/password/guestId? |
| `POST /api/auth/refresh` | 用 Cookie 换新 access token |
| `POST /api/auth/logout` | 撤销刷新令牌 |
| `GET /api/auth/me` | 当前账号（需 Bearer） |
| `POST /api/games` | 创建对局：requestId/mode/level |
| `GET /api/games/{id}` | 恢复对局（服务端按身份校验归属） |
| `POST /api/games/{id}/submit` | 提交三步操作树 |
| `POST /api/games/{id}/skip` | 跳题并罚时 |
| `POST /api/games/{id}/abandon` | 退出（无效局） |
| `GET /api/records` | 最近历史 + 四个最佳；支持 `mode`、`level` 筛选历史 |
| `GET /api/leaderboard?mode=A&level=L1&page=0&size=20` | 榜单 + 我的排名 |
| `GET /api/leaderboard/me` | 四个榜的我的排名（需 Bearer） |
| `GET /api/health` | 应用与数据库健康 |

### 配置（环境变量）

| 变量 | 默认 | 说明 |
|---|---|---|
| `DB_URL` | `jdbc:postgresql://127.0.0.1:55432/game24` | 数据库地址 |
| `DB_USERNAME` / `DB_PASSWORD` | `game24` / `game24_local_only` | 数据库账号 |
| `JWT_SECRET` | 开发用默认值 | **生产必须覆盖**，≥32 字节 |
| `ACCESS_TTL` / `REFRESH_TTL` | `PT30M` / `P30D` | 令牌有效期 |
| `COOKIE_SECURE` | `false` | HTTPS 生产环境设 `true` |
| `FORWARD_HEADERS_STRATEGY` | `none` | 反向代理后设 `framework` |
| `SERVER_PORT` | `8080` | 应用端口 |

## 题池

L1/L2 共用 1–13 可重复四数，按算符池离线筛选：

| 难度 | 算符 | 可解牌组 |
|---|---|---|
| L1 | + − | 220 |
| L2 | + − × ÷ | 1362 |

候选共 1820 组。重新生成：

```powershell
cd demo/server
.\mvnw.cmd compile exec:java "-Dexec.mainClass=com.game24.puzzle.PuzzleGenerator"
```

## 规则要点

- A 模式：300 秒，答对越多越好；答错 -5s，跳题 -10s。
- B 模式：答对 10 题结束，用时越短越好；答错 +5s，跳题 +10s。
- 合并三次必须用尽四个数字，结果精确等于 24。
- 计时、罚时、判题、结算全部在服务端；对局进行态也持久化，刷新可恢复。

## 上云部署

- 架构与数据库设计：`docs/账号与排行榜_上云架构方案.md`
- 拿到服务器后照做：`docs/上云部署手册.md`
- 当前线上服务器（121.43.236.209）的原生部署记录：`docs/服务器部署记录-121.43.236.209.md`
- 生产拓扑：Caddy（HTTPS）→ Spring Boot（含前端静态文件）→ PostgreSQL（仅内网）
- 一键：`./deploy/deploy.sh`；备份：`deploy/backup.sh`；恢复：`deploy/restore.sh`
