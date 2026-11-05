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
set_font(p.add_run("内部评审稿  ·  v0.1"), 9.5, True, TEAL)

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
set_font(p.add_run("游戏规则  ·  前后端架构  ·  模块组成"), 14, False, GREY)

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

meta = [
    ("呈报对象", "专业团队（评审与指导）"),
    ("编制", "项目组"),
    ("日期", "2026 年 11 月 5 日"),
    ("代码范围", "demo/web、demo/server、db/migration（2026-11-05 工作区快照）"),
    ("演示地址", "http://121.43.236.209:8081（HTTP 演示环境）"),
    ("材料性质", "内部讨论稿；请勿外传，亦不作为对外承诺"),
]
t = doc.add_table(rows=0, cols=2)
t.alignment = WD_TABLE_ALIGNMENT.LEFT
t.autofit = False
for k, v in meta:
    row = t.add_row().cells
    set_col_width(row[0], 3.6)
    set_col_width(row[1], 12.8)
    p0 = row[0].paragraphs[0]
    p0.paragraph_format.space_after = Pt(2)
    set_font(p0.add_run(k), 9, False, GREY)
    p1 = row[1].paragraphs[0]
    p1.paragraph_format.space_after = Pt(2)
    set_font(p1.add_run(v), 9.3, False, DARK)

p = doc.add_paragraph()
p.paragraph_format.space_before = Pt(46)
p.paragraph_format.space_after = Pt(0)
set_font(p.add_run("“先把现在讲清楚，再谈下一步。”"), 9.5, False, TEAL)

doc.add_page_break()

h1("一、", "游戏规则")
para("本稿只陈述现状：当前玩的是什么规则、哪些地方与代码不一致、哪些地方我们还不确定。所有描述以 2026-11-05 工作区代码与线上只读复核为准；规则文本与代码不一致处集中列在 7.1。")
callout("演示版本", [
    "http://121.43.236.209:8081",
    "当前为 HTTP 演示环境，无域名与 HTTPS；仅供评审查看，请勿使用真实密码。",
])
para("以下按现行规则文本陈述玩法，并在关键处标注代码现状。规则文本是 docs/24点游戏_单人挑战与排行榜_规则说明.md（文件头标注“最终版”）。")

h2("1.1", "题面与判题口径")
table_caption("表 1-1  题面与判题")
table(
    ["规则点", "规则文本", "代码现状"],
    [
        ("题面", "4 个整数，数字可重复", "一致；题池来自 puzzles-L1/L2.json"),
        ("数字范围", "L1、L2 均为 1–13", "一致"),
        ("数字使用", "每个数字必须且只能使用一次", "ExpressionEvaluator 用 consumed / usedLeaves 校验"),
        ("目标", "结果精确等于 24，允许中间分数", "一致；全程有理数 Fraction，不用浮点"),
        ("禁止", "除零、拼接数字、额外常数、一元负号", "三步操作树天然禁止拼接/额外常数/一元负号；除零抛错"),
        ("提交", "四张牌并成一张（三次合并）", "一致；steps 必须恰好 3 步，四张各一次"),
        ("判题位置", "服务端权威", "一致；前端只做本地预演，最终以服务端返回为准"),
    ],
    [2.8, 6.2, 7.6],
    font_size=8.8,
    header_size=8.8,
    first_col_bold=True,
)

h2("1.2", "难度与题池")
table_caption("表 1-2  两个难度")
table(
    ["难度", "可用算符", "数字", "题池", "作答方式"],
    [
        ("L1 加减级", "+ −", "1–13 可重复", "220 组", "点牌合并"),
        ("L2 四则级", "+ − × ÷", "1–13 可重复", "1,362 组", "点牌合并"),
    ],
    [3.2, 3.4, 3.4, 3.0, 3.6],
    font_size=9.0,
    header_size=9.0,
    first_col_bold=True,
    align_center={1, 2, 3, 4},
)
bullet("候选池：1–13 的非降序四元组共 1,820 组；用同一判题内核筛出可解牌组，L1 220、L2 1,362。", "题池来源：")
bullet("PuzzleGenerator 离线穷举，输出 puzzles-L1.json / puzzles-L2.json，随 jar 打包；启动时 PuzzleRepository 读入内存。", "生成方式：")
bullet("复制整副牌到 games.deck 并洗牌；deck_position 指向下一题；耗尽后重新洗牌并重置位置（规则 §7.3；代码路径有缺陷，见 7.2 R9）。", "每局：")
bullet("一个洗牌周期内按 deck 顺序取，不重复；重置后允许再次出现，规则明确允许。", "同局不重复：")
bullet("当前生成参数固定在代码常量里；重新生成需要执行 mvnw compile exec:java -Dexec.mainClass=com.game24.puzzle.PuzzleGenerator。", "可维护性：")

