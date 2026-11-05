
"""Build a single-slide competitor analysis deck (16:9, one page)."""

from __future__ import annotations

import os

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Cm, Pt

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "24点竞技游戏 竞品分析.pptx")

CJK = "微软雅黑"
LATIN = "Segoe UI"

NAVY = RGBColor(0x14, 0x24, 0x3A)
BLUE = RGBColor(0x2C, 0x5A, 0xA8)
BLUE_LT = RGBColor(0xE8, 0xF0, 0xFE)
GREEN = RGBColor(0x2F, 0x8F, 0x5B)
GREEN_LT = RGBColor(0xE7, 0xF4, 0xEC)
ORANGE = RGBColor(0xC8, 0x72, 0x24)
ORANGE_LT = RGBColor(0xFD, 0xEF, 0xE2)
PURPLE = RGBColor(0x6A, 0x49, 0xB4)
PURPLE_LT = RGBColor(0xF2, 0xEC, 0xFB)
RED = RGBColor(0xB4, 0x3A, 0x2E)
RED_LT = RGBColor(0xFC, 0xEF, 0xED)
GRAY_BG = RGBColor(0xF5, 0xF7, 0xFA)
GRAY_LINE = RGBColor(0xD6, 0xDD, 0xE7)
MUTED = RGBColor(0x5B, 0x64, 0x70)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

W = 33.867  # cm, 16:9
H = 19.05


def style_run(run, size, bold=False, color=NAVY, cjk=CJK, latin=LATIN):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    run.font.name = latin
    rpr = run._r.get_or_add_rPr()
    rfonts = rpr.find(qn("a:latin"))
    ea = rpr.find(qn("a:ea"))
    if ea is None:
        ea = rpr.makeelement(qn("a:ea"), {})
        rpr.append(ea)
    ea.set("typeface", cjk)
    if rfonts is not None:
        rfonts.set("typeface", latin)


def textbox(slide, x, y, w, h, lines, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP,
            margins=(0, 0, 0, 0)):
    box = slide.shapes.add_textbox(Cm(x), Cm(y), Cm(w), Cm(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = Cm(margins[0])
    tf.margin_right = Cm(margins[1])
    tf.margin_top = Cm(margins[2])
    tf.margin_bottom = Cm(margins[3])
    for i, spec in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = spec.get("align", align)
        if spec.get("space_before") is not None:
            p.space_before = Pt(spec["space_before"])
        p.space_after = Pt(spec.get("space_after", 0))
        p.line_spacing = spec.get("line_spacing", 1.05)
        run = p.add_run()
        run.text = spec["text"]
        style_run(run, spec.get("size", 14), spec.get("bold", False),
                  spec.get("color", NAVY))
    return box


def rounded(slide, x, y, w, h, fill, line=None, radius=0.06, line_w=1.0):
    shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Cm(x), Cm(y), Cm(w), Cm(h))
    shp.adjustments[0] = radius
    if fill is None:
        shp.fill.background()
    else:
        shp.fill.solid()
        shp.fill.fore_color.rgb = fill
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line
        shp.line.width = Pt(line_w)
    shp.shadow.inherit = False
    shp.text_frame.word_wrap = True
    return shp


def pill(slide, x, y, w, h, text, fill, color=WHITE, size=11):
    shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Cm(x), Cm(y), Cm(w), Cm(h))
    shp.adjustments[0] = 0.5
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill
    shp.line.fill.background()
    shp.shadow.inherit = False
    tf = shp.text_frame
    tf.margin_left = Cm(0.1)
    tf.margin_right = Cm(0.1)
    tf.margin_top = Cm(0)
    tf.margin_bottom = Cm(0)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = text
    style_run(r, size, True, color)
    return shp


def card(slide, x, y, w, h, accent, tint, title, lines, title_size=13,
         body_size=10.5, pad_top=0.36):
    rounded(slide, x, y, w, h, tint, line=accent, radius=0.05, line_w=1.25)
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Cm(x), Cm(y + 0.32), Cm(0.2), Cm(h - 0.64))
    bar.fill.solid()
    bar.fill.fore_color.rgb = accent
    bar.line.fill.background()
    bar.shadow.inherit = False
    textbox(slide, x + 0.5, y + pad_top, w - 0.85, 0.75,
            [{"text": title, "size": title_size, "bold": True, "color": accent}])
    specs = []
    for i, ln in enumerate(lines):
        specs.append({
            "text": ln,
            "size": body_size,
            "color": NAVY,
            "space_before": 4 if i else 5,
            "line_spacing": 1.1,
        })
    textbox(slide, x + 0.5, y + pad_top + 0.95, w - 0.9, h - pad_top - 1.15, specs)
    return


