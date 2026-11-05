from report_v2_base import *

# ---------------- chapter 4 ----------------
h1("三、", "前端架构与模块")
h2("3.1", "技术栈")
table_caption("表 3-1  前端选型")
table(
    ["项目", "选型", "说明"],
    [
        ("构建", "Vite 5.4.10", "dev server 127.0.0.1:5173，/api 代理到 8080"),
        ("语言", "TypeScript 5.6.3", "构建前执行 tsc --noEmit"),
        ("数字", "fraction.js 4.3.7", "精确分数，避免浮点误差"),
        ("测试", "Vitest 2.1.4 + jsdom 30", "合并逻辑 + DOM 点击"),
        ("样式", "手写 CSS 801 行", "设计 token；无 CSS 框架"),
        ("框架", "无", "直接 DOM API + 模板字符串"),
        ("路由", "无", "视图状态在内存，没有 URL 深链"),
        ("状态", "全局变量 + 纯函数编辑器", "没有 Redux / Zustand / Context"),
    ],
    [2.4, 4.6, 9.6],
    font_size=8.8,
    header_size=8.8,
    first_col_bold=True,
)

h2("3.2", "文件与职责")
table_caption("表 3-2  前端模块")
table(
    ["文件", "行数", "职责"],
    [
        ("index.html", "17", "挂载点、viewport、移动端 meta、主题色"),
        ("main.ts", "1,076", "5 个视图、全局状态、时钟、事件、渲染、弹窗与 toast"),
        ("api.ts", "271", "类型、fetch 封装、guest/token、401 刷新重试、actionId"),
        ("merge.ts", "194", "合并编辑器纯函数、表达式、撤销、预览"),
        ("styles.css", "801", "设计 token、响应式、卡片/榜单/弹窗"),
        ("tests/", "24 个用例", "merge 11 + ui 13（jsdom）"),
    ],
    [3.2, 2.4, 11.0],
    font_size=8.8,
    header_size=8.8,
    first_col_bold=True,
    align_center={1},
)

h2("3.3", "视图与状态")
table_caption("表 3-3  五个视图")
table(
    ["视图", "进入方式", "主要内容"],
    [
        ("home", "启动 / 返回首页", "模式卡（A/B）、难度（L1/L2）、开始按钮、最佳成绩条"),
        ("play", "开始挑战 / 下一题", "HUD、时钟、进度条、四张牌、算符、反馈、撤销/跳题/退出"),
        ("result", "对局 FINISHED", "本局统计、新纪录徽章、再来/成绩/排行/首页"),
        ("records", "底部导航", "游客提示、四个最佳、模式/等级筛选、最近 50 条"),
        ("leaderboard", "底部导航", "模式/等级切换、榜单、我的排名、上一页/下一页"),
    ],
    [2.6, 4.4, 9.6],
    font_size=8.8,
    header_size=8.8,
    first_col_bold=True,
)
para("全局状态集中在 main.ts：view、game、editor、mode、level、account、lbMode/lbLevel/lbPage、recMode/recLevel，以及时钟锚点。render() 先停表、清弹窗，再按 view 重建 DOM；records 与 leaderboard 是异步视图，用 renderSeq 防止旧请求覆盖新页面。")
para("没有路由、没有 history、没有深链，也没有把 gameId 写进 URL 或 localStorage。因此刷新页面总是回到首页；这是 7.1 R3 的一部分。")

