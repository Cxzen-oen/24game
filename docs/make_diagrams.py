"""Draw architecture diagrams for the 24-point competitive game proposal.

Outputs PNG files into ./diagrams. Uses only Pillow (bundled with the runtime).
"""
from __future__ import annotations

import os

from PIL import Image, ImageDraw, ImageFont

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "diagrams")
os.makedirs(OUT, exist_ok=True)

S = 3  # supersampling factor

FONT_CANDIDATES = [
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\msyhbd.ttc",
    r"C:\Windows\Fonts\simhei.ttf",
]


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = FONT_CANDIDATES[1 if bold else 0]
    return ImageFont.truetype(path, int(size * S))


def card(img):
    """Trim uniform outer margins only (never cut into the drawing)."""
    return img


# ---------------------------------------------------------------- palette
BG = "#FFFFFF"
TEXT = "#1F2328"
MUTED = "#5B6470"
LINE = "#8A94A0"

FILL_BLUE = "#E8F0FE"
STROKE_BLUE = "#4C7FE0"
FILL_GREEN = "#E6F4EA"
STROKE_GREEN = "#2F9E5E"
FILL_ORANGE = "#FDEEE0"
STROKE_ORANGE = "#D9822B"
FILL_PURPLE = "#F1E9FB"
STROKE_PURPLE = "#7B55C8"
FILL_GRAY = "#F3F4F6"
STROKE_GRAY = "#9AA3AD"
FILL_RED = "#FDECEC"
STROKE_RED = "#C94A4A"


def canvas(w: int, h: int) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (w * S, h * S), BG)
    return img, ImageDraw.Draw(img)


def box(
    d,
    x,
    y,
    w,
    h,
    text,
    fill=FILL_BLUE,
    stroke=STROKE_BLUE,
    size=13,
    bold=True,
    radius=8,
    dash=False,
    sub=None,
    sub_size=10,
):
    xy = [x * S, y * S, (x + w) * S, (y + h) * S]
    if dash:
        # approximate dashed border by drawing segments
        _dashed_round_rect(d, *xy, radius=radius * S, fill=fill, stroke=stroke)
    else:
        d.rounded_rectangle(xy, radius=radius * S, fill=fill, outline=stroke, width=2 * S)
    f = font(size, bold)
    lines = text.split("\n")
    fs = font(sub_size, False) if sub else None
    # measure
    heights = []
    widths = []
    for ln in lines:
        bbox = d.textbbox((0, 0), ln, font=f)
        heights.append(bbox[3] - bbox[1])
        widths.append(bbox[2] - bbox[0])
    total = sum(heights) + (len(lines) - 1) * 4 * S
    if sub:
        for ln in sub.split("\n"):
            bbox = d.textbbox((0, 0), ln, font=fs)
            heights_sub_item = bbox[3] - bbox[1]
            total += heights_sub_item + 6 * S
    cy = (y + h / 2) * S - total / 2
    for ln in lines:
        bbox = d.textbbox((0, 0), ln, font=f)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        d.text(((x + w / 2) * S - tw / 2, cy - bbox[1]), ln, font=f, fill=TEXT)
        cy += th + 4 * S
    if sub:
        cy += 4 * S
        for ln in sub.split("\n"):
            bbox = d.textbbox((0, 0), ln, font=fs)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            d.text(((x + w / 2) * S - tw / 2, cy - bbox[1]), ln, font=fs, fill=MUTED)
            cy += th + 3 * S


