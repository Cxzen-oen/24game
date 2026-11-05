> 后续进展（2026-11）：账号体系与排行榜已实现，云端部署方案见 `docs/账号与排行榜_上云架构方案.md`，部署步骤见 `docs/上云部署手册.md`。本文保留为单机 Demo 阶段的方案记录。

# 24 点单机 Demo 全栈开工方案

> 状态：已实施（本地跑通）  
> 实施记录：后端 Spring Boot 已落地，数据库使用本机独立 PostgreSQL 实例（端口 55432，避免与本机 5432 的 Hindsight 实例冲突）；
> 前端 Vite 页面已完成，题池 1820/220/1362 由 Java 实现复算通过。启动见 demo/README.md。  
> 目标：本地跑通真实出题、点击作答、服务端判题与结算、数据库保存成绩；保留后续云部署路径。  
> 规则依据：docs/24点游戏_单人挑战与排行榜_规则说明.md。旧 design/*.html 仅作视觉和交互参考。

## 1. 本轮闭环与边界

选择难度和模式 → 创建对局 → 服务端发题 → 点两张牌与算符合并 → 撤销 / 提交 / 跳题 → 正确进入下一题 → 达到结束条件 → 服务端结算 → 数据库保存成绩 → 查看历史与个人最佳 → 再来一局。

必须完成：

1. L1/L2 参数化离线题池，不再循环固定示例题。
2. 点牌 UI、表达式回读、服务端精确判题、撤销、反馈和快捷键。
3. A/B 服务端计时、罚时、结束与结算。
4. Java 后端 API、PostgreSQL 持久化、刷新恢复、历史与四个本机最佳成绩。
5. 可复现的本地启动、自动测试和浏览器验收。

排行榜只保留入口、A/B 与 L1/L2 筛选外观、表头和“暂未开放”。不填虚假玩家、不显示本机名次、不做排名 API。

明确不做：登录注册、双人匹配、对手、胜负平、L3、真实排行榜、防作弊、Redis、消息队列、微服务、本轮云部署。不用 H2/SQLite 替代 PostgreSQL，不用 localStorage 保存成绩。

## 2. 技术选型与环境前置

| 层 | 选型 | 说明 |
|---|---|---|
| 前端 | Vite + TypeScript（vanilla）+ 原生 CSS | 页面少，不引入大型 UI 框架 |
| 后端 | Java 21 + Spring Boot + Maven Wrapper | 本机已有 Java 21，Web/数据/测试生态成熟 |
| 精确运算 | 后端 Apache Commons Numbers Fraction；前端 fraction.js 仅作预览 | 复用成熟有理数库，权威结果由后端计算 |
| 数据库 | PostgreSQL（固定主版本） | 事务、约束、JSONB 与云部署均适用 |
| 数据访问 | Spring JDBC + Flyway | SQL 明确，表结构迁移可追踪 |
| 后端测试 | JUnit + Spring Boot Test + Testcontainers | 规则测试与真实数据库测试分开 |
| 前端/E2E | Vitest + Playwright | 覆盖逻辑与真实点击 |
| 本地依赖 | Docker Compose 管 PostgreSQL | 一条命令启动，减少环境差异 |

已核查：本机有 Node/npm 和 Java 21；Go、Docker、Maven 命令、PostgreSQL 客户端当前不在 PATH。开工先安装并启动 Docker Desktop；Maven 用项目 Wrapper，无需全局安装。这里只是环境检查，尚未运行 Demo。

localStorage 仅保存随机 guestId、界面设置和最近 gameId。对局、计时、罚时、结算、历史和最佳全部以服务端/数据库为准。

## 3. 不可改动的规则

| 项目 | 口径 |
|---|---|
| L1 加减级 | 四个 1–13 整数，可重复；只允许 +、− |
| L2 四则级 | 四个 1–13 整数，可重复；允许 +、−、×、÷ |
| 通用题面 | 四数各用一次；精确为 24；至少一解；允许中间分数；禁止除零 |
| 作答 | 点两张牌再点算符；合并三次后提交；括号由点击顺序决定 |
| A 模式 | 固定 300 秒倒计时，无单题超时 |
| B 模式 | 答对 10 题立即结束，跳题不占完成名额，无单题超时 |
| 答错 | 完整提交且不为 24，罚 5 秒；非法本地操作不罚 |
| 主动跳题 | 罚 10 秒，当前题不可返回 |
| A 成绩 | 答对题数；同题数比较答对第 N 题时计榜用时，短者优先 |
| B 成绩 | 第 10 题答对时实际用时 + 全部罚时，短者优先 |
| 最佳成绩 | 按游客 × 模式 × 难度保存四个最佳；严格变好才替换，追平不替换 |
| 中途退出 | 二次确认；无效，不写历史或最佳 |
| 刷新恢复 | 从服务端恢复原局；离线期间计时继续，不补偿 |

guestId 只隔离本机演示数据，不是账号安全。Demo 不伪造登录；未来接真实鉴权时，身份从登录主体获取，不能继续信任 URL 中的 ID。

## 4. 架构与工程边界

~~~text
浏览器（Vite / TS）
  │ 只展示、采集点击、渲染服务端状态
  │ HTTP JSON；开发环境 Vite 代理 /api
  ▼
Spring Boot 单体
  ├─ Game API：创建、恢复、提交操作树、跳题、退出
  ├─ Rules：精确判题、计时、罚时、结算
  ├─ Puzzle：离线题池加载、洗牌、不重复抽题
  └─ Records：事务写历史、更新最佳
       │ JDBC / Flyway
       ▼
PostgreSQL：对局、题目状态、幂等操作、成绩、最佳
~~~

进行中对局也持久化，内存不是唯一真相。所有写 API 在事务内执行。生产构建由 Spring Boot 托管前端静态资源；开发时分别启动。单体足够，不拆微服务。

~~~text
24game/
  compose.yaml
  .env.example
  demo/
    web/                    # Vite + TS
      src/{main,api,domain,ui,styles}
      tests/ e2e/
    server/                 # Spring Boot + Maven Wrapper
      pom.xml
      src/main/java/.../{api,game,puzzle,records}
      src/main/resources/{application.yml,db/migration,puzzles}
      src/test/
    README.md
  design/                   # 旧设计稿保留
  docs/                     # 规则与方案
~~~

Controller 不写判题或计分逻辑，UI 不自行决定成绩；规则只有后端一套权威实现。

## 5. L1/L2 题目生成

### 5.1 离线穷举

1. 穷举 1 ≤ a ≤ b ≤ c ≤ d ≤ 13，共 1820 个无序牌组，数字允许重复。
2. 每组运行 DFS：任选两张牌按本难度算符合并；减法和除法尝试两个操作数顺序，直到一张。
3. 用 Commons Fraction 精确判断是否得到 24，除零分支丢弃，不使用 eval。
4. 分别输出 L1/L2 可解牌组与配置版本；同一牌组可存在于两个独立题池。
5. 题池只保存数字四元组与稳定 ID，标准解和求解树不通过 API 发给浏览器。

生成配置：L1 为 min=1、max=13、target=24、operators=[+,-]；L2 为 [+,-,*,/]。最少解数、必须算符、必须分数只留扩展点，本轮不增加额外难度条件。

生成器是 Maven 独立 profile `generate-puzzles`，入口使用 `exec-maven-plugin`，命令为 `mvnw.cmd -Pgenerate-puzzles compile exec:java -Dexec.mainClass=com.game24.tools.PuzzleGenerator`（Linux/macOS 将 mvnw.cmd 换为 ./mvnw）。生成产物写入 server/src/main/resources/puzzles；不在服务启动或首屏请求时穷举。生成后断言：候选 1820、L1 可解 220、L2 可解 1362。本轮已用 Python Fraction 的两牌 DFS 与不排序子集 DP 两种独立算法交叉核验该结果；Java 实现也需与参考实现比对。若不一致先排查算法与规则，不直接改期望；重复生成必须一致，发布前用同一判题内核复算。

### 5.2 单局抽题

- 开局将该难度洗牌后的顺序持久化，记录 deckPosition。
- A 按游标持续抽题；B 跳题后继续补充，直到答对 10 题。
- 同一抽题周期不重复；整池耗尽才重新洗牌，跨周期允许重复。
- puzzleId 由服务端唯一生成，请求携带它防止旧题污染新题。
- 刷新或服务重启按已保存题序恢复，不重新随机换题。
- 本轮不做“前易后难”，UI 不宣称具备难度曲线。

## 6. 点牌 UI 与权威判题

### 6.1 交互

状态：未选牌 → 已选 1 张 → 已选 2 张 → 点算符合并 → 未选牌；三次合并后可提交，正确后反馈/下一题，结算后锁定。

- 每张牌有稳定 cardId、精确值和表达式子树，不能只存小数。
- 先点为左操作数，后点为右操作数；减除严格保持顺序。
- 再点已选牌可取消；选第三张时提示先取消，不静默替换。
- 合并后旧牌移除，结果牌显示整数或 a/b；复合子式回读加括号。
- 前端用快照栈支持连续多步撤销，不退时间、错误或罚时；每次错误提交后可继续撤销。刷新重置未提交编辑，但题面与已有计时/罚时不变。
- 除零、未选满、未完成、非法算符、旧题、已封盘均拒绝，不计答错。
- 完整提交不为 24：显示结果与罚 5 秒，保留牌面供撤销/重试。
- 提交、跳题和退出带唯一 actionId，双击或重试不得重复处罚或推进；本地合并/撤销不调用后端。

### 6.2 前后端协作

合并与撤销在前端本地完成，用 fraction.js 预览结果；正式 submit 传三步操作树，由后端用 Commons Fraction 逐步重算。每步引用两个原始 cardId 或更早的 stepId，最终根为第三步；服务端验证恰好三步、原始四叶各用一次、引用无重复/悬空/环、算符合法且无除零。非法链返回 422 不罚时，合法完整链不为 24 才罚 5 秒。前端不能传结果要求服务端采信。

局内写请求带 guestId、actionId；提交/跳题另带 puzzleId/revision，退出带 revision 不带 puzzleId；创建带 guestId/mode/level 和独立 requestId 防重。requestId 存入 games 并对 guestId+requestId 建唯一约束，同参数重放返回已建对局，不同参数 409。路径已有 gameId，body 不重复传。submit 额外带 operations 三步链。响应统一带最新 revision 和对应 actionId。

按钮：撤销、全部相加、全部相乘（仅 L2）、提交、跳题、退出。撤销在本地执行，快捷合并本地生成三步链；提交、跳题与退出调用 API。快捷键 1–4、+ − * /、Esc、Enter、A/S 与按钮共用动作入口；请求失败时重新同步服务端状态，不推进成绩。

## 7. 计时、罚时与事务结算

### 7.1 服务端计算

统一注入 Clock，每次请求只取一次 now，时间用 Instant，成绩用整数毫秒；不用 setInterval 次数或客户端上报用时。对局 GET 也在事务中锁行并惰性结算；B 完成或 A 到期后冻结 finishedAt 和成绩。每个写操作先锁定对局并检查 actionId：已存在且请求指纹一致时直接返回首次响应，不再次结算或处罚；指纹不同返回 409。新动作再执行 settleIfNeeded(now)，之后校验并执行。

设实际经过 E 毫秒，答错 W 次，跳题 S 次，罚时 P = 5000W + 10000S：

~~~text
A 剩余时间 = max(0, 300000 - E - P)
A 第 N 题计榜用时 = 答对第 N 题时的 E + 当时 P
B 总计榜用时 = 第 10 题答对时的 E + 当时 P
~~~

- A 到点或罚时耗尽立即封盘，不再发题；当前有效截止时刻 = startedAt + 300000ms − 已累计罚时。deadline_at 是该时刻的持久化投影，每次罚时同步更新；判分以开局时间和罚时重算结果为准。每次写操作先按旧罚时检查是否已到期，再应用本次动作；now 必须严格早于动作前有效截止时刻才可判分。动作后重新计算截止时刻，必要时立即结算。
- A 每次答对记录最后一题计榜用时，不能结算时统一填 300 秒。
- A 至少答对 1 题才更新最佳；0 题保存历史但不更新最佳。
- B 第 10 题答对时结算；跳题先罚时，再检查 A 是否结束，未结束才发题。
- 检查 revision 与 puzzleId，旧请求返回 409，不重复计分。
- 退出和到期幂等，已结算不可被迟到请求改变。

无需高频写库。创建、读取、提交、跳题、退出时按时间惰性结算；前端本地渲染倒计时，每个写动作及低频/到点再同步，不每秒请求后端。可有到期清理任务，但任务延迟不能延长作答时间。

### 7.2 事务

提交、跳题、退出在一个事务内完成：锁定对局 → 校验动作幂等 → 按时间结算 → 校验 → 写状态/结果 → 更新最佳 → 保存幂等响应。用 SELECT ... FOR UPDATE 防同局并发，唯一约束兜底。结果与最佳必须同一事务成功；退出无结果或最佳。

## 8. API 与 PostgreSQL 表

### 8.1 API

| 方法与路径 | 用途 |
|---|---|
| POST /api/games | 创建：guestId、mode、level、requestId，返回权威状态 |
| GET /api/games/{id}?guestId=... | 恢复，先检查到期 |
| POST /api/games/{id}/submit | guestId、puzzleId、revision、actionId、三步 operations，重算判题 |
| POST /api/games/{id}/skip | guestId、puzzleId、revision、actionId，跳题并罚时 |
| POST /api/games/{id}/abandon | guestId、revision、actionId，无效退出 |
| GET /api/records?guestId=...&limit=50 | 历史与四个最佳 |
| GET /api/health | 应用与数据库健康 |

统一状态包含 gameId、revision、status、mode、level、serverTime、puzzle、cards、correct、wrong、skipped、remaining/elapsed；结算追加成绩。进行中不返回答案或求解树。游客不匹配返回 403，旧版本/旧题 409，非法合并 422。

### 8.2 表

| 表 | 关键内容与约束 |
|---|---|
| games | id、guest_id、mode、level、status、started_at、deadline_at、correct/wrong/skipped、penalty_ms、last_scoring_time_ms、deck、deck_position、revision、finished_at |
| game_puzzles | id、game_id、sequence_no、puzzle_key、numbers_json、status；(game_id, sequence_no) 唯一；numbers_json 是四整数数组 |
| game_actions | game_id、action_id、action_type、request_fingerprint、response_jsonb、created_at；(game_id, action_id) 唯一，同键同指纹重放原响应，不同指纹 409 |
| game_results | result_id、game_id、guest_id、mode、level、答对/答错/跳题、实际用时、罚时、计榜用时、起止时间；result_id 与 game_id 均唯一 |
| personal_bests | guest_id、mode、level、result_id、achieved_at；(guest_id, mode, level) 唯一 |

时间戳 timestamptz，时长/罚时整数毫秒。首版 Flyway 明确 PK/FK/UNIQUE/CHECK：mode、level、status 枚举，deck_position 与 deck 一致，成绩字段非空且非负；game_results.result_id 唯一供 personal_bests 外键引用。最佳更新采用 INSERT ... ON CONFLICT DO UPDATE ... WHERE 新成绩严格优于旧成绩的原子 SQL，不能先查再更新导致并发纪录被覆盖；对同一 guest+mode+level 做并发集成测试。JSONB 只用于幂等响应，不替代结构化对局与成绩，也不存标准答案。

A 严格更好：答对更多，或答对相同且最后一题计榜用时更短。B 严格更好：总计榜用时更短。追平保留第一次纪录；不同游客、模式、难度互不影响。Flyway 管理迁移，不依赖 ORM 随意改表。

## 9. 页面

- 首页：L1/L2、A/B 固定配置、罚时说明、我的最佳、开始、历史与排行榜入口。
- 作答：顶部模式/难度/答对/计时；A 剩余时间进度条，B 已答对 /10；中部牌面；下部算式、最近合并、算符和反馈。
- 结算：无胜负，展示模式、难度、答对、实际用时、答错、跳题、罚时和计榜成绩；严格变好提示“新纪录”。
- 历史：数据库最近 50 局正常结算。
- 排行榜：静态筛选外观与空状态，绝不从 personal_bests 伪造排名。

复用旧 design 的颜色、卡片、数字牌与合并表达式思路，删除匹配、对手、L3、胜负和断线等待。旧 HTML 的手写分数、浮点牌值和固定 PUZZLES 不搬入新代码。适配 1440×900 和 390×844，不沿用旧 PC 绝对定位主布局。

## 10. 实施顺序

| 顺序 | 工作包 | 完成标志 |
|---|---|---|
| 0 | Docker 数据库、Spring/Vite、Flyway、健康检查 | 迁移成功，前后端访问健康 API |
| 1 | Fraction 规则内核、DFS 与离线题池 | 分数/除零/合并测试过，1820/220/1362 校验过 |
| 2 | 对局 API：建局、提交操作树、跳题、恢复、防重 | 权威状态可恢复，过期/重复请求不污染数据 |
| 3 | 首页与作答 UI、快捷键、API 对接 | 鼠标/键盘均可完成 L1/L2 一题 |
| 4 | Clock、A/B 状态机、事务结算、退出无效 | 到点封盘、B 第 10 题结束、罚时边界测试过 |
| 5 | 历史、四最佳、新纪录、排行榜空态 | 重启数据仍在，追平不替换，无假排名 |
| 6 | 单元、真实 PostgreSQL 集成、Playwright、说明 | 清单全过，本地启动可复现 |

前端可按固定 DTO 并行，但规则、计时、成绩只在后端实现一套。

## 11. 验收清单

### 规则/API

- [ ] 题面均为 1–13 且可解，L1 不混乘除；L1=220、L2=1362。
- [ ] 8/(3−8/3)=24 等中间分数精确判对；除零拒绝。
- [ ] 四数各用一次、三次合并、操作数顺序、撤销树、非法算符均正确。
- [ ] 错误罚 5 秒、跳题罚 10 秒；非法操作不罚；重复 actionId 不重复处罚。
- [ ] A 同题数比较最后一题计榜用时；自然到点/罚时耗尽封盘；0 题不更新最佳。
- [ ] B 跳题不增加答对数，第 10 次正确结算，罚时不重复加。
- [ ] 旧 puzzleId、过期版本、已结束对局、其他游客请求均拒绝。
- [ ] 提交与到期、双击与重试、并发提交不重复推进或结算。
- [ ] 四个最佳互不覆盖，变差/追平不覆盖；结果与最佳事务一致。

### 浏览器/数据库

- [ ] L1/A 服务端真实发题；合并、错误、撤销、跳题、提交完整可操作。
- [ ] L2/B 完成含除法和中间分数的一题，答满 10 题进入结算。
- [ ] 对局中刷新、重启后端仍恢复原题、计时和已确认进度；未提交合并编辑可重置；A 离线时间仍扣除。
- [ ] 结算后刷新、重启应用和数据库，历史与最佳仍可读。
- [ ] 主动退出二次确认，不写历史或最佳；排行榜始终“暂未开放”。
- [ ] 390×844 和 1440×900 无重叠、横向溢出或不可点击按钮。
- [ ] 如实记录单元、Testcontainers 和 Playwright 结果，不以“页面打开”代替验收。

## 12. 本地启动与云端路径

开工时先安装 Docker Desktop；项目负责提供 Compose、.env.example、Maven Wrapper 和应用配置。以下 Windows PowerShell 命令固定写入方案与 demo/README.md，不再留待后续补命令：

~~~powershell
# 1. 仓库根目录：创建本地配置并启动 PostgreSQL
Copy-Item .env.example .env
docker compose up -d

# 2. 后端：生成/校验题池，启动 API（Flyway 自动迁移）
cd demo/server
.\mvnw.cmd -Pgenerate-puzzles compile exec:java "-Dexec.mainClass=com.game24.tools.PuzzleGenerator"
.\mvnw.cmd spring-boot:run

# 3. 新 PowerShell 窗口：前端
cd demo/web
npm install
npm run dev
~~~

打开 Vite 实际输出地址，通常 http://localhost:5173；后端 http://localhost:8080/api/health 应显示健康。以日志为准。Linux/macOS 将 .\mvnw.cmd 换成 ./mvnw。.env.example 提供本机开发默认值：POSTGRES_DB=game24、POSTGRES_USER=game24、POSTGRES_PASSWORD=game24_local_only、POSTGRES_PORT=5432；后端对应 DB_URL=jdbc:postgresql://localhost:5432/game24，DB_USERNAME/DB_PASSWORD 与之相同。真实密码只写本机 .env，不提交。

题池已存在且未改规则时可跳过生成命令；修改生成规则必须重跑并核对统计。启动数据库后可用 docker compose exec postgres pg_isready -U game24 -d game24 验证。

验收与生产构建命令同样固定：

~~~powershell
cd demo/server
.\mvnw.cmd test                         # 规则与数据库集成测试，需要 Docker
cd ../web
npm test -- --run
npm run test:e2e                        # 需要按 Playwright 提示安装浏览器
npm run build                           # 产物由 Maven 构建复制到 server 静态目录
cd ../server
.\mvnw.cmd clean package               # 产出单一可运行 JAR
java -jar target/game24-demo.jar        # 实际 jar 名在 pom 中固定
~~~

这些命令对应开工后的交付物；当前尚未创建工程，不能把它们描述为已验证可运行。第 0 工作包完成后须在干净目录按以上步骤实测并记录结果，不要求手改生成数据或数据库。

未来云部署沿用 PostgreSQL（容器或云数据库）+ 单 Spring Boot + 后端托管前端构建，反向代理终结 HTTPS。配置走环境变量；持久化卷、备份、HTTPS、限流和真实账号鉴权是上线前工作项，本轮不宣称生产可用。

## 13. 给 Kimi 3.1 的开工约束

按第 10 节顺序实施，先完成 0、1 并展示规则测试与题池统计，再做 UI。使用 Java 21 + Spring Boot + PostgreSQL；不得擅自改成纯前端、localStorage 成绩、H2/SQLite、Go 或微服务。

不要恢复旧原型的双人、L3、固定题、浮点牌值和胜负文案；排行榜保持空壳。每个工作包运行测试并报告真实输出；规则变化先更新本方案与规则依据，不在代码里静默发明口径。