h2("3.4", "作答编辑器（merge.ts）")
para("merge.ts 是一个不依赖 DOM 的纯函数模块，负责“牌树”和“操作步骤”。核心结构是一个 Card：")
mono([
    "Card = {",
    "  id: 'c0'..'c3' | 's0'..'s2',   // 原始牌或第 n 次合并结果",
    "  value: Fraction,               // 精确值",
    "  origin: number | null,         // 原始牌面；合并牌为 null",
    "  left, right: Card | null,      // 合并树",
    "  op: string | null              // '+', '-', '*', '/'",
    "}",
])
bullet("未选时点牌 → 选中；再点同一张 → 取消；已选但未点算符 → 改选；已选且已点算符 → 立即合并。", "选择语义：")
bullet("点算符前必须已选一张牌；否则抛“先点一个数字”。", "算符：")
bullet("合并时计算精确值，除零抛错且不改变状态；生成 step { leftRef, rightRef, operator }，并压入 history 快照。", "合并：")
bullet("撤销弹出上一个快照，恢复 cards / selected / pendingOp / steps；不碰计时。", "撤销：")
bullet("cards.length === 1 且 steps.length === 3；此时 toOperations() 产出三步操作树。", "完成条件：")
bullet("previewText 显示“2 ?”“2 − ?”“2 − 4 = -2”三态，供牌面上方提示。", "预览：")
para("前端只知道“合并完成”，不判断是否等于 24；第三次合并完成时，UI 自动调用 submit，把三步操作树和当前 revision 发给服务端。")

h2("3.5", "API 客户端")
bullet("固定 /api 前缀；所有请求带 X-Guest-Id；有 token 时加 Authorization: Bearer；有 body 时加 JSON Content-Type。", "请求：")
bullet("fetch 使用 credentials: 'same-origin'，refresh cookie 才会随 /api/auth 请求发送。", "Cookie：")
bullet("遇到 401 且当前有 access token、且不是 /auth/refresh，会先调 refreshSession 换新 token，再重放原请求一次；失败则清本地登录态。", "401 重试：")
bullet("access token 存 sessionStorage；localStorage 只存“是否登录过”的标记和 guestId；启动时若标记为 1，静默 refresh 恢复登录。", "存储：")
bullet("每次 create/submit/skip/abandon 生成 r-/a-/s-/x- 前缀 + 时间戳 + 随机串的 actionId，供服务端幂等。", "actionId：")
bullet("接口类型是手写的 TypeScript interface，与后端 Java record 人工对齐；没有 OpenAPI 生成器，存在漂移风险。", "类型：")

h2("3.6", "界面与可用性")
bullet("先选模式，选完后才展开难度与开始按钮（渐进披露）；A/B 卡片有选中态与 aria-pressed。", "首页：")
bullet("HUD 显示模式/等级与答对数；时钟 A 倒计时、B 正计时（含罚时）；进度条 A 按剩余时间、B 按答对/目标。", "作答页：")
bullet("牌面显示 A/J/Q/K 角标与数值，红黑花色；合并后的牌只显示数值；分数过长时加 small/tiny 字号。", "牌面：")
bullet("反馈行显示“回答正确”“答案不是 24；总用时 +5 秒”“已跳过；剩余时间 −10 秒”等；错误用红色。", "反馈：")
bullet("退出有二次确认弹窗；跳题不弹确认，直接发请求；开始失败用 alert，其余失败用行内文案或 toast。", "操作：")
bullet("最大宽度 560 px、safe-area、100dvh、560/720 px 媒体查询、hover 仅精确指针、prefers-reduced-motion。", "移动端：")
bullet("aria-pressed、aria-live、aria-label、role=dialog 已有；没有完整键盘导航、焦点陷阱或屏幕阅读器回归测试。", "可访问性：")

h2("3.7", "前端边界")
for s_ in [
    "刷新丢局：没有持久化 gameId，刷新回首页；后端原局仍在，但前端不会自动接回。",
    "没有错误边界；异步视图失败只显示一行“加载失败”，没有重试按钮。",
    "以 innerHTML 模板为主；昵称等少数服务端字符串有 esc()，新增字段容易漏转义。",
    "现有 24 个用例是 jsdom + fake timers + fetch stub；本次另补了 headless Chrome E2E 11 项，但仍没有真机/多浏览器矩阵。",
    "成绩/榜单时间直接截取 ISO 字符串显示，线上是 UTC，和本地时间差 8 小时（见 7.1 R7）。",
    "没有离线/PWA、深色模式、国际化；中文文案硬编码在 main.ts。",
    "main.ts 单文件 1,076 行，视图、事件、时钟、弹窗都在一起，后续修改的回归面较大。",
]:
    bullet(s_)

