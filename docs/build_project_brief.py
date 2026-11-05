"""Build the teacher-facing project brief (DOCX) for the 24-point competitive game."""

from __future__ import annotations

import os

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

HERE = os.path.dirname(os.path.abspath(__file__))
DIAG = os.path.join(HERE, "diagrams")
OUT = os.path.join(HERE, "24点竞技游戏_项目说明.docx")

CJK = "微软雅黑"
LATIN = "Segoe UI"

CLR_TITLE = RGBColor(0x1B, 0x2A, 0x3A)
CLR_HEAD = RGBColor(0x2C, 0x5A, 0xA8)
CLR_MUTED = RGBColor(0x5B, 0x64, 0x70)
CLR_WHITE = RGBColor(0xFF, 0xFF, 0xFF)
CLR_TODO = RGBColor(0xB4, 0x3A, 0x2E)

FILL_HEAD_ROW = "2C5AA8"
FILL_ALT = "F4F7FC"
FILL_STRIPE = "EAF1FB"
FILL_TODO = "FDF1EF"
FILL_DONE = "EAF6EE"
BORDER = "C9D3E0"

TOTAL_WIDTH_CM = 16.6


# ----------------------------------------------------------------- helpers
def set_font(run, size=10.5, bold=False, color=None, cjk=CJK, latin=LATIN):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.name = latin
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    rfonts.set(qn("w:ascii"), latin)
    rfonts.set(qn("w:hAnsi"), latin)
    rfonts.set(qn("w:eastAsia"), cjk)
    if color is not None:
        run.font.color.rgb = color


def shade(cell, hex_fill):
    tcpr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_fill)
    tcpr.append(shd)


def cell_margins(table, top=60, bottom=60, left=90, right=90):
    tblpr = table._tbl.tblPr
    mar = OxmlElement("w:tblCellMar")
    for tag, val in (("top", top), ("left", left), ("bottom", bottom), ("right", right)):
        el = OxmlElement(f"w:{tag}")
        el.set(qn("w:w"), str(val))
        el.set(qn("w:type"), "dxa")
        mar.append(el)
    tblpr.append(mar)


def table_borders(table, color=BORDER, size=6):
    tblpr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), str(size))
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), color)
        borders.append(el)
    tblpr.append(borders)


def repeat_header(row):
    trpr = row._tr.get_or_add_trPr()
    el = OxmlElement("w:tblHeader")
    el.set(qn("w:val"), "true")
    trpr.append(el)


def no_split(row):
    trpr = row._tr.get_or_add_trPr()
    el = OxmlElement("w:cantSplit")
    el.set(qn("w:val"), "true")
    trpr.append(el)


def set_col_widths(table, widths_cm):
    table.autofit = False
    tblpr = table._tbl.tblPr
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    tblpr.append(layout)
    for row in table.rows:
        for idx, w in enumerate(widths_cm):
            row.cells[idx].width = Cm(w)
    # also set grid
    tblgrid = table._tbl.tblGrid
    for idx, gc in enumerate(tblgrid.findall(qn("w:gridCol"))):
        if idx < len(widths_cm):
            gc.set(qn("w:w"), str(int(widths_cm[idx] * 567)))


def para(cell_or_doc, text, size=9.5, bold=False, color=None, align=None, space_after=0):
    p = cell_or_doc.add_paragraph() if hasattr(cell_or_doc, "add_paragraph") else None
    if p is None:  # it's a cell
        p = cell_or_doc.paragraphs[0] if cell_or_doc.paragraphs and not cell_or_doc.paragraphs[0].text else cell_or_doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(0)
    pf.space_after = Pt(space_after)
    pf.line_spacing_rule = WD_LINE_SPACING.SINGLE
    if align is not None:
        p.alignment = align
    r = p.add_run(text)
    set_font(r, size=size, bold=bold, color=color)
    return p


