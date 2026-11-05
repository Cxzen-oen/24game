
from PIL import Image, ImageDraw, ImageFont
import os

W, H = 1800, 1200
BG = "#F7F9FC"
NAVY = "#0F3D5C"
TEAL = "#1E7A55"
GREY = "#5A6670"
LINE = "#C9D8E3"
CARD = "#FFFFFF"
SOFT = "#EAF1F6"

B = "C:/Windows/Fonts/msyhbd.ttc"
R = "C:/Windows/Fonts/msyh.ttc"

def f(size, bold=False):
    return ImageFont.truetype(B if bold else R, size)

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)

def rr(x1, y1, x2, y2, radius=18, fill=CARD, outline=LINE, width=2):
    d.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=fill, outline=outline, width=width)

def text(x, y, s, size=24, bold=False, color=NAVY, anchor="la"):
    d.text((x, y), s, font=f(size, bold), fill=color, anchor=anchor)

def center(x, y, s, size=24, bold=False, color=NAVY):
    text(x, y, s, size, bold, color, "mm")

def arrow(x1, y1, x2, y2, color=NAVY, width=4):
    d.line([x1, y1, x2, y2], fill=color, width=width)
    # arrow head
    import math
    ang = math.atan2(y2-y1, x2-x1)
    L = 16
    for s in (-0.5, 0.5):
        d.line([x2, y2, x2 - L*math.cos(ang+s), y2 - L*math.sin(ang+s)], fill=color, width=width)

# Browser
rr(300, 60, 1500, 240, 24, CARD, NAVY, 3)
center(900, 92, "浏览器（桌面 / 移动）", 30, True)
center(900, 138, "Vite + TypeScript 单页应用：选模式、点牌合并、计时展示、成绩与排行", 23, False, GREY)
center(900, 180, "只负责输入与展示；Access Token 存 sessionStorage，Refresh Token 为 HttpOnly Cookie", 21, False, GREY)
center(900, 214, "游客用 localStorage 中的 guestId 标识；登录后游客成绩并入账号", 21, False, GREY)

# arrow
arrow(900, 240, 900, 300)
text(930, 270, "同源 HTTP / JSON  ·  /api", 22, False, TEAL, "lm")

# container
rr(70, 300, 1730, 810, 26, SOFT, NAVY, 3)
text(110, 330, "Spring Boot 3.3.4 单体应用 · Java 21 · 可执行 jar", 30, True, NAVY)
text(110, 370, "Spring Security（无状态 JWT）· Spring JDBC · Flyway · HikariCP", 21, False, GREY)

cards = [
    ("账号与令牌  auth", "注册 / 登录 / 刷新 / 退出；BCrypt(12)；JWT HS256；\n刷新令牌轮换与重放检测；游客成绩并入账号"),
    ("对局与判题  game / rules", "三步合并逐条校验；有理数精确判题；\n服务端计时、罚时、结算与幂等动作"),
    ("题池  puzzle", "L1 220 组、L2 1362 组；离线穷举生成；\n开局洗牌，题池耗尽后重置"),
    ("排行榜  leaderboard", "A/B × L1/L2 四个榜；直接由最佳成绩派生；\n昵称脱敏、我的排名、分页"),
    ("接口与静态资源  api", "REST JSON；统一错误码；/api/health；\n生产环境把前端构建产物打进 jar"),
    ("配置与安全  config", "SecurityFilterChain；UTC Clock；\nPlayer 参数解析（账号或游客）"),
]
cw, ch = 500, 160
xs = [110, 650, 1190]
ys = [400, 575]
for i, (title, body) in enumerate(cards):
    x = xs[i % 3]; y = ys[i // 3]
    rr(x, y, x+cw, y+ch, 18, CARD, LINE, 2)
    d.rectangle([x, y, x+8, y+ch], fill=TEAL if i % 2 == 0 else NAVY)
    text(x+26, y+20, title, 25, True, NAVY)
    ty = y+62
    for line in body.split("\n"):
        text(x+26, ty, line, 20, False, GREY)
        ty += 30

# arrow to DB
arrow(900, 810, 900, 878)
text(930, 844, "JDBC  ·  HikariCP（开发 10 / 线上 8 连接）", 22, False, TEAL, "lm")

# DB
rr(180, 878, 1620, 1042, 24, CARD, NAVY, 3)
center(900, 910, "PostgreSQL 16 或 18.1（开发）/ 14（线上）", 30, True)
center(900, 952, "accounts · refresh_tokens · games · game_puzzles · game_actions · game_results · personal_bests", 21, False, GREY)
center(900, 992, "账号、对局进行态、题目、幂等动作、成绩、每个账号的最佳成绩都在这里；写操作在事务内", 21, False, GREY)

# footer facts
rr(70, 1070, 1730, 1160, 18, "#FFFFFF", LINE, 2)
facts = [
    ("开发", "Vite :5173 代理 /api → Spring Boot :8080"),
    ("线上", "systemd game24.service · :8081 · 当前 HTTP"),
    ("备份", "每日 03:00 pg_dump -Fc · 保留 14 天"),
]
fx = [100, 650, 1200]
for (k, v), x in zip(facts, fx):
    text(x, 1092, k, 20, True, TEAL)
    text(x, 1124, v, 19, False, GREY)

img.save(r"D:\24game\docs\report_fig1_architecture.png")
print("saved", img.size)