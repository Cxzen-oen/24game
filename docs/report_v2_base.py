# -*- coding: utf-8 -*-
from docx import Document
from docx.shared import Pt, Cm, RGBColor, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_BREAK
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import os

NAVY = RGBColor(0x0F, 0x3D, 0x5C)
TEAL = RGBColor(0x1E, 0x7A, 0x55)
GREY = RGBColor(0x5A, 0x66, 0x70)
DARK = RGBColor(0x1F, 0x2A, 0x33)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
WARN = RGBColor(0xB7, 0x79, 0x1F)
HEADBG = "0F3D5C"
LIGHT = "EAF1F6"
SOFT = "F2F7FA"

FONT = "微软雅黑"
MONO = "Consolas"

doc = Document()
sec = doc.sections[0]
sec.page_width = Cm(21.0)
sec.page_height = Cm(29.7)
sec.left_margin = Cm(2.2)
sec.right_margin = Cm(2.2)
sec.top_margin = Cm(2.2)
sec.bottom_margin = Cm(2.0)
sec.header_distance = Cm(1.1)
sec.footer_distance = Cm(0.9)

styles = doc.styles
normal = styles["Normal"]
normal.font.name = FONT
normal.font.size = Pt(10.5)
normal.font.color.rgb = DARK
normal.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
normal.paragraph_format.line_spacing = 1.5
normal.paragraph_format.space_after = Pt(5)

def set_font(run, size=10.5, bold=False, color=DARK, name=FONT, italic=False):
    run.font.name = name
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    rfonts.set(qn("w:eastAsia"), name)
    rfonts.set(qn("w:ascii"), name)
    rfonts.set(qn("w:hAnsi"), name)

def shade(cell, hexcolor):
    tcpr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hexcolor)
    tcpr.append(shd)

def cell_margins(table, top=45, bottom=45, left=80, right=80):
    tblPr = table._tbl.tblPr
    mar = OxmlElement("w:tblCellMar")
    for side, val in (("top", top), ("left", left), ("bottom", bottom), ("right", right)):
        el = OxmlElement("w:" + side)
        el.set(qn("w:w"), str(val))
        el.set(qn("w:type"), "dxa")
        mar.append(el)
    tblPr.append(mar)

def para(text="", size=10.5, bold=False, color=DARK, align=None,
         space_before=0, space_after=5, line=1.5, indent=None, name=FONT, italic=False):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = line
    if align is not None:
        p.alignment = align
    if indent is not None:
        p.paragraph_format.left_indent = Cm(indent)
    if text:
        set_font(p.add_run(text), size, bold, color, name, italic)
    return p

def rich(parts, size=10.5, align=None, space_before=0, space_after=5, line=1.55, indent=None):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = line
    if align is not None:
        p.alignment = align
    if indent is not None:
        p.paragraph_format.left_indent = Cm(indent)
    for text, bold, color in parts:
        set_font(p.add_run(text), size, bold, color if color else DARK)
    return p

def lead(lead_text, text, size=10.5):
    return rich([(lead_text, True, NAVY), (text, False, DARK)], size=size, line=1.55)

def bullet(text, lead_text=None, size=10.2, color=DARK):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(0.62)
    p.paragraph_format.first_line_indent = Cm(-0.36)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.45
    set_font(p.add_run("• "), size, False, TEAL)
    if lead_text:
        set_font(p.add_run(lead_text), size, True, NAVY)
    set_font(p.add_run(text), size, False, color)
    return p

def num_item(n, text, size=10.2):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(0.7)
    p.paragraph_format.first_line_indent = Cm(-0.44)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.45
    set_font(p.add_run(str(n) + ". "), size, True, TEAL)
    set_font(p.add_run(text), size, False, DARK)
    return p

def h1(num, title):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(16)
    p.paragraph_format.space_after = Pt(8)
    p.paragraph_format.keep_with_next = True
    if num:
        set_font(p.add_run(num + "  "), 16, True, TEAL)
    set_font(p.add_run(title), 16, True, NAVY)
    pPr = p._p.get_or_add_pPr()
    pbdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "10")
    bottom.set(qn("w:space"), "4")
    bottom.set(qn("w:color"), "C9D8E3")
    pbdr.append(bottom)
    pPr.append(pbdr)
    ol = OxmlElement("w:outlineLvl")
    ol.set(qn("w:val"), "0")
    pPr.append(ol)
    return p

