
"""Build a one-page competitor analysis report (A4, single page)."""
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

HERE = Path(__file__).resolve().parent
OUT = HERE / "24点竞技游戏_竞品分析一页汇报.docx"
FONT = "微软雅黑"
INK = RGBColor(0x19, 0x32, 0x38)
GREEN = RGBColor(0x1D, 0x6A, 0x5E)
GRAY = RGBColor(0x65, 0x71, 0x72)
RED = RGBColor(0xA8, 0x3A, 0x2C)
LIGHT = "EFF4F0"
HEAD = "DCE9E2"
WARN = "FBEDEA"


def font(run, size=9, bold=False, color=INK):
    run.font.name = FONT
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    run._element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:eastAsia"), FONT)
    return run


def p(doc, text="", size=9, bold=False, color=INK, before=0, after=3, align=None, spacing=1.18):
    para = doc.add_paragraph()
    para.paragraph_format.space_before = Pt(before)
    para.paragraph_format.space_after = Pt(after)
    para.paragraph_format.line_spacing = spacing
    if align is not None:
        para.alignment = align
    font(para.add_run(text), size, bold, color)
    return para


def section(doc, label, text, before=8):
    para = doc.add_paragraph()
    para.paragraph_format.space_before = Pt(before)
    para.paragraph_format.space_after = Pt(5)
    font(para.add_run(label + "  "), 11, True, GREEN)
    font(para.add_run(text), 11, True, INK)
    line = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    for key, value in [("val", "single"), ("sz", "6"), ("space", "3"), ("color", "B9CEC2")]:
        bottom.set(qn("w:" + key), value)
    line.append(bottom)
    para._p.get_or_add_pPr().append(line)


def shade(cell, color):
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), color)
    cell._tc.get_or_add_tcPr().append(shd)


def cell_text(cell, text, bold=False, size=8, color=INK, align=None):
    cell.text = ""
    para = cell.paragraphs[0]
    para.paragraph_format.space_before = Pt(0)
    para.paragraph_format.space_after = Pt(0)
    para.paragraph_format.line_spacing = 1.0
    if align is not None:
        para.alignment = align
    font(para.add_run(text), size, bold, color)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def table(doc, rows, widths, size=8, highlight_rows=(), aligns=None, head=True):
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
        cells = tbl.rows[-1].cells
        for i, (cell, value) in enumerate(zip(cells, values)):
            cell.width = Cm(widths[i])
            al = aligns[i] if aligns else None
            is_head = head and r_idx == 0
            cell_text(cell, value, bold=is_head or i == 0, size=size,
                      color=GREEN if is_head else INK, align=al)
            if is_head:
                shade(cell, HEAD)
            elif r_idx in highlight_rows:
                shade(cell, WARN)
    return tbl


def bullet(doc, lead, text, size=9):
    para = doc.add_paragraph()
    para.paragraph_format.left_indent = Cm(0.42)
    para.paragraph_format.first_line_indent = Cm(-0.42)
    para.paragraph_format.space_after = Pt(3)
    para.paragraph_format.line_spacing = 1.18
    font(para.add_run("•  " + lead), size, True, GREEN)
    font(para.add_run(text), size)
    return para