def _dashed_round_rect(d, x0, y0, x1, y1, radius, fill, stroke, dash=7, gap=5):
    d.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=fill, outline=None)
    step = (dash + gap) * S
    w = 2 * S
    # horizontal
    x = x0 + radius
    while x < x1 - radius:
        d.line([x, y0, min(x + dash * S, x1 - radius), y0], fill=stroke, width=w)
        d.line([x, y1, min(x + dash * S, x1 - radius), y1], fill=stroke, width=w)
        x += step
    y = y0 + radius
    while y < y1 - radius:
        d.line([x0, y, x0, min(y + dash * S, y1 - radius)], fill=stroke, width=w)
        d.line([x1, y, x1, min(y + dash * S, y1 - radius)], fill=stroke, width=w)
        y += step
    # corners (approx arcs)
    d.arc([x0, y0, x0 + 2 * radius, y0 + 2 * radius], 180, 270, fill=stroke, width=w)
    d.arc([x1 - 2 * radius, y0, x1, y0 + 2 * radius], 270, 360, fill=stroke, width=w)
    d.arc([x0, y1 - 2 * radius, x0 + 2 * radius, y1], 90, 180, fill=stroke, width=w)
    d.arc([x1 - 2 * radius, y1 - 2 * radius, x1, y1], 0, 90, fill=stroke, width=w)


def band(d, x, y, w, h, label, fill=FILL_GRAY, stroke=STROKE_GRAY):
    d.rounded_rectangle(
        [x * S, y * S, (x + w) * S, (y + h) * S],
        radius=10 * S,
        fill=fill,
        outline=stroke,
        width=1 * S,
    )
    d.text((x * S + 12 * S, y * S + 8 * S), label, font=font(10, True), fill=MUTED)


def arrow(d, pts, color=LINE, width=2, label=None, label_pos=None, label_size=9):
    """Polyline with arrow head at the end."""
    p = [(x * S, y * S) for x, y in pts]
    d.line(p, fill=color, width=width * S, joint="curve")
    # arrow head
    import math

    (x1, y1), (x2, y2) = p[-2], p[-1]
    ang = math.atan2(y2 - y1, x2 - x1)
    L = 9 * S
    for da in (math.radians(152), math.radians(-152)):
        d.line(
            [x2, y2, x2 + L * math.cos(ang + da), y2 + L * math.sin(ang + da)],
            fill=color,
            width=width * S,
        )
    if label:
        lx, ly = label_pos if label_pos else ((pts[0][0] + pts[-1][0]) / 2, (pts[0][1] + pts[-1][1]) / 2)
        f = font(label_size, False)
        bbox = d.textbbox((0, 0), label, font=f)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        d.rectangle([lx * S - 2 * S, ly * S - 1 * S, lx * S + w + 2 * S, ly * S + h + 2 * S], fill=BG)
        d.text((lx * S, ly * S - bbox[1]), label, font=f, fill=MUTED)


def title(d, x, y, text, size=15):
    d.text((x * S, y * S), text, font=font(size, True), fill=TEXT)