def h2(num, title):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    set_font(p.add_run("▍ "), 11.5, True, TEAL)
    set_font(p.add_run(num + "  " if num else ""), 11.5, True, TEAL)
    set_font(p.add_run(title), 11.5, True, NAVY)
    pPr = p._p.get_or_add_pPr()
    ol = OxmlElement("w:outlineLvl")
    ol.set(qn("w:val"), "1")
    pPr.append(ol)
    return p

def caption(text, before=3, after=9):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.line_spacing = 1.2
    set_font(p.add_run(text), 8.8, False, GREY)
    return p

def table_caption(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.keep_with_next = True
    set_font(p.add_run(text), 9.2, True, NAVY)
    return p

def set_col_width(cell, cm):
    cell.width = Cm(cm)
    tcPr = cell._tc.get_or_add_tcPr()
    tcW = tcPr.find(qn("w:tcW"))
    if tcW is None:
        tcW = OxmlElement("w:tcW")
        tcPr.append(tcW)
    tcW.set(qn("w:w"), str(int(cm / 2.54 * 1440)))
    tcW.set(qn("w:type"), "dxa")

def table(headers, rows, widths, font_size=8.8, header_size=8.8, align_center=None,
          first_col_bold=False):
    t = doc.add_table(rows=1, cols=len(headers))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.style = "Table Grid"
    t.autofit = False
    t.allow_autofit = False
    tblPr = t._tbl.tblPr
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    tblPr.append(layout)
    cell_margins(t)
    hdr = t.rows[0]
    trPr = hdr._tr.get_or_add_trPr()
    tblHeader = OxmlElement("w:tblHeader")
    trPr.append(tblHeader)
    for i, h in enumerate(headers):
        c = hdr.cells[i]
        set_col_width(c, widths[i])
        shade(c, HEADBG)
        c.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(1)
        p.paragraph_format.space_before = Pt(1)
        p.paragraph_format.line_spacing = 1.2
        set_font(p.add_run(h), header_size, True, WHITE)
    for idx, row in enumerate(rows):
        row_obj = t.add_row()
        trPr2 = row_obj._tr.get_or_add_trPr()
        cantSplit = OxmlElement("w:cantSplit")
        trPr2.append(cantSplit)
        cells = row_obj.cells
        for i, val in enumerate(row):
            c = cells[i]
            set_col_width(c, widths[i])
            if idx % 2 == 1:
                shade(c, LIGHT)
            c.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            p = c.paragraphs[0]
            p.paragraph_format.space_after = Pt(1)
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.line_spacing = 1.25
            if align_center is not None and i in align_center:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            bold = first_col_bold and i == 0
            set_font(p.add_run(str(val)), font_size, bold, DARK if i > 0 else NAVY)
    return t

def callout(title, lines, fill=SOFT, edge=TEAL):
    t = doc.add_table(rows=1, cols=1)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    t.allow_autofit = False
    c = t.rows[0].cells[0]
    set_col_width(c, 16.6)
    shade(c, fill)
    tcPr = c._tc.get_or_add_tcPr()
    borders = OxmlElement("w:tcBorders")
    for side in ("top", "left", "bottom", "right"):
        b = OxmlElement("w:" + side)
        if side == "left":
            b.set(qn("w:val"), "single")
            b.set(qn("w:sz"), "24")
            b.set(qn("w:color"), "1E7A55")
        else:
            b.set(qn("w:val"), "nil")
        borders.append(b)
    tcPr.append(borders)
    p = c.paragraphs[0]
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(2)
    set_font(p.add_run(title), 10, True, NAVY)
    for line in lines:
        p2 = c.add_paragraph()
        p2.paragraph_format.space_before = Pt(0)
        p2.paragraph_format.space_after = Pt(2)
        p2.paragraph_format.line_spacing = 1.4
        set_font(p2.add_run("· "), 9.3, False, TEAL)
        set_font(p2.add_run(line), 9.3, False, DARK)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)

