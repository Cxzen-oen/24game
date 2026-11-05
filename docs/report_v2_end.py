from report_v2_base import *

# ---------------- chapter 7 ----------------
h1("六、", "部署与运行现状")
h2("6.1", "本地开发")
table_caption("表 6-1  本地启动")
table(
    ["组件", "端口/命令", "说明"],
    [
        ("数据库", "docker compose up -d；或本机 PG 18.1 :55432", "compose 用 postgres:16；本机实例数据目录在 C:\\Users\\cx\\pgdata-game24"),
        ("后端", "cd demo/server；.\\mvnw.cmd spring-boot:run", "Flyway 启动时自动执行 V1、V2"),
        ("前端", "cd demo/web；npm install；npm run dev", "Vite :5173，/api 代理到 :8080"),
        ("健康检查", "GET http://127.0.0.1:8080/api/health", "期望 {\"status\":\"UP\",\"db\":\"UP\"}"),
        ("测试", "mvnw test；mvnw -Pintegration test；npx vitest run", "集成测试需要真实 PostgreSQL"),
        ("构建", "npm run build", "tsc --noEmit + vite build → dist"),
    ],
    [2.4, 7.0, 7.2],
    font_size=8.4,
    header_size=8.4,
    first_col_bold=True,
)

h2("6.2", "线上环境")
table_caption("表 6-2  当前线上部署（据部署记录与本次只读复核）")
table(
    ["项目", "现状"],
    [
        ("地址", "http://121.43.236.209:8081（公网；无域名、无 HTTPS）"),
        ("主机", "阿里云 ECS，Ubuntu 22.04.5 LTS；2 vCPU / 1,608 MB 内存 / 4 GB swap / 40 GB 磁盘"),
        ("Java", "OpenJDK 21.0.12.1（JRE headless）"),
        ("数据库", "PostgreSQL 14.24，同机 127.0.0.1:5432；只监听本机"),
        ("应用目录", "/opt/game24；game24-demo.jar + game24.env（600 权限）"),
        ("服务", "systemd game24.service；-Xms128m -Xmx384m；MaxMetaspace 128m；SerialGC"),
        ("反向代理", "无；Spring Boot 直接提供页面、静态资源与 /api"),
        ("备份", "root crontab 03:00 执行 pg_dump -Fc + gzip；保留 14 天；备份在本机"),
        ("容器", "服务器未安装 Docker；仓库内 Dockerfile / compose.prod / Caddyfile 未在该机启用"),
        ("资源占用", "部署记录：app RSS 约 236 MB；整机 used 约 858 MB，available 约 545 MB；swap 未使用"),
    ],
    [3.0, 13.6],
    font_size=8.6,
    header_size=8.6,
    first_col_bold=True,
)
para("部署记录同时写明：服务器上还有 teacher-student（:8000）和 review-tool（:7860）两个旧服务；80/443 未监听，ufw 未启用，公网通过安全组开放 22/8081。")

h2("6.3", "本次只读复核")
para("2026-11-05 18:47（Asia/Shanghai）对线上做了三项只读检查，结果如下：")
bullet("GET /api/health → 200，body 为 {\"status\":\"UP\",\"db\":\"UP\"}，serverTime 为 UTC。", "健康检查：")
bullet("GET / → 200；首页引用的构建产物为 index-CWCsHfd7.js 与 index-tZ_tH9Cq.css，与本地 demo/web/dist 一致。", "首页：")
bullet("GET /api/leaderboard?mode=A&level=L1&page=0&size=1 → total=10；第一名 *算王，28 题，计榜用时 215,000 ms。", "榜单：")
para("这些只说明服务在跑、静态资源是同一份构建，不说明功能与数据都正确。这次只读复核没有做注册、登录、建局、提交、跳题或任何写操作；后续另做了只读负载（见 8.2），仍没有向线上写入。", 9.5, False, GREY)

