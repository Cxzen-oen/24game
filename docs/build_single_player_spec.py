# -*- coding: utf-8 -*-
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

NAVY = RGBColor(0x0F, 0x3D, 0x5C)
DARK = RGBColor(0x1F, 0x2A, 0x33)
ACCENT = RGBColor(0x1E, 0x7A, 0x55)
GREY = RGBColor(0x5A, 0x66, 0x70)
LIGHT = "EAF1F6"
HEADBG = "0F3D5C"

doc = Document()
sec = doc.sections[0]
sec.page_width = Cm(21.0)
sec.page_height = Cm(29.7)
sec.left_margin = Cm(2.4)
sec.right_margin = Cm(2.4)
sec.top_margin = Cm(2.2)
sec.bottom_margin = Cm(2.2)

def set_font(run, size=10.5, bold=False, color=DARK, name="微软雅黑"):
    run.font.name = name
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    rfonts.set(qn("w:eastAsia"), name)
    rfonts.set(qn("w:ascii"), name)
    rfonts.set(qn("w:hAnsi"), name)

styles = doc.styles
normal = styles["Normal"]
normal.font.name = "微软雅黑"
normal.font.size = Pt(10.5)
normal.element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")
normal.paragraph_format.line_spacing = 1.45
normal.paragraph_format.space_after = Pt(3)

def shade(cell, hexcolor):
    tcpr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hexcolor)
    tcpr.append(shd)

def para(text="", size=10.5, bold=False, color=DARK, align=None, space_before=0, space_after=3, indent=None):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    if align is not None:
        p.alignment = align
    if indent is not None:
        p.paragraph_format.left_indent = Cm(indent)
    if text:
        set_font(p.add_run(text), size, bold, color)
    return p

def bullet(text, bold_prefix=None, indent=0.55):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(indent)
    p.paragraph_format.first_line_indent = Cm(-0.35)
    p.paragraph_format.space_after = Pt(2.5)
    p.paragraph_format.line_spacing = 1.4
    set_font(p.add_run("• "), 10.5, False, ACCENT)
    if bold_prefix:
        set_font(p.add_run(bold_prefix), 10.5, True, DARK)
    set_font(p.add_run(text), 10.5, False, DARK)
    return p

def heading(num, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True
    set_font(p.add_run(num + "  "), 13, True, ACCENT)
    set_font(p.add_run(text), 13, True, NAVY)
    pPr = p._p.get_or_add_pPr()
    pbdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "8")
    bottom.set(qn("w:space"), "3")
    bottom.set(qn("w:color"), "C9D8E3")
    pbdr.append(bottom)
    pPr.append(pbdr)
    return p

