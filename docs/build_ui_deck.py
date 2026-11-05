"""Build a two-page UI deck containing PC and mobile screens."""
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "24点竞技游戏_界面设计稿_PC与移动端.docx"
PC = ROOT / "design"
MB = ROOT / "design" / "mobile"

INK = RGBColor(0x1B, 0x22, 0x33)
MUTED = RGBColor(0x5D, 0x68, 0x80)
PRIMARY = RGBColor(0x5B, 0x4B, 0xDB)
LIGHT = RGBColor(0x8B, 0x95, 0xA8)
FONT = "微软雅黑"


def font(run, size=10.5, bold=False, color=INK):
    run.font.name = FONT
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    run._element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:eastAsia"), FONT)
    return run


def para(doc, text, size=10.5, bold=False, color=INK, before=0, after=4, align=None, line=1.3):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    pf.line_spacing = line
    if align is not None:
        p.alignment = align
    font(p.add_run(text), size, bold, color)
    return p


def heading(doc, no, text, before=2, break_before=False):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.space_after = Pt(6)
    font(p.add_run(no + "  "), 13, True, PRIMARY)
    font(p.add_run(text), 13, True)
    border = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    for k, v in [("val", "single"), ("sz", "6"), ("space", "3"), ("color", "D8DEEB")]:
        bottom.set(qn("w:" + k), v)
    border.append(bottom)
    p._p.get_or_add_pPr().append(border)
    if break_before:
        p.paragraph_format.page_break_before = True


def picture(doc, path, width_cm=16.2):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(str(path), width=Cm(width_cm))


def caption(doc, text, after=8):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(after)
    font(p.add_run(text), 8.5, False, LIGHT)


def bullet(doc, lead, text):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.left_indent = Cm(0.4)
    pf.first_line_indent = Cm(-0.4)
    pf.space_after = Pt(2)
    pf.line_spacing = 1.2
    font(p.add_run("· "), 10, True, PRIMARY)
    font(p.add_run(lead), 9.5, True, INK)
    font(p.add_run(text), 9.5, False, MUTED)
    return p


def page_break(doc):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(0)
    p.add_run().add_break(WD_BREAK.PAGE)


def build():
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.left_margin = sec.right_margin = Cm(2.2)
    sec.top_margin = Cm(1.6)
    sec.bottom_margin = Cm(1.5)

    normal = doc.styles["Normal"]
    normal.font.name = FONT
    normal.font.size = Pt(10.5)
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)

    footer = sec.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    font(footer.add_run("24 点双人对战  ·  界面设计稿  ·  第 "), 8.5, False, LIGHT)
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), "PAGE")
    footer._p.append(fld)

    # ---------------- 第 1 页
    para(doc, "界面设计稿", 10, True, PRIMARY, after=4)
    para(doc, "24 点双人对战", 24, True, after=2)
    para(doc, "PC 端与移动端 · 共 6 个页面", 10.5, False, MUTED, after=8)

    heading(doc, "一", "PC 端：主界面与对战页")
    picture(doc, PC / "主界面.png", 15.0)
    caption(doc, "PC 主界面：三档难度、两种模式；限时赛 90/180/300 秒、定题赛 5/10/20 题可直接选，并显示「可作答约 N 题」或「预计用时」。")
    picture(doc, PC / "对战界面.png", 15.0)
    caption(doc, "PC 对战页：点牌合并作答——点两张牌（高亮）再点算符即合并成一张新牌，上方步骤条显示合并过程，可撤销；提交后服务端逐条校验合并链。")

    # ---------------- 第 2 页
    heading(doc, "二", "PC 端：结算页", break_before=True)
    picture(doc, PC / "结算界面.png", 10.5)
    caption(doc, "PC 结算页：胜负结论、双方数据、判定依据、最快纪录与累计答对题数。")

    heading(doc, "三", "移动端：主界面、对战页、结算页", before=6)
    para(doc, "移动端按 390×844 单独布局，单列纵向排列；对战页同样用点牌合并，算符按钮触控高度 52px。", 9.5, False, MUTED, after=6)

    tbl = doc.add_table(rows=1, cols=3)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    for i, (fn, cap) in enumerate([
        ("主界面.png", "主界面：难度与模式"),
        ("对战界面.png", "对战页：计时与键盘"),
        ("结算界面.png", "结算页：胜负与数据"),
    ]):
        cell = tbl.rows[0].cells[i]
        cell.width = Cm(5.2)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(2)
        p.add_run().add_picture(str(MB / fn), width=Cm(4.5))
        cp = cell.add_paragraph()
        cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cp.paragraph_format.space_after = Pt(0)
        font(cp.add_run(cap), 8, False, LIGHT)

    para(doc, "四  ·  设计要点", 11.5, True, INK, before=6, after=3)
    bullet(doc, "信息层级：", "双方比分固定顶部左右，计时器居中；题目与作答区自上而下排列。")
    bullet(doc, "作答路径：", "输入、提交、反馈、键盘四层分离；答错保留算式，可直接修改。")
    bullet(doc, "移动适配：", "不缩放桌面版；压缩对比区、放大计时与数字牌，主要按钮置于拇指区域。")
    bullet(doc, "范围一致：", "两套界面均使用三档难度与限时、定题两种模式。")


    doc.save(OUT)
    print(OUT)


if __name__ == "__main__":
    build()