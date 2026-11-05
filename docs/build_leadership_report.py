"""Create the three-page leadership report for the 24-point game."""
from pathlib import Path
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

HERE = Path(__file__).resolve().parent
OUT = HERE / "24点竞技游戏_三页汇报.docx"
FONT = "微软雅黑"
INK = RGBColor(0x19, 0x32, 0x38)
GREEN = RGBColor(0x1D, 0x6A, 0x5E)
GRAY = RGBColor(0x65, 0x71, 0x72)
LIGHT = "EFF4F0"


def font(run, size=10.5, bold=False, color=INK):
    run.font.name = FONT
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    run._element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:eastAsia"), FONT)
    return run


def p(doc, text="", size=10.5, bold=False, color=INK, before=0, after=5, align=None):
    para = doc.add_paragraph()
    para.paragraph_format.space_before = Pt(before)
    para.paragraph_format.space_after = Pt(after)
    para.paragraph_format.line_spacing = 1.25
    if align is not None:
        para.alignment = align
    font(para.add_run(text), size, bold, color)
    return para


def title(doc, number, text):
    para = doc.add_paragraph()
    para.paragraph_format.space_before = Pt(0)
    para.paragraph_format.space_after = Pt(9)
    font(para.add_run(number + "  "), 16, True, GREEN)
    font(para.add_run(text), 16, True)
    line = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    for key, value in [("val", "single"), ("sz", "7"), ("space", "5"), ("color", "B9CEC2")]:
        bottom.set(qn("w:" + key), value)
    line.append(bottom)
    para._p.get_or_add_pPr().append(line)


def cell_text(cell, text, bold=False, size=9.5, color=INK):
    cell.text = ""
    para = cell.paragraphs[0]
    para.paragraph_format.space_after = Pt(0)
    para.paragraph_format.line_spacing = 1.2
    font(para.add_run(text), size, bold, color)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def table(doc, rows, widths):
    tbl = doc.add_table(rows=0, cols=len(widths))
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement("w:" + edge)
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "4")
        el.set(qn("w:color"), "D8E1DB")
        borders.append(el)
    tbl._tbl.tblPr.append(borders)
    for r_idx, values in enumerate(rows):
        cells = tbl.add_row().cells
        for i, (cell, value) in enumerate(zip(cells, values)):
            cell.width = Cm(widths[i])
            cell_text(cell, value, bold=(r_idx == 0 or i == 0), size=9.5)
            if r_idx == 0:
                shd = OxmlElement("w:shd")
                shd.set(qn("w:fill"), LIGHT)
                cell._tc.get_or_add_tcPr().append(shd)
    return tbl


def bullet(doc, lead, text):
    para = doc.add_paragraph()
    para.paragraph_format.left_indent = Cm(0.45)
    para.paragraph_format.first_line_indent = Cm(-0.45)
    para.paragraph_format.space_after = Pt(5)
    para.paragraph_format.line_spacing = 1.25
    font(para.add_run("•  " + lead), 10.5, True, GREEN)
    font(para.add_run(text), 10.5)
    return para


def page_break(doc):
    para = doc.add_paragraph()
    para.paragraph_format.space_after = Pt(0)
    para.add_run().add_break(WD_BREAK.PAGE)