h2("6.4", "构建与发布")
num_item(1, "本地执行 deploy/build-local.ps1，在独立的 .build/server 目录构建，避免和本机 8080 的旧 jar 抢文件；产物为 deploy/build/game24-demo.jar。")
num_item(2, "scp 到 root@121.43.236.209:/opt/game24/game24-demo.jar。")
num_item(3, "chown game24:game24，然后 systemctl restart game24。")
num_item(4, "curl http://127.0.0.1:8081/api/health，并用 journalctl -u game24 -n 30 查看启动日志。")
num_item(5, "Flyway 在启动时自动执行未应用的迁移；升级前建议先跑 /opt/game24/backup-native.sh。")
para("没有蓝绿发布、没有版本化制品仓库、没有一键回滚；回滚需要保留旧 jar 手工替换并重启。")

h2("6.5", "已准备但未启用的容器化资产")
bullet("多阶段构建：Node 22 构建前端 → Maven 3.9 + Temurin 21 构建后端，把 dist 拷进 src/main/resources/static；运行时 Temurin 21 JRE alpine，非 root 用户。", "Dockerfile：")
bullet("compose.prod.yaml：PostgreSQL 16 + app + Caddy 2；有 healthcheck、mem_limit、日志轮转、卷；数据库不映射宿主机端口。", "compose：")
bullet("deploy/Caddyfile、Caddyfile.ip、deploy.sh、backup.sh、restore.sh、server-init.sh、server-setup-2c2g.sh 等脚本。", "其他：")
para("这些资产与当前线上原生部署并存。评审时请以 6.2 为准，不要误认为 Caddy 或 Docker 已在现网启用。")

h2("6.6", "运维与安全边界")
bullet("journalctl 看应用日志；/api/health 做探活；cron 做每日备份。没有 Prometheus/Grafana、Sentry、告警或日志聚合。", "可观测性：")
bullet("数据库只监听 127.0.0.1；JWT/数据库密码在 600 权限的 env 文件；没有密钥管理服务。", "边界：")
bullet("当前 HTTP；refresh cookie 会明文传输；COOKIE_SECURE=false；登录密码也在请求体明文。正式使用前必须补 HTTPS。", "传输：")
bullet("没有防作弊判定、没有管理后台、没有 WAF；应用层只对登录/注册有限流。", "防护：")
bullet("没有域名、ICP 备案、隐私政策/用户协议；演示账号使用了弱口令（详见部署记录第 11 节）。", "合规：")

# ---------------- chapter 8 ----------------
h1("七、", "现状风险与待确认")
para("以下是我们自己看到的实现风险与工程缺口，不作为优先级结论；请团队判断哪些必须先处理。")