# ============================================================ Figure 1
def fig1():
    W, H = 1100, 760
    img, d = canvas(W, H)
    title(d, 24, 16, "图 1  系统分层架构")

    # client
    band(d, 24, 54, 1052, 108, "客户端层（浏览器）")
    box(d, 40, 78, 150, 62, "大厅 / 房间列表", FILL_BLUE, STROKE_BLUE, 12)
    box(d, 202, 78, 150, 62, "拼算式输入 UI", FILL_BLUE, STROKE_BLUE, 12)
    box(d, 364, 78, 150, 62, "倒计时 / 进度", FILL_BLUE, STROKE_BLUE, 12)
    box(d, 526, 78, 150, 62, "对战面板", FILL_BLUE, STROKE_BLUE, 12)
    box(d, 688, 78, 150, 62, "个人战绩 / 榜单", FILL_BLUE, STROKE_BLUE, 12)
    box(d, 850, 78, 210, 62, "本地语法即时提示\n（仅提示，不判题）", FILL_BLUE, STROKE_BLUE, 11, sub=None, sub_size=9)

    # gateway
    box(d, 300, 190, 500, 46, "Nginx / 负载均衡  ·  TLS 终结 · WebSocket 升级", FILL_GRAY, STROKE_GRAY, 12)

    # server band
    band(d, 24, 262, 1052, 250, "服务端")
    # API
    box(d, 40, 286, 300, 210, "API 服务（无状态，可水平扩容）", FILL_GREEN, STROKE_GREEN, 12,
        sub="账号与鉴权（JWT）\n对局与个人战绩查询\n首版无排行榜接口", sub_size=10)
    # Realtime cluster
    box(d, 360, 286, 500, 210, "实时对局服务（Colyseus，有状态）", FILL_ORANGE, STROKE_ORANGE, 12,
        sub="MatchRoom：仅 2 人同房\n服务端权威计时 · 判题 · 结算\n断线重连 · 优雅关闭", sub_size=10)
    # small room procs
    box(d, 378, 404, 148, 76, "房间进程 1", FILL_GRAY, STROKE_GRAY, 11)
    box(d, 536, 404, 148, 76, "房间进程 2", FILL_GRAY, STROKE_GRAY, 11)
    box(d, 694, 404, 148, 76, "房间进程 N", FILL_GRAY, STROKE_GRAY, 11)
    # worker
    box(d, 880, 286, 180, 210, "存档任务", FILL_PURPLE, STROKE_PURPLE, 12,
        sub="持久化队列\n事务 + 幂等\n失败标记无效", sub_size=10)

    # data band
    band(d, 24, 546, 1052, 128, "数据层")
    box(d, 40, 570, 320, 90, "PostgreSQL（权威数据）", FILL_GREEN, STROKE_GREEN, 12,
        sub="账号 · 对局记录 · 最好记录", sub_size=10)
    box(d, 380, 570, 320, 90, "存档任务（首版进程内）", FILL_RED, STROKE_RED, 12,
        sub="PostgreSQL 事务 + 唯一 matchId\n可靠重试，不改写终态", sub_size=10)
    box(d, 720, 570, 340, 90, "经典四则题池（离线生成）", FILL_PURPLE, STROKE_PURPLE, 12,
        sub="1–13 可解牌组 + 私有标准解", sub_size=10)

    # arrows
    arrow(d, [(550, 140), (550, 188)], label="HTTPS / WSS", label_pos=(560, 156))
    arrow(d, [(380, 236), (380, 284)], label="REST", label_pos=(392, 250))
    arrow(d, [(720, 236), (720, 284)], label="WebSocket", label_pos=(732, 250))
    arrow(d, [(240, 390), (356, 390)])
    arrow(d, [(860, 390), (878, 390)], label="结果入队", label_pos=(862, 362))
    arrow(d, [(940, 496), (940, 546)], label="任务落库", label_pos=(950, 514))
    arrow(d, [(550, 496), (550, 544)], label="房间注册", label_pos=(560, 514))

    img = img.resize((W, H), Image.LANCZOS)
    img = card(img)
    img.save(os.path.join(OUT, "fig1_architecture.png"), dpi=(220, 220))