h2("1.3", "一局怎么作答")
num_item(1, "选择模式（A/B）与难度（L1/L2），开始挑战。")
num_item(2, "点一张牌选中；点算符；点第二张牌，两张合并为一张新牌，值为运算结果，可以是分数。")
num_item(3, "重复 3 次，四张并成一张；前端在第三次合并完成的同一刻自动提交，没有单独的“提交答案”按钮。")
num_item(4, "服务端逐条校验三步合并，重算结果，判定是否等于 24。")
num_item(5, "正确则本题标记 SOLVED、答对数 +1，发下一题；错误则标记 WRONG、罚时并换下一题；跳题则标记 SKIPPED、罚时并换下一题。")
num_item(6, "达到结束条件后结算，展示本局成绩；若刷新个人最佳，页面显示“新纪录”（判定方式见 7.2 R8）。")
para("几个容易误解的点：")
bullet("括号由点击顺序决定，玩家不需要输入括号；合并树与最终算式一一对应。")
bullet("撤销只回退作答步骤，不回退计时，也不撤销已经产生的错误/跳题罚时。")
bullet("规则文本还写了“全部相加”“全部相乘”、数字键 1–4 选牌、算符热键；当前前端没有实现这些键盘操作（见 7.1 D2）。")
bullet("规则文本说答错后可以撤销并继续修改当前题；当前代码是答错即关闭本题、直接换下一题（见 7.1 D1）。这是最需要先确认的口径。")

h2("1.4", "两种模式")
table_caption("表 1-3  A/B 模式参数")
table(
    ["项目", "A 模式：限时挑战", "B 模式：定量挑战"],
    [
        ("固定配置", "300 秒倒计时", "答对 10 道题"),
        ("结束条件", "剩余时间降到 0", "第 10 道题正确提交"),
        ("考查重点", "有限时间内尽量多答对", "答对 10 题的总用时尽量短"),
        ("答错罚时", "剩余时间 −5 秒", "总计用时 +5 秒"),
        ("跳题罚时", "剩余时间 −10 秒", "总计用时 +10 秒"),
        ("单题时限", "无，只受总倒计时约束", "无，思考时间计入总用时"),
        ("计榜口径", "答对第 N 题时的实际经过 + 累计罚时", "完成第 10 题时的实际经过 + 累计罚时"),
        ("零题/未完成", "答对 0 题只留历史，不上榜", "未答满 10 题不结算为完成"),
    ],
    [2.9, 6.9, 6.8],
    font_size=8.8,
    header_size=8.8,
    first_col_bold=True,
)
para("B 模式的“10 道题”特指答对 10 道。主动跳过的题不占这 10 个名额，系统继续出题，直到答满 10 道。")

h2("1.5", "计时、罚时与结束判定")
bullet("服务端使用 UTC Clock；games.started_at / deadline_at 落库；A 的剩余时间 = 300,000 − 实际经过 − 累计罚时，由响应计算，前端只做 100 ms 插值显示。", "计时在服务端：")
bullet("A 的罚时直接扣 deadline；B 的罚时累加到 penalty_ms，表盘显示“实际经过 + 罚时”。", "罚时落在哪里：")
bullet("提交必须严格早于 deadline；到点后提交返回 409 GAME_EXPIRED，前端再用 GET 触发结算（当前实现路径，见 7.2 R2）。", "截止时刻：")
bullet("每次有效错误提交分别计罚；撤销不会消除罚时；跳题立即生效且不能返回。", "不可撤销：")
bullet("规则文本为“不设置”；代码一致，没有单题计时器。", "单题超时：")
bullet("由 deadline 判断；正常 submit/advance 能结算，但 skip 路径存在重复结算缺陷（7.2 R1）。", "A 模式罚时耗尽：")