h2("7.1", "技术风险")
table_caption("表 7-1  我们看到的实现风险（按现象记录，未按严重度排序）")
table(
    ["编号", "现象", "证据", "影响", "当前兜底"],
    [
        ("R1", "A 模式“跳题导致到期”时重复结算：skip 先 finish(after)，再 advance(..., after)，after 仍是 RUNNING 且 deadline 已过，advance 再次 finish；game_results.game_id 唯一，第二次插入冲突，事务回滚，接口 500",
         "GameService.java:192–194、307–317；V1 game_results.game_id UNIQUE",
         "用户看到“跳题失败”；依赖前端 sync GET 再结算；日志与错误码不干净",
         "前端 catch 后 sync()；未修"),
        ("R2", "截止后提交：checkNotExpired 在事务内先 finish 再 throw，异常导致整个事务回滚；提交返回 409，但这次 finish 不落库",
         "GameService.java:127、180、398–403",
         "结算依赖后续 GET；如果客户端不重试，A 局可能停在 RUNNING",
         "timeUp 轮询 GET；用户刷新"),
        ("R3", "刷新/关闭页面丢局：前端没有持久化 gameId；B 局没有后台超时归档；关闭页面后对局可能长期 RUNNING",
         "main.ts 全局 game；render() 重置为 home；无定时任务",
         "用户丢进度；DB 出现孤儿 RUNNING 局；统计偏差",
         "无"),
        ("R4", "线上无 HTTPS：refresh cookie 明文传输；COOKIE_SECURE=false；登录密码也在请求体明文",
         "部署记录 §8；application.yml",
         "不适合真实用户；只适合演示/可信小范围",
         "无"),
        ("R5", "无防作弊：服务端判题正确，但不阻止脚本/求解器；提交没有频率限制；账号可批量注册",
         "无 game action 级限流；AuthRateLimiter 只管 auth",
         "榜单可被脚本刷；成绩不能代表真人水平",
         "无"),
        ("R6", "单实例：限流在 JVM 内存；应用单进程；数据库同机；重启后限流清零",
         "AuthRateLimiter 的 ConcurrentHashMap；单 systemd 服务",
         "不能水平扩展；限流可绕过；DB 与应用争抢资源",
         "无"),
        ("R7", "时间显示 UTC：成绩/榜单直接截取 ISO 字符串；服务端 Instant 为 UTC，本地为 +8",
         "main.ts:855、889；Jackson UTC",
         "时间早 8 小时；跨日日期可能显示错",
         "无"),
        ("R8", "“新纪录”是启发式：结算后拉 records，比较最佳与本次 scoring；平纪录也可能显示新纪录",
         "main.ts:744–758",
         "展示层误报；不影响数据库",
         "无"),
        ("R9", "题池重置冲突：openNextPuzzle 重洗后 deck_position=0，seq=1；与 game_puzzles(game_id, sequence_no) 唯一约束冲突，下一题插入失败",
         "GameService.java:280–301；V1 uq_puzzle_game_seq",
         "题池耗尽后的重置路径不可用；正常节奏难触发",
         "无；未修"),
        ("R10", "参数校验不一致：POST /api/games 的 mode 或 level 缺失时 Mode.valueOf(null) 抛 NPE，被全局兜底为 500 而不是 400",
         "GameController.create；GlobalExceptionHandler",
         "客户端错误被报成服务端错误；监控噪声",
         "前端总是传；未修"),
        ("R11", "工程化缺口：无 CI；无常态化 E2E/压测/监控；无管理后台；封禁/改密靠 SQL",
         "仓库配置；部署记录",
         "自动验证与运维仍靠手工；评审复现成本高",
         "文档 + 手工脚本"),
        ("R12", "存储增长：games.deck 存整副牌；game_actions 只增不删；没有归档/清理",
         "V1 schema；代码无清理任务",
         "写放大；备份与查询随时间变慢",
         "无"),
        ("R13", "游客合并后 game_results 双 owner：claim 写入 account_id，但保留原 guest_id；personal_bests 则是 account-only",
         "GuestClaimService.claim；本次一致性 SQL 在本地 E2E 库命中 2 条",
         "同一成绩同时带 account_id 与 guest_id；按 account_id 查询功能正常，但 owner 语义不一致，是否为保留来源需确认",
         "查询用 account_id 过滤；未修"),
    ],
    [1.0, 6.2, 3.7, 3.7, 2.0],
    font_size=7.7,
    header_size=7.9,
    align_center={0},
)

h2("7.2", "我们还不确定的地方")
for s_ in [
    "答错之后是换下一题还是原地重做、刷新之后是否必须恢复原局？这两个玩法口径还没有最终决定。",
    "线上演示数据（10 个演示账号、弱口令）是否保留？是否允许外部访问？",
    "2C2G 的容量边界没有压测数据；我们不能给出“能扛多少并发”的结论。",
    "前端 24 个用例已在本次重跑通过（19:28，jsdom）；但 jsdom 不等于真实浏览器矩阵，移动端只做了 390px 视口。",
    "开发库有 16 和 18.1 两种，线上是 14；是否需要统一到一个版本，避免迁移/函数差异？",
    "“单人挑战 + 四个榜”是目标形态，还是两人对战版的过渡？这会影响数据模型和接口要不要预留。",
    "游客模式是否长期保留？如果保留，游客数据的清理与隐私边界需要明确。",
    "是否需要先补 CI、常态化 E2E、监控、HTTPS，再扩玩法？我们没有足够信息判断优先级。",
]:
    bullet(s_)