# ============================================================ Figure 2
def fig2():
    W, H = 1100, 620
    img, d = canvas(W, H)
    title(d, 24, 16, "图 2  一局对战的消息时序")

    cols = [
        ("玩家 A\n(客户端)", FILL_BLUE, STROKE_BLUE, 120),
        ("玩家 B\n(客户端)", FILL_BLUE, STROKE_BLUE, 250),
        ("MatchRoom\n(房间进程)", FILL_ORANGE, STROKE_ORANGE, 420),
        ("规则内核\n(rules 纯函数)", FILL_PURPLE, STROKE_PURPLE, 600),
        ("PostgreSQL", FILL_GREEN, STROKE_GREEN, 790),
    ]
    for name, fill, stroke, x in cols:
        box(d, x, 56, 160, 54, name, fill, stroke, 11)
        d.line([(x + 80) * S, 110 * S, (x + 80) * S, 560 * S], fill="#C9CED6", width=1 * S)

    XA, XB, XR, XK, XD = 200, 330, 500, 680, 870

    steps = [
        (140, "Hello 配对 / 预留座位"),
        (178, "Join（携带 JWT）"),
        (216, "room.join"),
        (254, "roomJoined：玩家列表、等级、模式"),
        (292, "start：统一倒计时开始"),
        (330, "puzzle：四张牌 + puzzleSeq（不含答案）"),
        (368, "submit：表达式 + puzzleSeq"),
        (406, "validate(expr)：有理数精确求值"),
        (444, "ok / 非法 → 更新个人成绩"),
        (482, "score 广播（仅名次与进度）"),
        (520, "matchEnd：名次 + 用时 / 题数"),
    ]
    for y, label in steps:
        d.text((24 * S, (y - 6) * S), label, font=font(9, False), fill=MUTED)

    arrow(d, [(XA, 140), (XR, 140)], label=None)  # A -> room (via matchmaker, simplified)
    arrow(d, [(XB, 178), (XR, 178)])
    arrow(d, [(XR, 216), (XA, 216)])
    arrow(d, [(XR, 254), (XA, 254)])
    arrow(d, [(XR, 292), (XA, 292)])
    arrow(d, [(XR, 330), (XA, 330)])
    arrow(d, [(XA, 368), (XR, 368)])
    arrow(d, [(XR, 406), (XK, 406)])
    arrow(d, [(XK, 444), (XR, 444)])
    arrow(d, [(XR, 482), (XA, 482)])
    arrow(d, [(XR, 482), (XB, 482)])

    # settle -> queue -> db
    d.line([(XR + 80) * S, 520 * S, XD * S, 520 * S], fill=LINE, width=2 * S)
    arrow(d, [(XD, 520), (XD, 512)])
    # queue note
    box(d, 790, 430, 240, 60, "唯一 matchId + 事务\n失败重试，最终标无效", FILL_GRAY, STROKE_GRAY, 10, radius=6)

    img = img.resize((W, H), Image.LANCZOS)
    img = card(img)
    img.save(os.path.join(OUT, "fig2_message_flow.png"), dpi=(220, 220))


# ============================================================ Figure 3
def fig3():
    W, H = 1100, 520
    img, d = canvas(W, H)
    title(d, 24, 16, "图 3  规则内核与题池：生成、下发与判题")

    # operator pools
    box(d, 24, 60, 200, 130, "加减级", FILL_GREEN, STROKE_GREEN, 13,
        sub="只许 + −\n数字 1–13", sub_size=10)
    box(d, 24, 200, 200, 130, "四则级", FILL_GREEN, STROKE_GREEN, 13,
        sub="+ − × ÷\n数字 1–13", sub_size=10)
    box(d, 24, 340, 200, 130, "扩展级", FILL_GRAY, STROKE_GRAY, 13,
        sub="再加 幂 · 开方 · 阶乘\n数字 1–12", sub_size=10, dash=True)

    # enumerator
    box(d, 270, 60, 210, 410, "题池生成器\n（离线）", FILL_ORANGE, STROKE_ORANGE, 13,
        sub="生成参数\n（数字范围 · 算符池\n· 最少解数）\n→ 穷举牌组\n→ 可解率校验\n→ 判题器复算\n→ 单局不重复抽样", sub_size=10)

    # pool files
    box(d, 530, 60, 220, 160, "pools/{l1,l2,l3}.json", FILL_GRAY, STROKE_GRAY, 11,
        sub="升序牌组 + 私有标准解\n只收至少一解的牌组\n发布前完整校验", sub_size=10)
    box(d, 530, 240, 220, 230, "开局固定题序", FILL_BLUE, STROKE_BLUE, 11,
        sub="双方题目与顺序相同\n前段偏易 · 末段加压\n逐题下发，不能跳题\n单题 60 秒超时\n限时赛预备 100 题", sub_size=10)

    # runtime
    box(d, 790, 60, 286, 120, "运行期：题面下发", FILL_BLUE, STROKE_BLUE, 12,
        sub="只发 4 个数字 + puzzleSeq + 难度\n标准解留在服务端私有字段", sub_size=10)
    box(d, 790, 200, 286, 140, "运行期：判题", FILL_PURPLE, STROKE_PURPLE, 12,
        sub="点牌合并：逐条校验合并链\n步数 = 3 · 除零直接拒绝\n扩展级：安全解析器（禁止 eval）\n有理数求值 == 24", sub_size=9)
    box(d, 790, 360, 286, 90, "严格约束", FILL_RED, STROKE_RED, 12,
        sub="全程分数运算，不用浮点比较", sub_size=10, dash=True)

    arrow(d, [(224, 125), (268, 170)])
    arrow(d, [(224, 265), (268, 250)])
    arrow(d, [(480, 140), (528, 140)])
    arrow(d, [(640, 220), (640, 238)])
    arrow(d, [(752, 350), (788, 350)], label="抽题", label_pos=(756, 330))

    img = img.resize((W, H), Image.LANCZOS)
    img = card(img)
    img.save(os.path.join(OUT, "fig3_rules_pool.png"), dpi=(220, 220))