def fill_cell(cell, text, size=9.5, bold=False, color=None, align=None):
    cell.text = ""
    lines = text.split("\n")
    p = cell.paragraphs[0]
    pf = p.paragraph_format
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)
    pf.line_spacing_rule = WD_LINE_SPACING.SINGLE
    if align is not None:
        p.alignment = align
    for i, line in enumerate(lines):
        if i:
            p = cell.add_paragraph()
            pf = p.paragraph_format
            pf.space_before = Pt(1)
            pf.space_after = Pt(0)
            pf.line_spacing_rule = WD_LINE_SPACING.SINGLE
            if align is not None:
                p.alignment = align
        r = p.add_run(line)
        set_font(r, size=size, bold=bold, color=color)


def heading(doc, text, level=1, size=None, space_before=14, color=CLR_HEAD):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(space_before)
    pf.space_after = Pt(6)
    pf.keep_with_next = True
    r = p.add_run(text)
    set_font(r, size=size or (15 if level == 1 else 12), bold=True, color=color)
    if level == 1:
        # thin rule under the heading
        ppr = p._p.get_or_add_pPr()
        pbdr = OxmlElement("w:pBdr")
        bottom = OxmlElement("w:bottom")
        bottom.set(qn("w:val"), "single")
        bottom.set(qn("w:sz"), "8")
        bottom.set(qn("w:space"), "4")
        bottom.set(qn("w:color"), "C9DAF4")
        pbdr.append(bottom)
        ppr.append(pbdr)
    return p


def body(doc, text, size=10.5, color=None, space_after=4, indent=0.0):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(0)
    pf.space_after = Pt(space_after)
    pf.line_spacing = 1.45
    if indent:
        pf.left_indent = Cm(indent)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    r = p.add_run(text)
    set_font(r, size=size, color=color)
    return p


def bullet(doc, text, size=10.5):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.left_indent = Cm(0.75)
    pf.first_line_indent = Cm(-0.35)
    pf.space_before = Pt(0)
    pf.space_after = Pt(2)
    pf.line_spacing = 1.4
    r = p.add_run("· ")
    set_font(r, size=size, bold=True, color=CLR_HEAD)
    r2 = p.add_run(text)
    set_font(r2, size=size)
    return p


def figure(doc, filename, caption, width_cm=16.4):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(os.path.join(DIAG, filename), width=Cm(width_cm))
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.paragraph_format.space_after = Pt(10)
    r = cap.add_run(caption)
    set_font(r, size=9, color=CLR_MUTED)


def callout(doc, title_text, text, fill="F3F7FD", border="4C7FE0"):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_col_widths(tbl, [TOTAL_WIDTH_CM])
    table_borders(tbl, color=border, size=8)
    cell = tbl.rows[0].cells[0]
    shade(cell, fill)
    cell.text = ""
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run(title_text)
    set_font(r, size=10, bold=True, color=CLR_HEAD)
    for i, line in enumerate(text.split("\n")):
        p2 = cell.add_paragraph()
        p2.paragraph_format.space_after = Pt(0)
        p2.paragraph_format.line_spacing = 1.35
        r2 = p2.add_run(line)
        set_font(r2, size=9.5)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def spacer(doc, pt=6):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.space_before = Pt(0)
    r = p.add_run("")
    set_font(r, size=pt)


