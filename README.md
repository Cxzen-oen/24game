# 24 点 · 单人挑战

一个单人 24 点网页游戏：前端 Vite + TypeScript 单页应用，后端 Spring Boot 3.3.4（Java 21）单体，PostgreSQL 持久化。判题、计时、罚时与结算都在服务端完成；账号体系与 A/B × L1/L2 四个排行榜。

- 演示地址：<http://121.43.236.209:8081>（当前为 HTTP 演示环境，无域名/HTTPS）
- 现状汇报：[`docs/24点单人挑战_现状汇报_2026-11-05.docx`](docs/24点单人挑战_现状汇报_2026-11-05.docx)
- 规则说明：[`docs/24点游戏_单人挑战与排行榜_规则说明.md`](docs/24点游戏_单人挑战与排行榜_规则说明.md)

## 目录

```text
demo/server   Spring Boot 3 + Java 21 + Maven Wrapper
demo/web      Vite + TypeScript + fraction.js
compose.yaml  本地开发用 PostgreSQL 16
Dockerfile / compose.prod.yaml / deploy/   容器化与生产部署资产
docs/         规则、架构、部署记录与现状汇报
design/       界面参考与静态稿
```

## 本地启动

```powershell
# 数据库（二选一）
docker compose up -d
# 或使用本机 PostgreSQL（默认 127.0.0.1:55432/game24）

cd demo/server
.\mvnw.cmd spring-boot:run

cd demo/web
npm install
npm run dev
```

打开 <http://127.0.0.1:5173>。Vite 已将 `/api` 代理到 8080。

## 测试

```powershell
cd demo/server
.\mvnw.cmd test            # 规则、题池、求值器
.\mvnw.cmd -Pintegration test   # 账号/榜单集成测试，需要真实 PostgreSQL

cd demo/web
npx vitest run
npm run build
```

## 现状边界

- 单人玩法，不含实时对战、匹配、房间、观战、回放；不含 L3 扩展算符。
- 线上当前用 systemd 直接跑 jar、PostgreSQL 同机、HTTP，没有 HTTPS、监控告警或防作弊。
- 仓库内是评审阶段的代码与文档，不是对外生产承诺；部署细节见 `docs/服务器部署记录-121.43.236.209.md`。

## 更多

启动方式、API、账号与排行榜、题池与部署说明见 [`demo/README.md`](demo/README.md)。