def build():
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.left_margin = sec.right_margin = Cm(1.7)
    sec.top_margin = Cm(1.3)
    sec.bottom_margin = Cm(1.1)
    sec.header_distance = Cm(0.6)
    sec.footer_distance = Cm(0.6)
    normal = doc.styles["Normal"]
    normal.font.name = FONT
    normal.font.size = Pt(9)
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    footer = sec.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    font(footer.add_run("24 点双人对战项目  ·  竞品分析一页汇报  ·  "), 7.5, color=GRAY)
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), "PAGE")
    footer._p.append(fld)

    # ---------- title
    p(doc, "汇报材料 · 竞品分析", 8.5, True, GREEN, after=3)
    p(doc, "24 点游戏竞品分析：界面、规则与数字生成", 19, True, after=4)
    p(doc, "调研 7 款产品，其中 4 款取得原始页面文案；另用求解器穷举实测自研题池的数字可解率。结论按“该学什么、该改什么”给出。",
      9, color=GRAY, after=2)

    # ---------- 1. 覆盖度
    section(doc, "01", "调研范围：真正能对标的只有 4 家")
    table(doc, [
        ["产品", "形态", "对战方式", "数字 / 难度规则", "证据"],
        ["4 Numbers!（4nums.com）", "网页 + 双端 App", "异步挑战、全球排名", "按数字幅度分档", "官网页面，高"],
        ["24® Game（Suntex）", "实体卡牌 + 赛事", "面对面多人", "按算符出 5 种牌组", "官网商店，高"],
        ["24点挑战（iOS）", "单机 + 本地双人", "同设备双人", "按算符 + 是否需分数", "App Store，高"],
        ["Math Battle（PLIX）", "网页", "同屏双人抢答", "选择题，非 24 点", "官网介绍，高"],
        ["算24點 / 魔幻24算", "iOS / 旧作", "未核实", "未核实", "下架 / 反爬，未纳入"],
    ], [4.3, 3.3, 3.4, 3.9, 2.8], size=7.8)
    p(doc, "刷题 PK 需登录、其余两款已下架或反爬，均未纳入结论；表格中“未核实”不做推断。",
      7.5, color=GRAY, before=3)

    # ---------- 2. 数字生成规则
    section(doc, "02", "数字生成规则：行业主流做法不是“按算符”，而是“按数字幅度”")
    table(doc, [
        ["思路", "代表产品", "具体定义", "评价"],
        ["按算符", "24® Game 牌组、本作 L1/L2/L3", "加减小包 6 岁用；乘除包 8 岁；四则 9 岁", "玩家不用重学规则，但各档可解率差异极大"],
        ["按数字幅度", "4 Numbers!", "Easy≤10；Medium≤20 且至少一个>10；Hard≤36 且至少一个>20", "题目形态统一，靠数字大小产生梯度"],
        ["按解法特征", "24点挑战", "中级 = 解法需要中间分数", "贴合认知难点，但这类题数量极少"],
    ], [2.5, 4.4, 6.6, 4.2], size=7.8)
    p(doc, "本作目前属于“按算符”一派。问题不是思路错，而是 L1 这一档在数学上撑不起来——见下节实测。",
      8, color=GRAY, before=3)

    # ---------- 3. 实测
    section(doc, "03", "关键发现：本作 L1 的可解题只有 31 组")
    p(doc, "以本项目判题器同一套有理数规则，穷举四数字所有组合（数字可重复、组合去重）：", 8.8, after=3)
    table(doc, [
        ["数字范围", "全部组合", "仅 + − 可解", "占比", "四则可解", "占比", "需分数才可解"],
        ["1–9（本作现设定）", "495", "31", "6.3%", "404", "81.6%", "7（1.7%）"],
        ["1–10（4nums Easy）", "715", "57", "8.0%", "566", "79.2%", "10（1.8%）"],
        ["1–13（扑克牌 A–K）", "1820", "220", "12.1%", "1362", "74.8%", "16（1.2%）"],
    ], [4.5, 2.2, 2.5, 1.8, 2.3, 1.8, 2.6], size=7.8, highlight_rows=(1,),
        aligns=[None, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT,
                WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT])
    bullet(doc, "L1 有硬伤：", "1–9 下仅用加减能凑出 24 的组合共 31 组，撑不起“每局 10 题不重复”的对局，真实比赛会反复出现死题。", 8.5)
    bullet(doc, "修法：", "数字上限放宽到 1–13，L1 可解组数 31→220（约 7 倍），且与“扑克牌 A–K”的经典直觉一致；只放宽到 1–10 也能到 57。", 8.5)
    bullet(doc, "“数字越大越难”并不严格：", "1–10 的四则可解率（79.2%）反而低于 1–9（81.6%）。范围一大，无解题更多，所以 4 Numbers 必须配“跳过扣时”机制来消化死题。", 8.5)
    bullet(doc, "“必须用分数”撑不起一档难度：", "在 1–9 下只占 7 组。24点挑战把“需要分数”当作中级难度整档，说明其实际数字范围应大于我们。", 8.5)

    # ---------- 4. 界面与规则
    section(doc, "04", "界面与规则对比：三点值得直接借鉴")
    table(doc, [
        ["对比项", "本作现状", "竞品做法", "建议"],
        ["作答方式", "自由文本输入 + 键盘，括号要自己打", "4 Numbers：点两数 + 运算符，中间结果并成一张牌，永不打括号", "L1/L2 改点击合并，L3（幂/开方/阶乘）保留文本"],
        ["对比信息", "三段式纵向：你 / 计时 / 对手", "Math Battle 放两侧键位区；棋类放上下对称", "保持纵向，但对手只显示“已答对 N 题”，不露算式"],
        ["节奏", "秒表制造紧迫", "4 Numbers：解出 +10 秒、跳过 −20 秒；Math Battle 难度随进程递增", "借“进程递增”编排题序，末段加压"],
        ["局外积累", "胜率 + 最快用时", "4 Numbers 累计解题 695 万次 + 月度榜", "补“累计答对题数”作长期目标"],
        ["实时对战", "真正跨设备同步匹配", "24点挑战把本地双人写成“实时对战”", "文案上主动区分，强调“真同步”"],
    ], [2.4, 4.6, 5.6, 5.1], size=7.8)

    # ---------- 5. 结论
    section(doc, "05", "结论与建议")
    table(doc, [
        ["优先级", "事项", "理由", "判断依据"],
        ["P0", "重定 L1 数字范围（建议 1–13），题池生成前先跑可解率验证", "31 组不成池，直接影响首版能否开局", "§03 实测"],
        ["P0", "保留单题超时机制", "本作答错不扣分且不可跳题，无超时则卡题拖垮结算", "与竞品“跳过扣时”同解"],
        ["P1", "L1/L2 改“点牌合并”输入", "把括号负担从玩家身上移除，降低误判", "4 Numbers 已验证"],
        ["P1", "匹配页增加时长预设与总时长预估", "小成本高感知，提升开赛前确定感", "24点挑战做法"],
    ], [1.5, 5.4, 5.9, 4.9], size=7.8,
        aligns=[WD_ALIGN_PARAGRAPH.CENTER, None, None, None])
    p(doc, "落地情况（V1.1 已并入规则定稿与界面稿）：数字范围改为 1–13（扩展级 1–12）并加可解率校验；"
           "L1/L2 已改为点牌合并、L3 保留文本输入；新增单题 60 秒超时；限时赛 90/180/300 秒、定题赛 5/10/20 题并显示预估；"
           "题序按前易后难编排；战绩新增累计答对题数。P2 的同屏双人与线下赛事包仍按后置处理。",
      7.5, color=GREEN, before=4)

    para = doc.add_paragraph()
    para.paragraph_format.space_before = Pt(9)
    para.paragraph_format.space_after = Pt(2)
    font(para.add_run("一句话结论："), 9, True, GREEN)
    font(para.add_run("竞品界面上没有颠覆性设计，真正拉开差距的是“数字怎么生成”和“作答怎么输入”。建议首版先解决 L1 题池不足（P0），再借鉴 4 Numbers 的点牌合并重做 L1/L2 作答，界面其余结构沿用现有方案即可。"),
         9, color=INK)

    doc.save(OUT)
    print(OUT)


if __name__ == "__main__":
    build()