def hline(slide, x, y, w, color=GRAY_LINE, thick=0.03):
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Cm(x), Cm(y), Cm(w), Cm(thick))
    line.fill.solid()
    line.fill.fore_color.rgb = color
    line.line.fill.background()
    line.shadow.inherit = False


def build():
    prs = Presentation()
    prs.slide_width = Cm(W)
    prs.slide_height = Cm(H)
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Cm(W), Cm(H))
    bg.fill.solid()
    bg.fill.fore_color.rgb = WHITE
    bg.line.fill.background()
    bg.shadow.inherit = False
    band = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Cm(0.55), Cm(H))
    band.fill.solid()
    band.fill.fore_color.rgb = BLUE
    band.line.fill.background()
    band.shadow.inherit = False

    # 标题：让导师先知道这页回答什么问题
    textbox(slide, 1.5, 0.65, 22, 1.0,
            [{"text": "24 点游戏竞品分析", "size": 29, "bold": True, "color": NAVY}])
    textbox(slide, 1.5, 1.75, 25, 0.65,
            [{"text": "重点回答三个问题：我们有什么不同、哪些做法值得借鉴、首版最需要改什么",
              "size": 12.5, "color": MUTED}])
    pill(slide, 28.6, 0.85, 3.9, 0.78, "2026.11 · 已落地", GREEN, size=10)

    # 一句话结论
    rounded(slide, 1.5, 2.65, 31.0, 1.55, BLUE_LT, line=None, radius=0.08)
    textbox(slide, 2.0, 2.95, 3.0, 0.75,
            [{"text": "先说结论", "size": 12, "bold": True, "color": BLUE}],
            anchor=MSO_ANCHOR.MIDDLE)
    textbox(slide, 5.0, 2.78, 26.8, 1.15,
            [{"text": "我们的优势是「在线双人实时对战」；首要风险「入门题库太小」已按本次结论改掉，方案进入 V1.1。",
              "size": 17, "bold": True, "color": NAVY, "line_spacing": 1.1}],
            anchor=MSO_ANCHOR.MIDDLE)

    # 三个调研发现
    textbox(slide, 1.5, 4.55, 20, 0.6,
            [{"text": "一、调研得到三个结论", "size": 13.5, "bold": True, "color": NAVY}])
    findings = [
        ("01", "差异化在“真人对战”",
         "4 个有公开资料的产品中，没有与本作相同的跨设备实时双人模式。",
         "4 Numbers：各自完成后比成绩；\n24点挑战：同一设备双人。", BLUE, BLUE_LT),
        ("02", "基础作答可以更简单",
         "4 Numbers 通过“点两个数 + 运算符”得到中间结果，玩家不必输入括号。",
         "适合借鉴到加减级、四则级，\n减少输入错误。", GREEN, GREEN_LT),
        ("03", "入门题库明显不足（已修）",
         "1–9 的数字组合共 495 种，仅用加减能算出 24 的只有 31 种。",
         "范围改为 1–13 后有 220 种，\n并加可解率校验与单局不重复。", GREEN, GREEN_LT),
    ]
    x = 1.5
    for no, title, body, note, col, tint in findings:
        rounded(slide, x, 5.2, 10.0, 3.25, tint, line=None, radius=0.06)
        textbox(slide, x + 0.45, 5.48, 0.9, 0.55,
                [{"text": no, "size": 11, "bold": True, "color": col}])
        textbox(slide, x + 1.35, 5.43, 8.1, 0.65,
                [{"text": title, "size": 14, "bold": True, "color": col}])
        textbox(slide, x + 0.45, 6.28, 9.1, 1.15,
                [{"text": body, "size": 11, "color": NAVY, "line_spacing": 1.12}])
        textbox(slide, x + 0.45, 7.47, 9.1, 0.75,
                [{"text": note, "size": 10, "color": MUTED, "line_spacing": 1.08}])
        x += 10.5

    # 最大问题：左边证据，右边建议
    textbox(slide, 1.5, 8.85, 24, 0.6,
            [{"text": "二、关键依据：只比较「仅用加减」入门难度的可解题数", "size": 13.5, "bold": True, "color": NAVY}])
    rounded(slide, 1.5, 9.5, 15.0, 4.25, WHITE, line=GRAY_LINE, radius=0.05)
    textbox(slide, 2.0, 9.78, 13.8, 0.55,
            [{"text": "不同数字范围下，仅用 + − 能算出 24 的牌组数", "size": 11.5, "bold": True, "color": NAVY}])
    table = slide.shapes.add_table(4, 3, Cm(2.0), Cm(10.45), Cm(14.0), Cm(2.35)).table
    for row in table.rows:
        row.height = Cm(0.56)
    for i, wd in enumerate([4.2, 5.0, 4.8]):
        table.columns[i].width = Cm(wd)
    rows = [
        ["数字范围", "可解题数量", "判断"],
        ["1–9（V1.0 原案）", "31 组（6.3%）", "明显不足"],
        ["1–10", "57 组（8.0%）", "仍然偏少"],
        ["1–13（V1.1 采用）", "220 组（12.1%）", "相对充足"],
    ]
    for r_idx in range(4):
        for c_idx in range(3):
            cell = table.cell(r_idx, c_idx)
            cell.margin_left = Cm(0.18)
            cell.margin_right = Cm(0.12)
            cell.margin_top = Cm(0)
            cell.margin_bottom = Cm(0)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.fill.solid()
            cell.fill.fore_color.rgb = GRAY_BG if r_idx == 0 else (GREEN_LT if r_idx == 3 else WHITE)
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT if c_idx == 0 else PP_ALIGN.CENTER
            run = p.add_run()
            run.text = rows[r_idx][c_idx]
            style_run(run, 10.5, r_idx == 0 or r_idx == 3 or c_idx == 0,
                      GREEN if r_idx == 3 else NAVY)
    textbox(slide, 2.0, 13.05, 13.8, 0.45,
            [{"text": "注：由同一求解器穷举；数字可重复，组合去重。", "size": 9, "color": MUTED}])

    rounded(slide, 17.0, 9.5, 15.5, 4.25, GREEN_LT, line=None, radius=0.05)
    textbox(slide, 17.55, 9.82, 14.4, 0.65,
            [{"text": "V1.1 已采用：数字范围 1–13", "size": 14, "bold": True, "color": GREEN}])
    textbox(slide, 17.55, 10.55, 14.4, 1.0,
            [{"text": "31  →  220", "size": 28, "bold": True, "color": GREEN}])
    textbox(slide, 17.55, 11.55, 14.4, 0.55,
            [{"text": "可解题组数约增加 7 倍", "size": 11.5, "bold": True, "color": NAVY}])
    textbox(slide, 17.55, 12.2, 14.2, 1.0,
            [{"text": "加减级、四则级统一 1–13，扩展级 1–12；题池改为「生成参数 + 可解率校验」，单局不重复。",
              "size": 10.5, "color": MUTED, "line_spacing": 1.12}])

    # 下一步：只保留三项决定
    rounded(slide, 1.5, 14.2, 31.0, 3.25, GRAY_BG, line=None, radius=0.05)
    textbox(slide, 2.0, 14.48, 20, 0.6,
            [{"text": "三、三项结论的落地情况（已并入 V1.1）", "size": 13.5, "bold": True, "color": NAVY}])
    actions = [
        ("✓", "题库：已扩到 1–13", "题池改为参数化生成，\n上线前跑可解率校验"),
        ("✓", "作答：已改点牌合并", "加减级、四则级合并作答，\n扩展级保留文本输入"),
        ("✓", "对战结构：保持不变", "在线双人、顶部对比、独立结算页；\n另加单题超时与时长可选"),
    ]
    x = 2.0
    for no, title, body in actions:
        pill(slide, x, 15.35, 0.72, 0.72, no, BLUE, size=10)
        textbox(slide, x + 0.95, 15.28, 8.2, 0.65,
                [{"text": title, "size": 12, "bold": True, "color": NAVY}])
        textbox(slide, x + 0.95, 16.05, 8.2, 0.95,
                [{"text": body, "size": 10.5, "color": MUTED, "line_spacing": 1.1}])
        x += 10.0

    hline(slide, 1.5, 17.85, 31.0)
    textbox(slide, 1.5, 18.0, 28.5, 0.45,
            [{"text": "调研对象：4 Numbers!、24® Game、24点挑战、Math Battle；详细依据见《24点游戏_竞品分析.md》。",
              "size": 8.5, "color": MUTED}])
    textbox(slide, 30.5, 18.0, 2.0, 0.45,
            [{"text": "01", "size": 9, "bold": True, "color": RGBColor(0x9A, 0xA3, 0xAD)}],
            align=PP_ALIGN.RIGHT)

    prs.save(OUT)
    print("saved:", OUT)


if __name__ == "__main__":
    build()