# ---------------- chapter 5 ----------------
h1("四、", "后端架构与模块")
h2("4.1", "技术栈")
table_caption("表 4-1  后端选型")
table(
    ["项目", "选型", "说明"],
    [
        ("框架", "Spring Boot 3.3.4", "Java 21；Maven Wrapper 3.9.9"),
        ("Web", "spring-boot-starter-web", "REST JSON；Tomcat 线程上限 50"),
        ("数据访问", "spring-boot-starter-jdbc + JdbcTemplate", "手写 SQL；没有 JPA / MyBatis"),
        ("迁移", "Flyway core + flyway-database-postgresql", "启动时执行 db/migration"),
        ("安全", "spring-boot-starter-security + oauth2-resource-server", "无状态 JWT 资源服务器"),
        ("校验", "spring-boot-starter-validation", "主要在 Service 内手工校验"),
        ("分数", "commons-numbers-fraction 1.2", "精确有理数"),
        ("连接池", "HikariCP（Boot 默认）", "开发 10，线上 8"),
        ("测试", "spring-boot-starter-test", "JUnit 5 / MockMvc / AssertJ"),
    ],
    [2.6, 6.6, 7.4],
    font_size=8.8,
    header_size=8.8,
    first_col_bold=True,
)

h2("4.2", "包结构与职责")
table_caption("表 4-2  后端模块")
table(
    ["包", "文件", "行数", "关键类与职责"],
    [
        ("api", "4", "185", "GameController、ApiException、ErrorResponse、GlobalExceptionHandler；健康检查与统一错误"),
        ("auth", "11", "987", "AuthController/Service、TokenService、GuestClaimService、AccountGuardFilter、PlayerArgumentResolver、AuthRateLimiter、JwtConfig、Player"),
        ("config", "3", "117", "SecurityConfig、WebConfig、ClockConfig"),
        ("game", "7", "623", "GameService（建局/提交/跳题/退出/记录/结算）、GameRow、GameView、PuzzleRow、PuzzleView、RecordsView、GameStatus"),
        ("leaderboard", "2", "227", "LeaderboardController/Service；四个榜、我的排名、昵称脱敏"),
        ("puzzle", "2", "135", "PuzzleRepository（加载/洗牌）、PuzzleGenerator（离线生成）"),
        ("rules", "6", "201", "GameRules（求解）、ExpressionEvaluator（校验）、Operator、OperationStep、Mode、Level"),
        ("根", "1", "11", "DemoApplication"),
        ("合计", "36", "2,486", "—"),
    ],
    [2.6, 1.6, 1.8, 10.6],
    font_size=8.6,
    header_size=8.6,
    first_col_bold=True,
    align_center={1, 2},
)

h2("4.3", "请求处理链")
bullet("无状态；CSRF 关闭、CORS 关闭、basic/form 登录关闭、frame deny；SecurityConfig 只把 /api/auth/me 设为 authenticated，其余 /api/** 放行；/api/leaderboard/me 在 Controller 里手工要求 JWT，对局归属在 Service 校验。", "SecurityFilterChain：")
bullet("JWT 签名通过后，再查账号是否存在、是否 ACTIVE、token_version 是否与 JWT 的 tv 一致；不一致直接 401 JSON。这样封禁/改密后旧 access token 立即失效。", "AccountGuardFilter：")
bullet("有 JWT 就解析 subject 为 Player.of(accountId)；否则读 X-Guest-Id，按 8–64 位正则校验；缺失/非法返回 400 GUEST_ID_REQUIRED。", "PlayerArgumentResolver：")
bullet("Controller 返回 record，Jackson 序列化；ApiException 映射为 {code, message}；未处理异常记录日志并返回 500，不暴露堆栈。", "错误：")
bullet("没有统一的请求审计/操作日志；只有未处理异常会打 error 日志。", "可观测性：")