# ----------------------------------------------------------------- build
def build():
    doc = Document()

    # page setup: A4, comfortable margins
    sec = doc.sections[0]
    sec.page_width = Cm(21.0)
    sec.page_height = Cm(29.7)
    sec.left_margin = Cm(2.2)
    sec.right_margin = Cm(2.2)
    sec.top_margin = Cm(2.0)
    sec.bottom_margin = Cm(1.9)

    # default style
    normal = doc.styles["Normal"]
    normal.font.name = LATIN
    normal.font.size = Pt(10.5)
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), CJK)

    # footer with page number
    footer_p = sec.footer.paragraphs[0]
    footer_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = footer_p.add_run()
    set_font(run, size=8.5, color=CLR_MUTED)
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), "PAGE")
    footer_p._p.append(fld)
    run2 = footer_p.add_run("  /  ")
    set_font(run2, size=8.5, color=CLR_MUTED)
    fld2 = OxmlElement("w:fldSimple")
    fld2.set(qn("w:instr"), "NUMPAGES")
    footer_p._p.append(fld2)

    # ---------------- cover block
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run("24 点竞技游戏")
    set_font(r, size=28, bold=True, color=CLR_TITLE)

    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(10)
    r = p.add_run("项目说明")
    set_font(r, size=18, bold=False, color=CLR_HEAD)

    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(18)
    r = p.add_run("双人同题 · 点牌合并作答 · 双模式竞速      |      首版定稿 V1.1（竞品分析修订）")
    set_font(r, size=10, color=CLR_MUTED)

    fig = os.path.join(DIAG, "fig1_architecture.png")
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(4)
    p.add_run().add_picture(fig, width=Cm(16.6))
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.paragraph_format.space_after = Pt(14)
    r = cap.add_run("图 1  系统整体架构（详见第 3 节）")
    set_font(r, size=9, color=CLR_MUTED)

    # info table
    info = doc.add_table(rows=0, cols=2)
    info.alignment = WD_TABLE_ALIGNMENT.CENTER
    table_borders(info, color="DDE3EC")
    cell_margins(info)
    rows = [
        ("项目名称", "24 点竞技游戏（暂定）"),
        ("项目类型", "在线多人数学益智竞技游戏"),
        ("技术方向", "Web 全栈开发 + 实时网络通信 + 算法与规则引擎"),
        ("核心难点", "服务端权威判题与计时、双人同题对局的一致性、结果可靠存档"),
        ("文档状态", "首版规则已按竞品分析修订并定稿（V1.1），可作为开发与验收依据（见第 5 节）"),
    ]
    for k, v in rows:
        row = info.add_row()
        no_split(row)
        fill_cell(row.cells[0], k, size=9.5, bold=True, color=CLR_HEAD)
        shade(row.cells[0], "F3F6FB")
        fill_cell(row.cells[1], v, size=9.5)
    set_col_widths(info, [3.6, 13.0])
    info.columns[0].width = Cm(3.6)

    # ---------------- 1
    doc.add_page_break()
    heading(doc, "一、项目概述")
    body(doc,
         "本项目首版是一款双人 24 点竞速游戏。双方在同一时间收到完全相同的题目和题序，"
         "使用四个给定数字及加、减、乘、除凑出 24；系统以「答得对、做得多、用时短」为唯一竞技口径。")
    body(doc,
         "本版相对 V1.0 的核心修正是两处：作答由「自由文本 + 键盘」改为「点两个数 + 一个算符，中间结果并成一张牌」，"
         "括号由点击顺序自动决定，玩家不再需要打括号；出题由「固定 1–9 题池」改为「参数化生成 + 可解率校验」，"
         "避免加减级与低数字段出现大量死题。")
    body(doc,
         "修订依据是竞品调研：行业主流（4 Numbers!）把难度定义在数字幅度上而非算符上，并且用点牌合并消除了括号输入；"
         "本作原方案在加减级上可解题只有 31 组（1–9 仅用 + −），撑不起限时赛的连续出题。", color=CLR_MUTED)
    body(doc,
         "首版只做账号、自动匹配、双人对战和个人战绩。先保证一条对局链路稳定，再考虑多人房、扩展玩法与社交功能。")

    callout(doc, "首版边界：先稳定，再扩展",
            "仅 2 人对战，不做 2–8 人房；难度分加减级 / 四则级 / 扩展级，四则级是默认档；不做对数、排列与组合。\n"
            "仅自动匹配和同题同序，自选难度、时长与题数可以，但不做邀请房、段位、Elo、排行榜、观战与回放。\n"
            "已有项目可作为技术参考：Colyseus（房间与权威同步）、NestJS Prisma Starter（账号与数据骨架）、"
            "calc24 / 24_game_solver（经典四则求解算法）。")

    # ---------------- 2
    heading(doc, "二、首版玩法与统一计分规则")
    body(doc, "每题给出 4 个 1–13 的整数（加减级、四则级），每个数字必须且只能使用一次，结果用有理数精确计算并等于 24。"
              "允许中间过程出现分数，不允许拼接数字、额外常数、一元负号或除以零。")
    body(doc, "作答采用「点牌合并」：先点两张牌，再点一个算符（+ − × ÷），两张牌合并成一张新牌；四张牌并成一张即为完成。"
              "括号由点击顺序决定，玩家不需要、也不能输入括号——这一条同时解决了「算式对但括号打错被判错」的误判，"
              "也让加减级天然被约束成只许加减。扩展级因为要用幂、开方与阶乘，保留自由文本输入。")

    t = doc.add_table(rows=1, cols=3)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    table_borders(t)
    cell_margins(t)
    hdr = t.rows[0]
    repeat_header(hdr)
    for i, txt in enumerate(["项目", "首版规则", "实现与验收口径"]):
        fill_cell(hdr.cells[i], txt, size=9.5, bold=True, color=CLR_WHITE)
        shade(hdr.cells[i], FILL_HEAD_ROW)
    data = [
        ("对战与题目", "仅双人自动匹配；同局同题同序", "开局前一次性确定题序；双方 puzzleId 相同，不能重抽或跳题"),
        ("作答输入", "点牌合并：点两数 + 算符，中间结果并成一张牌；扩展级用自由文本", "每次合并上报（步骤序号、两张牌、算符）；服务端逐条校验合并链，步骤数必须为 3；合并成一张牌后才接受提交"),
        ("撤销与快捷", "撤销一步；全部相加（A）、全部相乘（S）；数字键 1–4 选牌", "撤销只回退合并步骤，不暂停也不回拨计时；快捷操作产生的步骤同样逐条校验"),
        ("错误与重试", "答错不扣分，可继续修改当前题", "每题每人每 2 秒最多提交 1 次；错误次数只展示，不参与胜负"),
        ("单题超时", "同一题 60 秒没有正确提交，自动收走该题继续计时", "只改变当前题状态，不改题序、不扣分；与封盘、断线竞争时不重复结算"),
        ("正确提交", "当前题锁定为已完成，立即进入下一题", "同一玩家同一题只接受第一次正确提交；重复、迟到请求直接忽略并返回当前状态"),
        ("弃权", "点击弃权后二次确认，对方直接获胜", "弃权局仍正常结算；不计个人最好成绩"),
    ]
    for idx, row_data in enumerate(data):
        row = t.add_row()
        no_split(row)
        for i, txt in enumerate(row_data):
            fill_cell(row.cells[i], txt, size=9.5, bold=(i == 0))
            if idx % 2 == 1:
                shade(row.cells[i], FILL_ALT)
    set_col_widths(t, [2.8, 5.2, 8.6])

    spacer(doc, 4)
    heading(doc, "胜负判定：两种模式，参数可选", level=2, space_before=10)

    t2 = doc.add_table(rows=1, cols=3)
    t2.alignment = WD_TABLE_ALIGNMENT.CENTER
    table_borders(t2)
    cell_margins(t2)
    hdr = t2.rows[0]
    repeat_header(hdr)
    for i, txt in enumerate(["对比项", "模式 A：限时赛", "模式 B：定题赛"]):
        fill_cell(hdr.cells[i], txt, size=9.5, bold=True, color=CLR_WHITE)
        shade(hdr.cells[i], FILL_HEAD_ROW)
    rows = [
        ("可选配置", "总时长 90 / 180 / 300 秒，默认 180 秒", "题数 5 / 10 / 20，默认 10 题；全局上限 600 秒"),
        ("匹配页预估", "按每题约 20 秒显示「可作答 N 题左右」", "显示「预计用时 X 分 Y 秒」"),
        ("比较对象", "答对题数", "完成题数（不超过设定题数）"),
        ("判定顺序", "答对多者胜；相同则最后一题正确提交的累计用时短者胜；仍相同则平局", "先比完成题数；相同再比各自最后一题正确提交的累计用时，短者胜；仍相同则平局"),
        ("关键约束", "不可跳题；单题 60 秒超时；到点立即封盘", "不可跳题；单题 60 秒超时；无人完成设定题数也在 600 秒封盘，按已完成数判定"),
        ("成绩口径", "只记录胜/负/平与答对题数；累计答对题数跨局累加", "只有完成全部设定题数才更新个人最快用时"),
    ]
    for idx, rd in enumerate(rows):
        row = t2.add_row()
        no_split(row)
        for i, txt in enumerate(rd):
            fill_cell(row.cells[i], txt, size=9.5, bold=(i == 0))
            if idx % 2 == 1:
                shade(row.cells[i], FILL_ALT)
    set_col_widths(t2, [2.8, 6.9, 6.9])

    spacer(doc, 4)
    heading(doc, "出题与题池：参数化生成 + 可解率校验", level=2, space_before=10)
    bullet(doc, "题池不是写死的 JSON 题库，而是「生成参数 + 预筛结果」：参数包括数字上下限、算符池、是否必须使用某算符、最少解数；调难度只改参数，不改代码。")
    bullet(doc, "每个难度独立维护题池，每题至少存在 1 个合法解；牌组按四个数字升序保存，重复数字合法；发布前用服务端同一判题器逐题复算。")
    bullet(doc, "数字范围：加减级、四则级为 1–13，扩展级为 1–12。加减级若停留在 1–9，仅用 + − 可解牌组只有 31 组（6.3%），放宽到 1–13 后为 220 组（12.1%），这是本次修订最关键的一处数据依据。")
    bullet(doc, "单局内牌组不重复；每个难度的可发布牌组数要达到「10 局内不重样」，达不到就收紧题数或分档，而不是上线后再补题。")
    bullet(doc, "题序在开局时一次性生成并写入对局记录，双方完全相同：前段偏易、中段平稳、末段加压；限时赛额外准备 100 题，用尽仍按结束时的统一口径结算。")
    bullet(doc, "个人战绩仅区分限时赛与定题赛；统计场次、胜/负/平，定题赛另存最快用时，另有跨局累加的「累计答对题数」作为长期进度。")

    doc.add_page_break()

    # ---------------- 3
    heading(doc, "三、系统架构")
    body(doc, "首版采用单机、单实时进程架构：浏览器经 Nginx 连接 Colyseus 实时服务与 NestJS API，PostgreSQL 保存账号、对局和战绩。"
              "不引入 Redis、异步 Worker、多进程房间或排行榜；后续确有容量需求再扩容。")

    figure(doc, "fig1_architecture.png", "图 1  系统分层架构")

    t3 = doc.add_table(rows=1, cols=3)
    t3.alignment = WD_TABLE_ALIGNMENT.CENTER
    table_borders(t3)
    cell_margins(t3)
    hdr = t3.rows[0]
    repeat_header(hdr)
    for i, txt in enumerate(["层次", "组成", "关键职责"]):
        fill_cell(hdr.cells[i], txt, size=9.5, bold=True, color=CLR_WHITE)
        shade(hdr.cells[i], FILL_HEAD_ROW)
    rows = [
        ("客户端", "React + TypeScript\n（浏览器）", "匹配、点牌合并交互（选牌 / 合并 / 撤销 / 快捷键）、倒计时与进度、个人战绩；本地只做预判，不作判题依据"),
        ("接入层", "Nginx", "TLS 终结、WebSocket 升级；首版不需要负载均衡和会话保持"),
        ("服务层", "单进程 Colyseus 实时服务", "双人房间、统一计时（含单题 60 秒超时）、合并链校验与判题、一次性结算、60 秒断线重连"),
        ("", "NestJS API 服务", "注册登录与鉴权、对局与个人战绩查询；不开放客户端选题接口"),
        ("", "结果存档任务", "结算时由服务端写入可靠队列并重试；不占用来局消息回调；失败则对局标为无效，不更新战绩"),
        ("数据层", "PostgreSQL + 题池文件", "账号、对局、战绩、最快记录与累计答对题数；各难度题池（生成参数 + 预筛牌组）与私有标准解"),
    ]
    for idx, rd in enumerate(rows):
        row = t3.add_row()
        no_split(row)
        for i, txt in enumerate(rd):
            fill_cell(row.cells[i], txt, size=9.5, bold=(i == 0))
            if idx % 2 == 1:
                shade(row.cells[i], FILL_ALT)
    set_col_widths(t3, [2.6, 4.8, 9.2])

    spacer(doc, 6)
    heading(doc, "一局对战的交互流程", level=2, space_before=10)
    body(doc, "下面是一次完整对局的消息时序。可以看到：题目下发只包含四张牌与题号，标准解始终留在服务端，"
              "减少客户端被逆向或抓包获取答案的空间。")

    figure(doc, "fig2_message_flow.png", "图 2  一局对战的消息时序")

    spacer(doc, 4)
    heading(doc, "规则内核与多难度题池", level=2, space_before=10)
    body(doc, "规则内核是整个系统最核心的资产：它负责校验玩家上报的合并链（或扩展级的文本算式）、用分数精确求值、并校验是否符合该等级规则。"
              "前端与服务端共享同一语法约束，但正确与否只以服务端结果为准。判题是同步纯函数，不使用 eval，不读取数据库或题解。")

    figure(doc, "fig3_rules_pool.png", "图 3  规则内核与题池的生成、下发与判题关系")

    # ---------------- 4
    doc.add_page_break()
    heading(doc, "四、技术选型与工程结构")

    t4 = doc.add_table(rows=1, cols=3)
    t4.alignment = WD_TABLE_ALIGNMENT.CENTER
    table_borders(t4)
    cell_margins(t4)
    hdr = t4.rows[0]
    repeat_header(hdr)
    for i, txt in enumerate(["层次", "选型", "选择理由"]):
        fill_cell(hdr.cells[i], txt, size=9.5, bold=True, color=CLR_WHITE)
        shade(hdr.cells[i], FILL_HEAD_ROW)
    rows = [
        ("前端", "React + TypeScript + Vite", "生态成熟、类型安全；作答采用「点两个数 + 一个算符、中间结果并成一张牌」的合并交互，从交互层消除括号与非法表达式的歧义"),
        ("实时通信", "Colyseus", "内置房间、状态同步、重连和服务端权威模型，天然适合「多房间、小状态」的对局；相比裸 Socket.IO 少大量重复工作"),
        ("业务后端", "NestJS", "模块化清晰，账号与战绩模块边界明确，便于后续接入其他玩法"),
        ("数据库", "PostgreSQL", "权威数据需要事务与唯一约束；最好记录的更新依赖条件更新语句的原子性"),
        ("存档可靠性", "PostgreSQL 事务 + 持久化任务", "结算与战绩更新在同一事务；matchId 唯一保证幂等；本地持久化队列重试，失败标记无效"),
        ("部署", "Docker Compose + Nginx", "单机、单实时进程即可运行；首版不引入 Redis、Worker 集群和 PM2 多进程"),
    ]
    for idx, rd in enumerate(rows):
        row = t4.add_row()
        no_split(row)
        for i, txt in enumerate(rd):
            fill_cell(row.cells[i], txt, size=9.5, bold=(i == 0))
            if idx % 2 == 1:
                shade(row.cells[i], FILL_ALT)
    set_col_widths(t4, [2.6, 4.6, 9.4])

    spacer(doc, 6)
    figure(doc, "fig4_repo_layout.png", "图 4  代码仓库结构")

    heading(doc, "三条贯穿全程的工程约束", level=2, space_before=10)
    t5 = doc.add_table(rows=1, cols=2)
    t5.alignment = WD_TABLE_ALIGNMENT.CENTER
    table_borders(t5)
    cell_margins(t5)
    hdr = t5.rows[0]
    repeat_header(hdr)
    for i, txt in enumerate(["约束", "反例与后果"]):
        fill_cell(hdr.cells[i], txt, size=9.5, bold=True, color=CLR_WHITE)
        shade(hdr.cells[i], FILL_HEAD_ROW)
    rows = [
        ("提交按 matchId + playerId + puzzleId + seq 去重；合并链校验、判题与推进为原子操作", "双击、重连补发或超时竞争不能重复加题；同一玩家同一题只有第一次正确提交有效；伪造合并链一律拒绝"),
        ("单题超时与服务端计时同源", "60 秒超时由服务端单调时钟触发，客户端倒计时只作展示；超时不改变题序与比分"),
        ("只同步题号、四张牌、进度和封盘时间；标准解只在私有题池", "客户端抓包无法读到答案；也不能提前下发后续题目供人离线求解"),
        ("统一使用服务端单调时钟；到期先封盘再处理提交", "收到时间大于或等于截止时间的提交一律无效；以服务端记录为准，不采用客户端用时"),
        ("结算函数只执行一次，matchId 唯一，结果与战绩同事务更新", "重复消息、断线回调和存档重试不能造成重复计数或重复结算"),
        ("结算前掉线保留 60 秒，计时不暂停；封盘后拒绝任何提交", "超时未回直接判负；双方均掉线则对局无效；已封盘结果不能因重连改变"),
    ]
    for idx, rd in enumerate(rows):
        row = t5.add_row()
        no_split(row)
        for i, txt in enumerate(rd):
            fill_cell(row.cells[i], txt, size=9.5, bold=(i == 0))
            if idx % 2 == 1:
                shade(row.cells[i], FILL_ALT)
    set_col_widths(t5, [8.0, 8.6])

    # ---------------- 5
    doc.add_page_break()
    heading(doc, "五、首版规则决策清单")
    body(doc, "以下规则已全部确定，开发、测试与验收统一按此执行。未列入首版的能力一律后置，不在开发中临时增加。", color=CLR_MUTED)

    t6 = doc.add_table(rows=1, cols=4)
    t6.alignment = WD_TABLE_ALIGNMENT.CENTER
    table_borders(t6)
    cell_margins(t6)
    hdr = t6.rows[0]
    repeat_header(hdr)
    for i, txt in enumerate(["编号", "已确定事项", "影响范围", "状态"]):
        fill_cell(hdr.cells[i], txt, size=9.5, bold=True, color=CLR_WHITE)
        shade(hdr.cells[i], FILL_HEAD_ROW)

    todo_rows = [
        ("R1", "对战人数：仅 2 人自动匹配，同局同题同序；取消多人房和邀请房", "房间上限、匹配与公平性"),
        ("R2", "难度：加减级（仅 + −）、四则级（四则）、扩展级（四则 + 幂/开方/阶乘）；数字范围 1–13（L3 为 1–12）", "题池、解析器与判题范围"),
        ("R3", "输入：L1/L2 点牌合并（步数必须为 3，服务端逐条校验）；L3 自由文本最多 200 字符；数字各用一次；中间分数合法", "合并链校验、白名单、分数运算与非法输入"),
        ("R4", "模式：限时赛 90/180/300 秒；定题赛 5/10/20 题且全局上限 600 秒；匹配页显示预估", "状态机、计时、匹配页与验收"),
        ("R4b", "单题超时：同题 60 秒未答对即收走该题继续计时，不改题序、不扣分", "计时器、题序推进与结算边界"),
        ("R5", "胜负：先答对/完成数，再比最后一次正确提交的累计用时；完全相同为平局", "统一口径，不使用平均用时或错误数"),
        ("R6", "跳题与错误：不可跳题；答错不罚可重试；每题每人 2 秒最多 1 次", "消息限流、重复请求与防刷"),
        ("R7", "结束：到时或定题双方完成后封盘；单次结算；弃权则对方获胜", "超时竞争、结算幂等与战绩"),
        ("R8", "断线：保留 60 秒且计时继续；超时判负；双方均掉线则本局无效", "重连、房间回收与异常结果"),
        ("R9", "题池：参数化生成 + 可解率校验；每档至少一解；单局不重复；开局确定题序；服务端私有答案", "预生成、复算、题序编排与安全下发"),
        ("R10", "账号：难度、模式、时长/题数在匹配前选择；胜/负/平、定题最快用时、累计答对题数", "不做 Elo、段位与排行榜"),
        ("R11", "存档：事务 + 唯一 matchId + 持久化重试；最终失败标为无效，不改战绩", "防止重复、漏算和错误纪录"),
        ("R12", "首版安全：服务端权威、白名单语法、请求限流；不做主观作弊识别与封禁系统", "避免复杂误判；异常日志供人工排查"),
        ("R13", "故障：未开局可解散；已开局进程崩溃则本局无效；不做对局恢复与迁移", "以清楚失败代替半成品恢复逻辑"),
        ("R14", "后置：多人房、观战回放、排行榜、自由文本以外的自定义配置（如自定义目标数、自定义时长）均不进首版", "控制范围，优先保证核心链路稳定"),
    ]
    for idx, rd in enumerate(todo_rows):
        row = t6.add_row()
        no_split(row)
        fill_cell(row.cells[0], rd[0], size=9, bold=True, color=CLR_MUTED)
        fill_cell(row.cells[1], rd[1], size=9.5)
        fill_cell(row.cells[2], rd[2], size=9)
        fill_cell(row.cells[3], "已确定", size=9, bold=True, color=RGBColor(0x2F, 0x8F, 0x5B))
        shade(row.cells[3], FILL_DONE)
        if idx % 2 == 1:
            shade(row.cells[0], FILL_ALT)
            shade(row.cells[1], FILL_ALT)
            shade(row.cells[2], FILL_ALT)
    set_col_widths(t6, [1.4, 7.4, 5.4, 2.4])

    # ---------------- 6
    spacer(doc, 10)
    heading(doc, "六、已明确的设计决策")
    t7 = doc.add_table(rows=1, cols=2)
    t7.alignment = WD_TABLE_ALIGNMENT.CENTER
    table_borders(t7)
    cell_margins(t7)
    hdr = t7.rows[0]
    repeat_header(hdr)
    for i, txt in enumerate(["决策", "说明"]):
        fill_cell(hdr.cells[i], txt, size=9.5, bold=True, color=CLR_WHITE)
        shade(hdr.cells[i], FILL_HEAD_ROW)
    decisions = [
        ("状态机唯一", "waiting → playing → finished；只允许合法迁移。结算后才可关闭房间，终态不可被重连或迟到消息改写"),
        ("统一计分", "不做扣分、平均用时、名次积分或复杂公式；完成数相同才比较最后一次正确提交时的累计用时；单题超时不计入比较项"),
        ("括号由交互消除", "点牌合并让点击顺序即运算顺序，玩家无需也不允许输入括号；扩展级的文本输入才需要显式括号"),
        ("题池可调而非写死", "难度由「生成参数」定义：数字上下限、算符池、最少解数；上线后调整难度不需要改判题代码"),
        ("全程有理数运算", "分数精确求值，不依赖浮点容差；除零、字符越界、数字次数错误均直接判为非法"),
        ("服务端权威与逐题下发", "只发当前题，不泄露后续题目与标准解；计时、判题、结算都在服务端"),
        ("超时边界明确", "提交到达时间必须严格早于截止时间；到点先封盘；不接受客户端声称的作答时间"),
        ("可靠且幂等存档", "matchId 唯一；结果和战绩同事务；持久化任务重试，最终失败标无效，不展示虚假已保存状态"),
        ("故障策略简单", "进程崩溃的进行中房间标记无效，不尝试迁移或恢复；双方均掉线同样无效"),
    ]
    for idx, rd in enumerate(decisions):
        row = t7.add_row()
        no_split(row)
        fill_cell(row.cells[0], rd[0], size=9.5, bold=True)
        fill_cell(row.cells[1], rd[1], size=9.5)
        if idx % 2 == 1:
            shade(row.cells[0], FILL_ALT)
            shade(row.cells[1], FILL_ALT)
    set_col_widths(t7, [4.6, 12.0])

    doc.save(OUT)
    print("saved:", OUT)


if __name__ == "__main__":
    build()