# ---------------- chapter 9 ----------------
h1("八、", "测试与验证")
para("本章记录 2026-11-05 这次补做的验证。测试环境是工作区内隔离的 PostgreSQL 18.1（:55433）、本地 Spring Boot（:8080）与 Vite（:5173）；浏览器为 headless Chrome 156；线上只做只读请求。所有结果来自本次实际执行，不是引用旧报告。")

h2("8.1", "现有自动化用例")
table_caption("表 8-1  自动化用例清单")
table(
    ["范围", "文件", "用例", "覆盖点"],
    [
        ("后端", "GameRulesTest", "6", "分数中间值、经典分数题、除零、算符顺序、L1 禁用乘除、不可解题"),
        ("后端", "ExpressionEvaluatorTest", "6", "分数解、连加、复用牌、步数错误、L1 乘除、除零"),
        ("后端", "PuzzleGeneratorTest", "2", "候选数 1,820；L1 220、L2 1,362"),
        ("后端", "GameServiceScoringTest", "3", "A 取最后一题用时；A 零题；B 用时+罚时"),
        ("后端", "LeaderboardNicknameMaskTest", "3", "中文首字脱敏；emoji 不截断；null/空"),
        ("后端", "AccountLeaderboardIntegrationTest", "4", "注册/登录/me；refresh 轮换与重放；游客合并；榜单排序与我的排名"),
        ("前端", "merge.test.ts", "11", "选择/算符/合并顺序、分数、除零、撤销、三步完成、预览"),
        ("前端", "ui.test.ts", "13", "首页渐进披露、点牌合并、J/Q/K、自动提交 payload、答错罚时、A 倒计时/到时、跳题/退出弹窗"),
    ],
    [1.6, 5.6, 1.4, 8.0],
    font_size=8.0,
    header_size=8.0,
    first_col_bold=True,
    align_center={2},
)
para("后端 24 个用例（含 4 个集成用例），前端 24 个用例。集成测试用 @Tag(\"integration\")，默认 mvn test 排除，mvn -Pintegration test 打开。")

h2("8.2", "本次执行记录")
table_caption("表 8-2  2026-11-05 补做结果")
table(
    ["项目", "执行方式", "结果"],
    [
        ("后端单元 + 集成", "mvn -Pintegration test；隔离 PG 18.1 :55433", "24/24 通过；AccountLeaderboardIntegrationTest 4/4，15.65 s"),
        ("前端单元", "npx vitest run", "24/24 通过（2 个文件）"),
        ("浏览器 E2E", "headless Chrome 156 + CDP，本地 Vite/Spring", "11/11 通过：首页、渐进披露、A/L1 开局、正确、答错罚时、撤销、跳题、退出、刷新回首页、390px 无横向溢出、records 断网报错"),
        ("API E2E", "Node fetch，本地 :8080", "26/26 通过：建局幂等、归属 403、正确/错误/跳题/退出、B 答满 10、游客合并、me、榜单脱敏与排名、refresh 轮换与重放、400/401/409/500 边界"),
        ("只读负载", "Node fetch，线上 :8081，180 请求", "0 错误；health p50/p90/p99 = 143/290/394 ms；榜单 117/156/159 ms；首页 95/147/157 ms；观测吞吐 84.7–106.6 rps（含公网 RTT，不代表容量）"),
        ("安全冒烟", "线上只读 + 本地账号/错误路径", "16/16 通过；XFO=DENY、nosniff；无 HSTS/CSP；CORS 无 ACAO；Cookie HttpOnly+SameSite=Strict；500 无堆栈；无 token 的 me=401"),
        ("数据库迁移", "Flyway V1/V2 全新 schema + 约束探针", "V1、V2 success；8 张表（含 flyway history）；111 个约束、25 个索引；重复 game_result、无 owner 的 best/game、重复题目序号、非法用户名均被拒绝"),
        ("数据一致性", "SQL 对账（game/game_results/personal_bests）", "game24_test 0 条异常；本地 E2E 库发现 2 条 claimed result 同时带 account_id 与 guest_id（见 8.3）"),
        ("依赖审计", "npm audit（生产 / 全量）", "生产 0；全量 6 个（3 moderate、1 high、2 critical），均在 Vitest/Vite/esbuild 开发链"),
        ("覆盖率", "JaCoCo 0.8.12；Vitest v8", "后端行 57.6%、分支 46.6%、指令 53.7%；前端语句/行 59.21%、分支 72.31%、函数 69.41%"),
    ],
    [3.0, 6.6, 7.0],
    font_size=8.0,
    header_size=8.0,
    first_col_bold=True,
)