h2("4.4", "对局服务（GameService）")
table_caption("表 4-3  对局操作")
table(
    ["操作", "服务端行为"],
    [
        ("create", "生成 gameId；复制整副 deck；A 写 deadline；INSERT ... ON CONFLICT DO NOTHING；重复 requestId 返回已有局；开第一题"),
        ("load", "SELECT ... FOR UPDATE；校验归属；A 已到期则补结算；返回 GameView"),
        ("submit", "actionId 幂等；校验 revision/状态/题目 OPEN/未过期；重算三步；正确则 SOLVED、correct+1、记 last_scoring；错误则 WRONG、wrong+1、罚时；advance"),
        ("skip", "actionId 幂等；校验 revision/状态/题目 OPEN/未过期；SKIPPED、skipped+1、罚时；A 到期结算；advance"),
        ("abandon", "actionId 幂等；revision 校验；RUNNING → ABANDONED、finished_at；不写 game_results"),
        ("records", "limit 夹到 1–100；按账号或游客查历史；返回 history + bests"),
    ],
    [2.6, 14.0],
    font_size=8.6,
    header_size=8.6,
    first_col_bold=True,
)
bullet("所有写操作在 @Transactional 内；同一局用 SELECT ... FOR UPDATE 串行化；revision 做客户端乐观并发校验。", "事务与锁：")
bullet("game_actions 的 (game_id, action_id) 唯一；同一 actionId + 相同 fingerprint 返回当前局，不同 fingerprint 返回 409 ACTION_REUSED。response_jsonb 存了但没有被回放使用。", "幂等：")
bullet("submit 正确后更新 correct_count 与 last_scoring_ms；B 模式达到 10 时 finish；错误则把 deadline 往前扣（A），B 只累加 penalty_ms。", "计数与罚时：")
bullet("finish 先 INSERT game_results（game_id 唯一，保证一局只结算一次），再更新 games 状态，再按严格更优条件 upsert personal_bests；A 零题直接返回，不建最佳。", "结算：")
bullet("advance 先看是否已结束、A 是否到期、当前题是否还 OPEN；否则开下一题；B 已答满则结算；deck 耗尽时重新洗牌（该路径有缺陷，见 7.1 R9）。", "下一题：")

h2("4.5", "判题内核")
para("判题分两层：离线求解器与在线求值器。")
bullet("GameRules.solvable 递归地从当前数字集合中取两张、套一个算符、放回结果，直到只剩一个数；减法/除法尝试两种操作数顺序；全程 Fraction，无浮点、无缓存。", "求解器：")
bullet("ExpressionEvaluator 对提交的三步操作树逐条校验：恰好三步；引用必须已存在；每个引用只能被消费一次；算符必须属于该难度；除零拒绝；最终根必须是 s2；除根以外的中间结果必须被消费；四张原始牌必须各用一次。", "求值器：")
bullet("校验失败抛 IllegalArgumentException；GameService 包成 422 INVALID_STEPS；其他请求参数问题由 Controller/全局处理器映射为 400。", "错误：")
bullet("求解器只用于离线题池生成与测试，没有对外的“提示/答案”接口。", "边界：")
para("服务端只接收操作树，不接收表达式字符串，因此不需要解析用户输入；这减少了注入与括号歧义，但不能阻止玩家用外部求解器辅助作弊（见 7.1 R5）。")

h2("4.6", "题池")
bullet("PuzzleGenerator 固定 MIN=1、MAX=13，穷举非降序四元组，校验候选数 1,820、L1 220、L2 1,362；不符直接抛错，避免静默生成错池。", "生成：")
bullet("输出 JSON 数组到 src/main/resources/puzzles/；PuzzleRepository 启动时从 classpath 读入，文件缺失直接启动失败。", "加载：")
bullet("deckFor(level) 复制一份并 Collections.shuffle；poolSize 提供给测试/诊断。", "洗牌：")
bullet("games.deck 存整副牌，deck_position 指向下一题；一局内按顺序取，不重复；耗尽后重洗。", "对局：")