# ============================================================ Figure 4
def fig4():
    W, H = 1100, 560
    img, d = canvas(W, H)
    title(d, 24, 16, "图 4  代码仓库结构")
    def tree(x, y, depth, name, note=None, color=TEXT, is_dir=True):
        indent = x + depth * 22
        d.text((indent * S, y * S), name, font=font(10, is_dir), fill=color)
        if note:
            bbox = d.textbbox((0, 0), name, font=font(10, is_dir))
            d.text(((indent + (bbox[2] - bbox[0]) / S + 10) * S, y * S), note, font=font(9, False), fill=MUTED)

    cw = W * S
    ch = 700 * S
    d.rounded_rectangle([8 * S, 52 * S, (W - 8) * S, 700 * S], radius=8 * S,
                        fill="#FBFCFD", outline="#D5DAE1", width=1 * S)

    rows = [
        (0, "24game/", None),
        (1, "apps/", None),
        (2, "web/", "React + Vite + TypeScript"),
        (3, "大厅 / 房间 / 对战 / 战绩", "页面层"),
        (3, "features/merge/", "点牌合并、撤销、快捷键与本地预判"),
        (3, "socket/", "Colyseus 客户端封装、断线重连"),
        (2, "server/", "Colyseus 实时服务 + REST API"),
        (3, "rooms/MatchRoom.ts", "房间生命周期、计时、结算、重连"),
        (3, "modules/auth/", "账号、JWT 鉴权"),
        (3, "modules/stats/", "胜负平、定题最快纪录、累计答对题数"),
        (3, "modules/pool/", "题池加载、按档抽样与题序编排"),
        (2, "persistence/", "对局结果可靠重试、事务与幂等"),
        (1, "packages/", None),
        (2, "shared/", "共享事件名、payload 类型、错误码"),
        (2, "rules/", "★ 核心：算符池、合并链校验、解析、求值、判题"),
        (3, "operators.ts", "三档难度的算符白名单（数据驱动）"),
        (3, "parser.ts", "表达式 → 语法树，拒绝非法 token"),
        (3, "evaluate.ts", "分数精确求值"),
        (3, "validate.ts", "合并链校验 + 数字验重 + 白名单规则"),
        (1, "pools/", "l1 / l2 / l3.json（参数化生成、发布前复算）"),
        (1, "scripts/", "题池生成、数据校验、压测脚本"),
        (1, "infra/", "docker-compose、Nginx（单机单实时进程）"),
        (1, "docs/", "规则单、协议、库表、压测报告"),
    ]
    y = 62
    for depth, name, note in rows:
        color = TEXT if depth <= 1 else ("#3B4A5A" if depth >= 2 else TEXT)
        tree(24, y, depth, name, note, color, is_dir=name.endswith("/"))
        y += 22

    # legend
    ly = y + 14
    d.rounded_rectangle([24 * S, ly * S, 1040 * S, (ly + 44) * S], radius=6 * S,
                        fill=FILL_GRAY, outline=STROKE_GRAY, width=1 * S)
    d.text((36 * S, (ly + 14) * S),
           "packages/rules 是唯一判题实现：前端即时预判、服务端最终裁定；算符表与题池参数均为数据驱动。",
           font=font(9, False), fill=MUTED)

    img = img.resize((W, 560), Image.LANCZOS)
    img.save(os.path.join(OUT, "fig4_repo_layout.png"), dpi=(220, 220))


if __name__ == "__main__":
    fig1()
    fig2()
    fig3()
    fig4()
    print("done:", os.listdir(OUT))