h2("1.6", "成绩有效性")
table_caption("表 1-4  哪些局有效")
table(
    ["情形", "是否有效", "说明"],
    [
        ("A 自然倒计时结束（≥1 题）", "有效", "正常结束，可更新最佳成绩"),
        ("A 罚时耗尽结束（≥1 题）", "有效", "正常结束，可更新最佳成绩"),
        ("A 一题未答对", "只留历史", "不上榜，不建最佳"),
        ("B 正常答满 10 题", "有效", "可更新最佳成绩"),
        ("主动中途退出", "无效", "不写 game_results、不建档、不上榜"),
        ("断线", "不判无效", "服务端计时继续；后端可按 gameId 读取原局"),
        ("题池耗尽", "继续", "规则要求重置题池；代码路径有缺陷，见 7.2 R9"),
    ],
    [4.7, 3.0, 8.9],
    font_size=8.8,
    header_size=8.8,
    first_col_bold=True,
)

h2("1.7", "排名与最佳成绩")
para("每个账号在每个“模式 × 难度”下只保留一条最佳，共四条；只有严格更好才替换，追平保留首次取得时间。排序口径如下：")
mono([
    "A 榜：best_correct DESC → best_scoring_ms ASC → achieved_at ASC → account_id ASC",
    "B 榜：best_scoring_ms ASC → achieved_at ASC → account_id ASC",
    "计榜用时（A）：答对第 N 题时的（实际经过 + 累计罚时）",
    "计榜用时（B）：完成第 10 题时的（实际经过 + 累计罚时）",
])
bullet("规则文本只写到“先取得者优先”；代码在 achieved_at 相同时又用 account_id 兜底，保证分页稳定。")
bullet("昵称展示隐藏第一个 Unicode 码点，前面加 *；例如“心算王”显示为“*算王”。")
bullet("分页 size 1–50、page ≥ 0，offset 上限 5,000；超过返回 400 PAGE_OUT_OF_RANGE。")
bullet("“我的排名”= 排在我前面的人数 + 1，每次实时 count，不缓存。")

h2("1.8", "账号、游客与榜单身分")
table_caption("表 1-5  身份与合并规则")
table(
    ["项目", "实现"],
    [
        ("游客", "localStorage 中的 guestId，8–64 位 [A-Za-z0-9_-]；请求头 X-Guest-Id；可玩、有本机历史/最佳，不上榜"),
        ("注册", "用户名 4–20 位、字母开头、小写字母/数字/下划线；昵称 2–12 字符；密码 8–64 位且同时含字母和数字"),
        ("登录", "用户名 + 密码；带 guestId 时合并游客数据；返回 access token 并设置 refresh cookie"),
        ("游客合并", "同一事务把 games / game_results 归到账号，合并 personal_bests；claimedGames 是“并入的对局数”，不是成绩条数"),
        ("榜单身分", "只有 account_id 非空的成绩进榜；游客最佳只在本机记录中可见"),
    ],
    [3.0, 13.6],
    font_size=8.8,
    header_size=8.8,
    first_col_bold=True,
)
para("账号规则由服务端统一校验：用户名、昵称、密码、guestId 的格式都在 AuthService 里，Controller 不重复判断。密码用 BCrypt 成本 12 存储；用户名不存在时也会跑一次 BCrypt，避免通过响应时间枚举账号。")

h2("1.9", "规则文本与代码：先记住三处")
callout("会影响玩法的三处差异（完整对照见 7.1）", [
    "答错之后：文本说“撤销后继续修改当前题”，代码是“本题关闭，直接换下一题”。这决定了罚时节奏与题目消耗方式。",
    "刷新之后：文本与 README 说“可重连恢复”，后端确实能按 gameId 读取原局，但前端没有持久化 gameId，刷新页面实际回到首页。",
    "快捷键：文本提到“全部相加/全部相乘”、数字键选牌与算符热键；当前前端只有按钮，没有键盘绑定。",
])

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
bullet("服务端统一 UTC；前端本地化不足，见 7.2 R7。", "时间：")

h2("2.4", "请求路径")
mono([
    "浏览器",
    "  │ 同源 /api（开发经 Vite 代理到 :8080）",
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

h2("2.5", "开发与线上的差别")
table_caption("表 2-2  两套运行形态")
table(
    ["项目", "开发", "线上"],
    [
        ("页面", "Vite :5173，/api 代理到 :8080", "Spring Boot 托管 dist，:8081"),
        ("数据库", "compose PG 16 :55432，或本机 PG 18.1", "本机 PG 14，127.0.0.1:5432"),
        ("进程", "mvnw spring-boot:run", "systemd game24.service"),
        ("HTTPS", "无", "无（当前）"),
        ("备份", "手动", "cron 03:00，pg_dump，保留 14 天"),
    ],
    [2.7, 6.7, 7.2],
    font_size=8.8,
    header_size=8.8,
    first_col_bold=True,
)
para("详细部署与运维见第六章。")