h2("4.7", "账号与令牌")
table_caption("表 4-4  令牌与密码")
table(
    ["项目", "实现"],
    [
        ("Access Token", "JWT HS256，30 分钟；claims：iss=game24、sub=accountId、iat、exp、jti、nick、tv；Authorization: Bearer"),
        ("Refresh Token", "32 字节随机串，Base64URL；只存 SHA-256；HttpOnly、SameSite=Strict、path=/api/auth；30 天；每次刷新轮换"),
        ("重放检测", "旧 refresh 被再次使用且 replaced_by 非空 → 撤销该账号全部未撤销 refresh，返回 401"),
        ("密码", "BCrypt 成本 12；数据库只存哈希；用户名不存在也跑一次 dummy hash"),
        ("限流", "注册 10 次/小时/IP；登录 60 次/10 分钟/IP；同一 IP+用户名失败 8 次/15 分钟锁定；内存固定窗口"),
        ("账号守卫", "JWT 的 tv 必须等于 accounts.token_version；封禁/改密把版本 +1 即可让旧 token 失效"),
        ("游客合并", "锁账号行；更新 games/game_results 的 account_id；删除游客 personal_bests；按严格更优 upsert 账号最佳"),
    ],
    [3.4, 13.2],
    font_size=8.6,
    header_size=8.6,
    first_col_bold=True,
)
para("当前没有找回密码、修改密码、封禁/解封的 HTTP 接口；token_version 机制已经预留，但实际操作仍要直接改数据库。")

h2("4.8", "排行榜")
bullet("榜单不单独建表，直接从 personal_bests 派生；每个账号每个模式×难度只有一条，天然不会重复占名次。", "数据源：")
bullet("JOIN accounts 且 status='ACTIVE'；A 按 best_correct DESC、best_scoring_ms ASC、achieved_at ASC、account_id ASC；B 按 best_scoring_ms ASC、achieved_at ASC、account_id ASC。", "排序：")


bullet("昵称隐藏第一个 Unicode 码点；total 单独 count；page/size 夹取；offset > 5,000 返回 400。", "展示：")
bullet("standing(account, mode, level) 先取自己的最佳，再 count 排在自己前面的人 +1；standings 返回四个榜。", "我的排名：")
bullet("没有缓存、没有物化视图、没有榜单快照；每次请求实时查 personal_bests。", "缓存：")

h2("4.9", "接口一览")
table_caption("表 4-5  HTTP API（14 个）")
table(
    ["方法与路径", "身份", "用途", "主要错误"],
    [
        ("POST /api/auth/register", "公开", "注册并登录；username/password/nickname/guestId?", "409 USERNAME_TAKEN；400 格式；429"),
        ("POST /api/auth/login", "公开", "登录；username/password/guestId?", "401 INVALID_CREDENTIALS；403 ACCOUNT_BANNED；429"),
        ("POST /api/auth/refresh", "Cookie", "轮换 refresh，返回新 access token", "401 UNAUTHORIZED"),
        ("POST /api/auth/logout", "Cookie", "撤销 refresh 并清 cookie", "—"),
        ("GET /api/auth/me", "Bearer", "当前账号", "401 UNAUTHORIZED"),
        ("POST /api/games", "公开/游客", "建局；requestId/mode/level", "400；500（字段缺失时见 7.1 R10）"),
        ("GET /api/games/{id}", "所有者", "读取/恢复；A 到期补结算", "403 PLAYER_MISMATCH；404 GAME_NOT_FOUND"),
        ("POST /api/games/{id}/submit", "所有者", "提交三步操作树", "409 REVISION_MISMATCH / GAME_CLOSED / GAME_EXPIRED / PUZZLE_CLOSED / ACTION_REUSED；422 INVALID_STEPS"),
        ("POST /api/games/{id}/skip", "所有者", "跳题并罚时", "409 同上；404；403"),
        ("POST /api/games/{id}/abandon", "所有者", "退出，本局无效", "409 REVISION_MISMATCH"),
        ("GET /api/records", "公开/游客", "最近历史 + 最佳；limit/mode/level", "400 INVALID_MODE / INVALID_LEVEL"),
        ("GET /api/leaderboard", "公开", "榜单 + 我的排名；mode/level/page/size", "400 INVALID_MODE / INVALID_LEVEL / PAGE_OUT_OF_RANGE"),
        ("GET /api/leaderboard/me", "Bearer", "四个榜我的排名", "401 UNAUTHORIZED"),
        ("GET /api/health", "公开", "应用与数据库健康", "503（数据库不可用）"),
    ],
    [4.9, 2.1, 4.4, 5.2],
    font_size=8.2,
    header_size=8.2,
)