def mono(lines):
    t = doc.add_table(rows=1, cols=1)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    t.allow_autofit = False
    c = t.rows[0].cells[0]
    set_col_width(c, 16.6)
    shade(c, "F5F7FA")
    tcPr = c._tc.get_or_add_tcPr()
    borders = OxmlElement("w:tcBorders")
    for side in ("top", "left", "bottom", "right"):
        b = OxmlElement("w:" + side)
        b.set(qn("w:val"), "single")
        b.set(qn("w:sz"), "4")
        b.set(qn("w:color"), "DDE3EE")
        borders.append(b)
    tcPr.append(borders)
    first = True
    for line in lines:
        p = c.paragraphs[0] if first else c.add_paragraph()
        first = False
        p.paragraph_format.space_before = Pt(1)
        p.paragraph_format.space_after = Pt(1)
        p.paragraph_format.line_spacing = 1.15
        set_font(p.add_run(line), 8.8, False, RGBColor(0x2B, 0x33, 0x44), MONO)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)

def figure(path, width_cm, cap):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(path, width=Cm(width_cm))
    caption(cap, before=3, after=9)

doc.core_properties.title = "24 点单人挑战项目 · 现状汇报"
doc.core_properties.subject = "游戏规则、前后端架构与模块组成（现状）"
doc.core_properties.author = "项目组"
doc.core_properties.comments = "内部讨论稿，仅供评审与指导；不含改造方案。"

# ---------------- cover ----------------
p = doc.add_paragraph()
p.paragraph_format.space_before = Pt(40)
p.paragraph_format.space_after = Pt(4)
set_font(p.add_run("内部评审稿  ·  v0.2"), 9.5, True, TEAL)

p = doc.add_paragraph()
p.paragraph_format.space_before = Pt(30)
p.paragraph_format.space_after = Pt(0)
set_font(p.add_run("24 点单人挑战项目"), 27, True, NAVY)

p = doc.add_paragraph()
p.paragraph_format.space_before = Pt(4)
p.paragraph_format.space_after = Pt(6)
set_font(p.add_run("现状汇报"), 42, True, NAVY)

p = doc.add_paragraph()
p.paragraph_format.space_before = Pt(6)
p.paragraph_format.space_after = Pt(18)
set_font(p.add_run("玩法  ·  前后端架构  ·  模块组成"), 14, False, GREY)

# thin line
p = doc.add_paragraph()
p.paragraph_format.space_before = Pt(0)
p.paragraph_format.space_after = Pt(14)
pPr = p._p.get_or_add_pPr()
pbdr = OxmlElement("w:pBdr")
bottom = OxmlElement("w:bottom")
bottom.set(qn("w:val"), "single"); bottom.set(qn("w:sz"), "12")
bottom.set(qn("w:space"), "1"); bottom.set(qn("w:color"), "1E7A55")
pbdr.append(bottom); pPr.append(pbdr)

p = doc.add_paragraph()
p.paragraph_format.space_before = Pt(0)
p.paragraph_format.space_after = Pt(40)
p.paragraph_format.line_spacing = 1.65
set_font(p.add_run("呈报给专业团队，作为评审与指导的底稿。本稿只陈述现状，不含改造方案；所有描述尽量落到代码、数据库迁移与部署记录。文中不当与不详之处，恳请指正。"), 11, False, GREY)

doc.add_page_break()

h1("一、", "玩法")
para("24 点是一个单人数字游戏：每题给四张牌，玩家用加、减、乘、除把四个数字各用一次，算出 24。当前是单人在线挑战，不设对手，不做实时对战。")
callout("演示版本", [
    "http://121.43.236.209:8081",
    "当前为 HTTP 演示环境，无域名与 HTTPS；仅供评审查看，请勿使用真实密码。",
])

h2("1.1", "一局怎么玩")
para("选择 A 或 B 模式、L1 或 L2 难度后开始。系统发四张 1–13 的牌；点一张牌、点算符、再点第二张牌，两张合并成一张新牌，值为运算结果，可以是分数。重复三次，四张并成一张即完成。")
para("括号由点击顺序决定，玩家不需要输入；第三次合并完成后前端自动提交，服务端用有理数重算并判定是否等于 24。作答中可以撤销上一步；撤销不暂停计时，也不消除已经产生的罚时。")
para("也可以跳题或退出：跳题立即换下一题并产生罚时；退出需要二次确认，本局作废，不写入成绩。")