def subheading(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.keep_with_next = True
    set_font(p.add_run(text), 11, True, NAVY)
    return p

def table(headers, rows, widths):
    t = doc.add_table(rows=1, cols=len(headers))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.style = "Table Grid"
    t.autofit = False
    hdr = t.rows[0].cells
    for i, h in enumerate(headers):
        hdr[i].width = Cm(widths[i])
        shade(hdr[i], HEADBG)
        p = hdr[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(1)
        set_font(p.add_run(h), 10, True, RGBColor(0xFF, 0xFF, 0xFF))
    for idx, row in enumerate(rows):
        cells = t.add_row().cells
        for i, val in enumerate(row):
            cells[i].width = Cm(widths[i])
            if idx % 2 == 1:
                shade(cells[i], LIGHT)
            p = cells[i].paragraphs[0]
            p.paragraph_format.space_after = Pt(1)
            p.paragraph_format.line_spacing = 1.3
            if i > 0:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            set_font(p.add_run(val), 9.5, False, DARK)
    return t

def callout(title, text):
    t = doc.add_table(rows=1, cols=1)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    cell = t.rows[0].cells[0]
    cell.width = Cm(16.2)
    shade(cell, "EEF5F1")
    tcpr = cell._tc.get_or_add_tcPr()
    bdr = OxmlElement("w:tcBorders")
    for edge in ("left",):
        el = OxmlElement("w:" + edge)
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "18")
        el.set(qn("w:color"), "1E7A55")
        bdr.append(el)
    tcpr.append(bdr)
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(2)
    set_font(p.add_run(title), 10.5, True, ACCENT)
    p2 = cell.add_paragraph()
    p2.paragraph_format.space_after = Pt(2)
    set_font(p2.add_run(text), 9.5, False, DARK)
    return t

# ---------- 封面 ----------
for _ in range(3):
    para("", space_after=0)
para("24 点游戏", 30, True, NAVY, WD_ALIGN_PARAGRAPH.CENTER, space_after=4)
para("单人挑战与排行榜", 22, True, NAVY, WD_ALIGN_PARAGRAPH.CENTER, space_after=14)
p = para("", align=WD_ALIGN_PARAGRAPH.CENTER, space_after=10)
set_font(p.add_run("规则说明 · 完整版"), 13, False, ACCENT)

# 封面信息卡
t = doc.add_table(rows=5, cols=2)
t.alignment = WD_TABLE_ALIGNMENT.CENTER
t.autofit = False
info = [("玩法形态", "单人挑战，按账号保存最佳成绩排名"),
        ("难度等级", "L1 加减级　·　L2 四则级"),
        ("两种模式", "A 模式：限时 5 分钟　·　B 模式：答对 10 题"),
        ("计分方式", "答错罚 5 秒，主动跳题罚 10 秒"),
        ("竞技体现", "A、B 两个排行榜，每个账号每榜一条最佳成绩")]
for i, (k, v) in enumerate(info):
    c0, c1 = t.rows[i].cells
    c0.width = Cm(4.2)
    c1.width = Cm(12.0)
    shade(c0, LIGHT)
    p = c0.paragraphs[0]
    p.paragraph_format.space_after = Pt(1)
    set_font(p.add_run(k), 9.5, True, NAVY)
    p = c1.paragraphs[0]
    p.paragraph_format.space_after = Pt(1)
    set_font(p.add_run(v), 9.5, False, DARK)

doc.add_page_break()

# ---------- 正文 ----------
heading("01", "核心形态")
para("本作是一款单人 24 点挑战游戏。玩家在账号下独立作答，以个人最佳成绩进入排行榜，不设置对手与实时对抗。",
     space_after=6)
table(["要素", "规定"],
      [["玩家人数", "单人，一人一局，无对手"],
       ["难度", "L1 加减级、L2 四则级"],
       ["模式", "A 模式（5 分钟限时）、B 模式（答对 10 题）"],
       ["竞技体现", "A、B 两个排行榜，按模式与难度分别排名"],
       ["账号成绩", "每个账号在每个“模式 × 难度”下保留一条最佳成绩"]],
      [3.6, 12.6])

heading("02", "难度与题目")
subheading("2.1 两个难度")
table(["难度", "数字范围", "可用运算", "作答方式"],
      [["L1 加减级", "1–13，可重复", "+  −", "点牌合并"],
       ["L2 四则级", "1–13，可重复", "+  −  ×  ÷", "点牌合并"]],
      [3.4, 4.0, 4.4, 4.4])

subheading("2.2 题面规则")
bullet("每题给出 4 个整数，数字可以重复。", "组成：")
bullet("每个数字必须且只能使用一次，运算结果必须精确等于 24。", "目标：")
bullet("允许中间结果出现分数；禁止除零、拼接数字、额外常数和一元负号。", "边界：")
bullet("每题至少有一解；同一抽题周期内不重复抽题。", "可解性：")

subheading("2.3 作答方式：点牌合并")
bullet("先点两张牌，再点一个算符，两张牌合并为一张新牌，值为运算结果，可以是分数。")
bullet("连续合并 3 次，四张牌并成一张后才能提交。")
bullet("括号由点击顺序决定，玩家无需输入括号，合并过程与最终算式一一对应。")
bullet("提供撤销、全部相加、全部相乘，以及数字键 1–4 选牌、算符热键的快捷操作。")
bullet("撤销只回退作答步骤，不回退计时，也不撤销已经产生的错误提交与跳题罚时。")
bullet("服务端按合并步骤逐条校验，用有理数精确求值判定是否正确。", "判题：")

heading("03", "两种模式")
table(["项目", "A 模式：限时挑战", "B 模式：定量挑战"],
      [["固定配置", "5 分钟（300 秒）倒计时", "答对 10 道题"],
       ["结束条件", "剩余时间降到 0", "第 10 道题正确提交"],
       ["考查重点", "在有限时间内尽量多答对", "答对 10 题的总用时尽量短"],
       ["单题时限", "无，只受总倒计时约束", "无，思考时间计入总用时"],
       ["跳题是否计为完成", "否", "否"],
       ["能否重复挑战", "可以", "可以"]],
      [3.4, 6.4, 6.4])

para("B 模式的“10 道题”特指答对 10 道题。主动跳过的题不占用这 10 个名额，系统继续出题，直到答满 10 道。",
     space_after=6, space_before=4)

heading("04", "罚时与作答控制")
subheading("4.1 罚时标准")
table(["行为", "A 模式", "B 模式"],
      [["答错一次（正式提交后被判错）", "剩余时间减 5 秒", "总计用时加 5 秒"],
       ["主动跳题一次", "剩余时间减 10 秒", "总计用时加 10 秒"],
       ["单题超时", "不设置", "不设置"]],
      [6.4, 4.9, 4.9])

subheading("4.2 罚时执行细则")
bullet("只有完整提交答案并被判错，才算一次答错；算式未完成、非法操作被本地拦截，不计罚时。")
bullet("答错后可以撤销并继续修改当前题；每一次有效错误提交分别计罚。")
bullet("主动跳题立即结束当前题、产生罚时并进入下一题；跳过的题不能返回重做，也不计为答对。")
bullet("撤销、查看说明等普通操作不产生罚时，但计时不会暂停。")
bullet("错误与跳题已经通过罚时计入成绩，不再作为额外的排名比较项，避免重复惩罚。")
bullet("A 模式若因答错或跳题罚时使剩余时间降到 0，本局立即结束，不再继续作答，也不生成下一题。",
       "时间耗尽：")
bullet("所有判题、计时、罚时与结束判定，均以服务端记录为准。", "权威口径：")

heading("05", "成绩计算与排名")
subheading("5.1 A 模式")
para("A 模式的成绩为“答对题数”，同题数时比较答对最后一题时的计榜用时：", space_before=2)
callout("计榜用时公式", "第 N 题计榜用时 = 300 秒 − 答对第 N 题时的剩余时间（N 为本局答对题数）")
para("此时剩余时间已扣除该题之前产生的全部答错与跳题罚时，因此等价于“截至该题的实际用时 + 累计罚时”，不再重复加罚时。",
     space_before=4, size=10)
subheading("5.2 B 模式")
callout("总计榜用时公式", "总计榜用时 = 开局到第 10 题答对的实际用时 + 5 秒 × 答错次数 + 10 秒 × 跳题次数")
para("实际用时持续累计，不因答错、跳题或撤销而暂停；第 10 题提交正确后本局立即结束，不再计时或计罚。",
     space_before=4, size=10)
subheading("5.3 排名规则")
table(["榜单", "第一比较项", "第二比较项", "仍相同时"],
      [["A 模式榜", "答对题数多者优先", "答对第 N 题计榜用时短者优先", "先取得该成绩者优先"],
       ["B 模式榜", "总计榜用时短者优先", "—", "先取得该成绩者优先"]],
      [3.0, 4.4, 5.6, 3.2])
para("A 榜不计算平均用时，避免跳题、错误与最后一道未完成题是否计入的歧义。同分时的“取得时间”以服务端完成该局结算的时间为准。",
     space_before=4, size=10)

heading("06", "排行榜与最佳成绩")
subheading("6.1 两个榜")
bullet("设置 A 模式排行榜与 B 模式排行榜两个榜。")
bullet("每个榜提供 L1、L2 筛选，只有同模式、同难度的成绩相互排名。")
bullet("每个账号在每个“模式 × 难度”下最多保留一条最佳成绩，共 4 条，不累计占多个名次。")
subheading("6.2 建档与替换")
bullet("首次取得有效成绩时建立纪录。")
bullet("后续挑战只有按该榜排名指标严格优于原纪录时才替换。")
bullet("较差成绩不覆盖最佳成绩，但保留在个人挑战历史中。")
bullet("追平自己的纪录不替换，保留首次取得该成绩的时间。")
bullet("跨模式、跨难度的成绩互不影响。")
subheading("6.3 展示内容")
bullet("名次、昵称、最佳成绩、纪录取得时间，并支持查看“我的最佳成绩”与“我的排名”。")
bullet("A 榜主成绩为答对题数，同题数时展示计榜用时；B 榜主成绩为总计榜用时。")
bullet("可展示实际用时、答错次数、跳题次数与累计罚时，但这些明细不另设排名权重。")

heading("07", "有效性、断线与题池")
subheading("7.1 成绩有效性")
table(["情形", "是否有效", "说明"],
      [["A 自然倒计时结束", "有效（≥1 题）", "正常结束，可更新最佳成绩"],
       ["A 罚时耗尽结束", "有效（≥1 题）", "正常结束，可更新最佳成绩"],
       ["A 一题未答对", "不上榜", "仅保存个人挑战历史"],
       ["B 正常答满 10 题", "有效", "可更新最佳成绩"],
       ["主动中途退出", "无效", "不建档、不上榜，不计入挑战历史"],
       ["断线", "不判无效", "计时继续，可重连恢复原局"]],
      [4.8, 3.4, 8.0])
subheading("7.2 断线与重连")
bullet("断线本身不判无效，允许重连并恢复原局。")
bullet("断线期间服务端计时继续，不暂停、不补偿时间，作答进度与已产生罚时保持不变。")
bullet("断线期间若 A 模式达到结束条件，按正常结束结算，重连后展示结果；B 模式未答满 10 题时保留原局等待继续。")
bullet("断线后玩家主动退出，仍按无效局处理。")
subheading("7.3 题池重置")
bullet("当前难度未抽的候选题耗尽时，重置已抽题池并继续出题，挑战不因此结束。")
bullet("重置后开始新的抽题周期，本局此前出现过的题可以再次被抽到。")
bullet("题池重置不暂停计时，不清除答对题数、答错次数、跳题次数或累计罚时，也不改变 B 模式答对 10 题的要求。")

heading("08", "一局挑战流程")
table(["步骤", "内容"],
      [["1", "登录账号，选择 L1 或 L2"],
       ["2", "选择 A 模式或 B 模式，查看固定规则与罚时说明"],
       ["3", "开始挑战，服务端初始化题池与题目序列，同时开始计时"],
       ["4", "作答：合并牌面、提交答案，或承担罚时主动跳题"],
       ["5", "达到结束条件后结算，不判断胜、负、平"],
       ["6", "展示本局成绩，并与同模式、同难度下的历史最佳成绩比较"],
       ["7", "若刷新纪录则提示“新纪录”，并更新对应排行榜名次"]],
      [2.0, 14.2])

heading("09", "规则速查")
table(["规则点", "口径"],
      [["玩家人数", "单人挑战，不设对手"],
       ["可选难度", "L1 加减级、L2 四则级"],
       ["A 模式", "5 分钟倒计时，答对题数多者优先"],
       ["B 模式", "答对 10 题，总计榜用时短者优先"],
       ["答错罚时", "5 秒"],
       ["跳题罚时", "10 秒"],
       ["单题超时", "不设置"],
       ["A 同题数比较", "答对第 N 题时的计榜用时"],
       ["平局处理", "先取得该成绩者优先"],
       ["最佳成绩", "每个账号每个“模式 × 难度”保留一条"],
       ["零题成绩", "只存个人挑战历史，不上榜"],
       ["中途退出", "本局无效"],
       ["断线", "不判无效，计时继续，可重连"],
       ["题池耗尽", "重置题池继续出题"]],
      [5.0, 11.2])

doc.save("24点游戏_单人挑战与排行榜_规则说明.docx")
print("saved")