h2("4.10", "错误码")
table_caption("表 4-6  主要错误码")
table(
    ["HTTP", "错误码", "含义"],
    [
        ("400", "BAD_REQUEST / GUEST_ID_REQUIRED", "请求体或访客标识不合法"),
        ("400", "INVALID_USERNAME / NICKNAME / PASSWORD / GUEST_ID", "注册/登录字段格式不符"),
        ("400", "INVALID_MODE / INVALID_LEVEL / PAGE_OUT_OF_RANGE", "参数取值或翻页越界"),
        ("401", "UNAUTHORIZED / INVALID_CREDENTIALS", "未登录、令牌失效或用户名密码错误"),
        ("403", "FORBIDDEN / ACCOUNT_BANNED / PLAYER_MISMATCH", "无权限、账号封禁、对局不属于当前玩家"),
        ("404", "GAME_NOT_FOUND", "对局不存在"),
        ("409", "USERNAME_TAKEN / REVISION_MISMATCH / GAME_CLOSED", "用户名占用、版本冲突、对局已结束"),
        ("409", "GAME_EXPIRED / PUZZLE_CLOSED / ACTION_REUSED", "已过期、题目已关闭、同一 actionId 用于不同请求"),
        ("422", "INVALID_STEPS", "三步操作树不合法"),
        ("429", "TOO_MANY_ATTEMPTS", "登录/注册限流"),
        ("500", "INTERNAL_ERROR", "未处理异常（不暴露堆栈）"),
        ("503", "—", "健康检查中数据库不可用"),
    ],
    [1.8, 6.4, 8.4],
    font_size=8.6,
    header_size=8.6,
    align_center={0},
)

h2("4.11", "关键配置")
table_caption("表 4-7  配置项（环境变量可覆盖）")
table(
    ["配置", "默认", "说明"],
    [
        ("DB_URL", "jdbc:postgresql://127.0.0.1:55432/game24", "数据库地址"),
        ("DB_USERNAME / DB_PASSWORD", "game24 / game24_local_only", "数据库账号；生产必须改"),
        ("DB_POOL_SIZE", "10", "Hikari 连接池；线上 compose 设为 8"),
        ("JWT_SECRET", "开发默认值", "≥32 字节；生产必须覆盖"),
        ("ACCESS_TTL / REFRESH_TTL", "PT30M / P30D", "Access 30 分钟；Refresh 30 天"),
        ("COOKIE_SECURE", "false", "HTTPS 生产应为 true"),
        ("FORWARD_HEADERS_STRATEGY", "none", "反向代理后设 framework"),
        ("SERVER_PORT", "8080", "应用端口"),
        ("TOMCAT_MAX_THREADS", "50", "Tomcat 最大线程"),
        ("game24.a-duration-ms", "300000", "A 模式总时长"),
        ("game24.b-target-correct", "10", "B 模式目标题数"),
        ("game24.wrong-penalty-ms / skip-penalty-ms", "5000 / 10000", "答错/跳题罚时"),
    ],
    [5.4, 5.2, 6.0],
    font_size=8.4,
    header_size=8.4,
    first_col_bold=True,
)