h2("1.2", "难度与模式")
table_caption("表 1-1  两个难度")
table(
    ["难度", "可用算符", "数字", "题池"],
    [
        ("L1 加减级", "+ −", "1–13 可重复", "220 组"),
        ("L2 四则级", "+ − × ÷", "1–13 可重复", "1,362 组"),
    ],
    [3.6, 4.2, 4.4, 4.4],
    font_size=9.0,
    header_size=9.0,
    first_col_bold=True,
    align_center={1, 2, 3},
)
table_caption("表 1-2  两种模式")
table(
    ["模式", "目标", "结束条件", "答错", "跳题"],
    [
        ("A 限时", "300 秒内答对越多越好", "倒计时归零", "剩余时间 −5 秒", "剩余时间 −10 秒"),
        ("B 定量", "答对 10 题，总用时越短越好", "第 10 题答对", "总用时 +5 秒", "总用时 +10 秒"),
    ],
    [2.4, 6.0, 2.8, 2.6, 2.8],
    font_size=8.8,
    header_size=8.8,
    first_col_bold=True,
)

h2("1.3", "成绩与榜单")
para("A 榜先比答对题数，同题数再比答对最后一题时的计榜用时；B 榜比完成 10 题的总用时。每个账号在每个“模式 × 难度”下只保留一条最佳成绩，共四个榜。游客可以直接玩，但只有登录后的账号成绩进入排行榜；登录或注册时，游客成绩会并入账号。")

# ---------------- chapter 3 ----------------
h1("二、", "总体架构")
h2("2.1", "一张图")
figure(os.path.join(os.path.dirname(__file__), "report_fig1_architecture.png"), 16.4,
       "图 1  当前运行架构：浏览器 SPA → Spring Boot 单体 → PostgreSQL。生产环境静态文件由 Spring Boot 直接托管。")

h2("2.2", "三层职责")
table_caption("表 2-1  分层与边界")
table(
    ["层", "组成", "负责", "不负责"],
    [
        ("浏览器", "Vite + TypeScript 单页应用", "选模式、点牌合并、倒计时插值、token 管理、渲染", "判题、权威计时、成绩写库"),
        ("应用", "Spring Boot 3.3.4 单体", "REST、身份、规则校验、计时、事务、幂等、结算、静态文件", "页面视觉、离线能力"),
        ("数据", "PostgreSQL", "账号、对局、题目、动作、成绩、最佳；约束与索引", "除唯一/检查约束外的业务规则"),
    ],
    [2.2, 4.6, 6.3, 3.5],
    font_size=8.8,
    header_size=8.8,
    first_col_bold=True,
)

h2("2.3", "关键设计（现状，不是主张）")
bullet("一个进程同时提供 /api 与静态页面；没有服务发现、消息队列、独立前端服务器（生产）。", "单体：")
bullet("客户端提交的是三步操作树（c0..c3 / s0..s2 + 算符），不是“24”这个最终值；服务端重算。", "服务端权威：")
bullet("JWT，不建 HttpSession；刷新令牌存库、每次轮换。", "无状态：")
bullet("对局、成绩、最佳同一 PostgreSQL；排行榜不另建表，直接派生。", "单库事务：")
bullet("建局用 requestId 唯一；动作 use actionId + fingerprint + revision；行锁串行化同一局。", "幂等与并发：")
bullet("服务端统一 UTC；前端未做时区转换，时间按 ISO 原文显示。", "时间：")

h2("2.4", "请求路径")
mono([
    "浏览器",
    "  │ 同源 /api",
    "  ▼",
    "Spring Security FilterChain",
    "  ├─ BearerTokenAuthenticationFilter → AccountGuardFilter（账号存在 / ACTIVE / tv 一致）",
    "  └─ 未登录：X-Guest-Id",
    "  ▼",
    "PlayerArgumentResolver → Controller → Service（@Transactional）",
    "  ▼",
    "JdbcTemplate / HikariCP → PostgreSQL",
    "  ▼",
    "GameView / RecordsView / BoardView（JSON）→ 前端重绘",
])