h2("8.3", "补做结论与仍未覆盖")
para("原先“没有覆盖的部分”列出的缺口，能在这套环境里做的已经补做：浏览器 E2E、只读负载、安全冒烟、前端网络故障、迁移前置校验、覆盖率、数据一致性、依赖审计。下面是补做后的结论与仍然做不了的部分。")
callout("补做中发现的一处数据一致性差异", [
    "游客合并后，game_results 写入 account_id，但保留原 guest_id；personal_bests 则只有 account_id。",
    "本次对账在本地 E2E 库命中 2 条这样的记录；按 account_id 查询功能正常，但同一成绩的 owner 语义不一致。",
    "这可能是为了保留来源，也可能是遗漏；需要团队确认口径，再决定是否清理 guest_id。",
])
for s_ in [
    "仍未做写路径的并发/容量压测：本次只压了 health、榜单、首页三条只读路径，没有压提交、结算、游客合并；不能据此给出并发上限。",
    "仍未做生产故障注入：数据库断连、慢查询、时钟漂移、Flyway 失败、磁盘满，只在本地做了前端断网展示。",
    "仍未做多浏览器/真机矩阵与无障碍审计：只跑了 headless Chrome 156 一个视口（390px）和桌面默认视口。",
    "仍无法做迁移回滚：仓库只有向上迁移，没有 down 脚本；本次只验证了全新 schema 的 V1→V2。",
    "仍未做后端依赖 CVE 扫描：前端 npm audit 已做，Maven 依赖只核对了版本，没有跑 OWASP Dependency-Check。",
    "仍未做完整渗透测试：本次只覆盖了响应头、CORS、认证/鉴权状态码、错误信息、Cookie 标志与一个注入式参数。",
    "仍未做长时间稳定性/内存泄漏观察：应用在本地只跑了单次测试周期，线上只读请求约 3 分钟。",
]:
    bullet(s_)
para("测试环境说明：本地 PostgreSQL 18.1 使用独立数据目录（端口 55433），测试结束后已停止并清理；没有接触线上数据库，也没有向线上写入任何对局或账号。", 9.2, False, GREY)

# ---------------- appendix ----------------
doc.add_page_break()
h1("附录 A", "关键文件索引")
table_caption("表 A-1  评审时可以直接打开的文件")
table(
    ["关心的问题", "文件"],
    [
        ("求解与判题", "demo/server/src/main/java/com/game24/rules/GameRules.java；ExpressionEvaluator.java"),
        ("对局/计时/结算", "demo/server/src/main/java/com/game24/game/GameService.java"),
        ("账号/令牌/合并", "demo/server/src/main/java/com/game24/auth/"),
        ("排行榜", "demo/server/src/main/java/com/game24/leaderboard/"),
        ("表结构与迁移", "demo/server/src/main/resources/db/migration/V1__init.sql；V2__accounts_and_leaderboard.sql"),
        ("前端交互", "demo/web/src/main.ts"),
        ("合并编辑器", "demo/web/src/merge.ts"),
        ("API 客户端", "demo/web/src/api.ts"),
        ("样式与响应式", "demo/web/src/styles.css"),
        ("部署记录", "docs/服务器部署记录-121.43.236.209.md；deploy/"),
        ("测试", "demo/server/src/test/；demo/web/tests/"),
    ],
    [4.6, 12.0],
    font_size=8.4,
    header_size=8.4,
    first_col_bold=True,
)