# ---------------- chapter 6 ----------------
h1("五、", "数据模型")
h2("5.1", "七张业务表")
table_caption("表 5-1  表清单与关键约束")
table(
    ["表", "作用", "关键约束 / 索引"],
    [
        ("accounts", "账号", "username 唯一；status ∈ ACTIVE/BANNED；token_version ≥0"),
        ("refresh_tokens", "刷新令牌", "token_hash char(64) 唯一；revoked_at / replaced_by；account_id 索引"),
        ("games", "对局进行态", "owner = account 或 guest；request_id 幂等；status ∈ RUNNING/FINISHED/ABANDONED；revision；deck jsonb；finished 一致性 CHECK"),
        ("game_puzzles", "一局中的题目", "(game_id, sequence_no) 唯一；status 为 text（OPEN/SOLVED/WRONG/SKIPPED）"),
        ("game_actions", "动作幂等记录", "(game_id, action_id) 唯一；action_type；fingerprint；response_jsonb"),
        ("game_results", "已结算成绩", "game_id 唯一；counts、actual/penalty/scoring、started/finished"),
        ("personal_bests", "每账号/游客最佳", "owner 二选一 CHECK；result_id 唯一；(account/guest, mode, level) 唯一"),
        ("flyway_schema_history", "迁移版本", "Flyway 自动维护"),
    ],
    [3.4, 3.6, 9.6],
    font_size=8.4,
    header_size=8.4,
    first_col_bold=True,
)
para("另有 PostgreSQL 枚举 game_mode（A/B）、game_level（L1/L2）、game_status（RUNNING/FINISHED/ABANDONED）。game_puzzles.status 没有用枚举，也没有 CHECK 约束，靠代码写入四个值。")

h2("5.2", "关系")
bullet("accounts 1–N refresh_tokens / games / game_results / personal_bests；账号删除时级联。", "账号：")
bullet("games 1–N game_puzzles / game_actions；games 1–1 game_results（game_id UNIQUE）。", "对局：")
bullet("game_results 1–1 personal_bests.result_id；一条成绩最多被一个最佳引用。", "成绩：")
bullet("personal_bests 的 owner 二选一：account_id 非空或 guest_id 非空，不允许同时为空/同时非空。", "最佳：")

h2("5.3", "状态与结算")
figure(os.path.join(os.path.dirname(__file__), "report_fig2_lifecycle.png"), 16.4,
       "图 2  对局状态与结算链路。RUNNING 的每次提交/跳题都会开下一题；FINISHED 写成绩与最佳；ABANDONED 不写成绩。")

h2("5.4", "几个设计取舍（现状）")
bullet("没有单独的排行榜表；榜单直接查 personal_bests，避免“最佳更新了、榜没更新”的不一致。", "排行榜派生：")
bullet("account 与 guest 各自一条唯一约束；账号用部分唯一索引（WHERE account_id IS NOT NULL），游客用普通唯一约束。", "双 owner：")
bullet("A 榜与 B 榜各有一条部分索引，匹配排序字段；查询走索引，但未做过大规模数据验证。", "索引：")
bullet("games.deck 存整副牌；L2 每局会把 1,362 组牌写进 jsonb，存在明显写放大。", "deck：")
bullet("game_actions 只增不删；目前没有清理/归档任务。", "动作表：")
bullet("成绩历史就是 game_results；没有单独的历史表，也没有软删除。", "历史：")

h2("5.5", "数据保留与备份")
bullet("线上每日 03:00 用 pg_dump -Fc 备份，gzip 后保留 14 天；备份文件与数据库在同一台机器。", "备份：")
bullet("没有异地备份、没有 PITR、没有恢复演练记录（部署记录里有一次空库恢复测试）。", "恢复：")
bullet("没有数据归档/清理策略；账号、对局、动作、成绩都会持续增长。", "保留：")
bullet("开发库可随时清空；线上演示数据在部署记录中提供了一条 TRUNCATE 清理命令。", "清理：")