def build():
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.left_margin = sec.right_margin = Cm(2.1)
    sec.top_margin = Cm(1.8)
    sec.bottom_margin = Cm(1.6)
    sec.header_distance = Cm(0.8)
    sec.footer_distance = Cm(0.8)
    normal = doc.styles["Normal"]
    normal.font.name = FONT
    normal.font.size = Pt(10.5)
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    footer = sec.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    font(footer.add_run("24 点双人对战项目  ·  "), 8.5, color=GRAY)
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), "PAGE")
    footer._p.append(fld)

    # Page 1
    p(doc, "项目汇报", 10, True, GREEN, after=9)
    p(doc, "24 点双人对战游戏", 27, True, after=7)
    p(doc, "首版方案：双人同题 · 点牌合并作答 · 三档难度 · 时长可选", 12, color=GRAY, after=16)
    p(doc, "一、项目要做什么", 14, True, after=7)
    p(doc, "项目拟开发一款网页端 24 点对战游戏。两名玩家同时进入同一道题，在限定时间内提交算式，系统自动判题并给出结果。首版重点是完成匹配、作答、判题和战绩保存这一条完整流程，先保证运行稳定，再考虑扩展玩法。", after=12)
    title(doc, "01", "玩法与胜负规则")
    p(doc, "每题给出 4 个 1–13 的数字，每个数字必须且只能使用一次，算出 24。作答改为「点牌合并」：点两张牌、再点一个算符，中间结果并成一张新牌，四张并成一张就完成，括号由点击顺序自动决定，玩家不用再打括号。加减级只能点加减，四则级可以加减乘除；扩展级要用幂、开方和阶乘，保留手动输入。双方题目和顺序完全相同，答错可以撤销重试，不扣分，也不能跳题；同一题卡住 60 秒自动收走，继续计时。", after=9)
    table(doc, [
        ["模式", "比赛设置", "胜负判定"],
        ["限时赛", "90 / 180 / 300 秒，默认 180 秒", "先比答对题数；相同再比累计用时"],
        ["定题赛", "5 / 10 / 20 题，默认 10 题，最长 600 秒", "先比完成题数；相同再比累计用时"],
    ], [3.0, 6.2, 7.3])
    p(doc, "选完时长或题数，匹配页会直接显示「可作答约 N 题」或「预计用时 X 分 Y 秒」，开局前就知道这一局要打多久。完成数和用时仍相同则判平局；只有完整完成设定题数，才记录个人最快用时。", 9.5, color=GRAY, before=7, after=10)
    title(doc, "02", "首版范围")
    bullet(doc, "保留：", "账号登录、双人匹配、三档难度、两种模式（时长/题数可选）、点牌合并作答、单题超时、个人战绩与累计答对题数。")
    bullet(doc, "暂缓：", "多人房、排行榜、段位、观战和回放。")
    bullet(doc, "这样安排的原因：", "竞品调研显示，真正影响体验的是「题目怎么出」和「答案怎么输」，而不是界面花样。因此首版把力气压在题池可解率和点牌合并上，其余功能克制，便于集中测试判题、计时和结算。")

    # Page 2
    page_break(doc)
    title(doc, "03", "界面初稿与操作流程")
    p(doc, "对战页按「顶部双方对比、中部题目、底部作答」的顺序组织：中央大计时器是视觉重心。题目区的四张牌可以直接点选，点中的牌高亮，再点下方算符就合并成一张新牌；合并过程显示在上方步骤条里，随时可以撤销一步。主界面负责选难度、模式、时长并开始匹配，结算单独成页。", after=8)
    pic = doc.add_paragraph()
    pic.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pic.paragraph_format.space_after = Pt(5)
    pic.add_run().add_picture(str(HERE.parent / "design" / "对战界面.png"), width=Cm(16.7))
    p(doc, "对战页初稿：顶部双方比分与中央计时器，中部题目，底部输入、提交、反馈与数字符号键盘。", 8.5, color=GRAY, after=10, align=WD_ALIGN_PARAGRAPH.CENTER)
    table(doc, [
        ["步骤", "玩家操作", "系统处理"],
        ["1. 进入比赛", "选难度、模式、时长后匹配", "双人入场后同时开始，并显示本局用时预估"],
        ["2. 作答", "点两张牌 + 一个算符，合并三次成一张牌后提交", "逐条校验合并链，精确求值等于 24"],
        ["3. 继续答题", "答对后进入下一题；卡住 60 秒自动收走", "同步双方进度、剩余时间和超时状态"],
        ["4. 查看结果", "时间到或双方完成", "统一结算并保存战绩与累计题数"],
    ], [2.7, 6.4, 7.4])
    p(doc, "页面还需覆盖三种状态：匹配等待、断线重连、比赛结果。结算页只显示胜负、答对题数和用时，不增加复杂积分。三份页面初稿：design/主界面.html、design/对战界面.html、design/结算界面.html。", 10, before=10)

    # Page 3
    page_break(doc)
    title(doc, "04", "实现安排与验收重点")
    p(doc, "首版采用网页前端、实时对战服务和数据库三部分。出题、计时、判题、结算均由服务端处理，页面只负责输入和展示，避免不同玩家看到的结果不一致。", after=11)
    table(doc, [
        ["工作项", "主要内容", "完成标准"],
        ["规则与界面", "确定页面、算式格式和题池", "两种模式均可完整试玩"],
        ["对战功能", "匹配、同步、判题、结算", "双方进度一致，结果唯一"],
        ["账号与战绩", "登录、对局记录、最快用时", "不重复记录，不错误刷新纪录"],
        ["测试与上线", "异常操作、断线、超时测试", "完成核心验收后部署"],
    ], [3.0, 6.4, 7.1])
    title(doc, "05", "优先控制的四类问题")
    bullet(doc, "判题准确：", "支持分数运算，按难度限制算符；合并链逐条校验，伪造步骤、除零、步数不对一律拒绝。")
    bullet(doc, "计时一致：", "以服务端时间为准；截止后提交无效；单题 60 秒超时也由服务端触发，不改题序、不扣分。")
    bullet(doc, "结算唯一：", "重复点击、网络重发不能重复加题或重复写入战绩。")
    bullet(doc, "异常有结果：", "断线保留 60 秒且比赛计时继续；超时未回判负，双方均掉线则本局无效。")
    p(doc, "验收方式", 12, True, before=8, after=6)
    p(doc, "用两名测试账号完整跑通两种模式、三档难度和每档时长/题数组合，重点检查双方同题、单题超时、超时封盘、重复提交、断线重连和存档失败；上线前先跑每个难度的可解率校验，确认题池够用且单局不重样。以上场景通过后再上线；暂不增加首版范围之外的功能。", after=10)
    p(doc, "本次汇报结论", 10, True, GREEN, before=8, after=4)
    p(doc, "方案已按竞品调研完成修订：作答改点牌合并、题池改参数化生成并做可解率校验、补单题超时与时长预估。范围已收敛，可按首版规则进入页面和规则模块开发。", 11, True)

    doc.save(OUT)
    print(OUT)


if __name__ == "__main__":
    build()