h1("附录 B", "术语表")
table_caption("表 B-1  文中反复出现的词")
table(
    ["术语", "含义"],
    [
        ("A 模式", "限时挑战：300 秒倒计时，答对越多越好；答错/跳题扣剩余时间"),
        ("B 模式", "定量挑战：答对 10 题结束，总用时越短越好；答错/跳题加总用时"),
        ("L1 / L2", "难度：L1 只用 + −；L2 用 + − × ÷"),
        ("局 / 题", "一局 = 一次挑战；一题 = 一组合并，由四个数字与三次合并组成"),
        ("计榜用时", "A 为答对第 N 题时的实际经过+罚时；B 为完成第 10 题时的实际经过+罚时"),
        ("罚时", "答错 5 秒、跳题 10 秒；A 扣剩余时间，B 加总用时；撤销不消除"),
        ("revision", "对局版本号；每次写操作 +1，客户端提交时必须带当前版本，防并发覆盖"),
        ("actionId", "动作幂等号；同一局同一 actionId 只能对应一个请求指纹"),
        ("guestId", "游客标识；localStorage 生成，请求头 X-Guest-Id，登录时并入账号"),
        ("personal_bests", "每账号/游客在每个模式×难度下的唯一最佳成绩"),
        ("幂等", "同一请求重复到达，结果与一次到达相同；建局用 requestId，动作用 actionId"),
    ],
    [3.4, 13.2],
    font_size=8.4,
    header_size=8.4,
    first_col_bold=True,
)

h1("附录 C", "本地复现命令")
para("以下命令按 Windows PowerShell / Git Bash 的混合写法整理，实际以 demo/README.md 为准；Linux 下把 .\\mvnw.cmd 换成 ./mvnw。", 9.2, False, GREY)
mono([
    "# 1) 数据库（二选一）",
    "docker compose up -d",
    "# 或使用本机 PostgreSQL 18.1（端口 55432，数据目录 C:\\Users\\cx\\pgdata-game24）",
    "",
    "# 2) 后端",
    "cd demo/server",
    ".\\mvnw.cmd spring-boot:run",
    "# 健康检查",
    "curl http://127.0.0.1:8080/api/health",
    "",
    "# 3) 前端",
    "cd demo/web",
    "npm install",
    "npm run dev",
    "# 打开 http://127.0.0.1:5173",
    "",
    "# 4) 测试与构建",
    "cd demo/server && .\\mvnw.cmd test",
    "cd demo/server && .\\mvnw.cmd -Pintegration test   # 需真实 PostgreSQL",
    "cd demo/web && npx vitest run",
    "cd demo/web && npm run build",
    "",
    "# 5) 重新生成题池（L1/L2）",
    "cd demo/server",
    ".\\mvnw.cmd compile exec:java \"-Dexec.mainClass=com.game24.puzzle.PuzzleGenerator\"",
])

# closing
p = doc.add_paragraph()
p.paragraph_format.space_before = Pt(22)
p.paragraph_format.space_after = Pt(4)
set_font(p.add_run("以上是截至 2026 年 11 月 5 日的现状。"), 10.5, True, NAVY)
p = doc.add_paragraph()
p.paragraph_format.space_after = Pt(4)
p.paragraph_format.line_spacing = 1.5
set_font(p.add_run("凡是我们判断错的地方，请直接指出；凡是文档与代码不一致的地方，也请告诉我们以哪边为准。谢谢。"), 10.5, False, DARK)

out = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs", "24点单人挑战_现状汇报_2026-11-05.docx")
doc.save(out)
print("saved", out)
print("paragraphs", len(doc.paragraphs), "tables", len(doc.tables))