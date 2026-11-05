# -*- coding: utf-8 -*-
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn

FONT = "微软雅黑"
NAVY = RGBColor(0x0F, 0x3D, 0x5C)
NAVY_D = RGBColor(0x08, 0x27, 0x3C)
GREEN = RGBColor(0x1E, 0x7A, 0x55)
GREEN_L = RGBColor(0xE7, 0xF2, 0xEC)
TEAL = RGBColor(0x2C, 0x8C, 0x8C)
TEAL_L = RGBColor(0xE4, 0xF0, 0xF1)
AMBER = RGBColor(0xC0, 0x7A, 0x1B)
GREY = RGBColor(0x5A, 0x66, 0x70)
GREY_L = RGBColor(0x7C, 0x89, 0x93)
INK = RGBColor(0x16, 0x1F, 0x26)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
LINE = RGBColor(0xD3, 0xDF, 0xE7)
BG = RGBColor(0xF7, 0xFA, 0xFC)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
slide = prs.slides.add_slide(prs.slide_layouts[6])

def setfont(run, size, bold=False, color=INK):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    run.font.name = FONT
    rPr = run._r.get_or_add_rPr()
    for tag in ("a:ea", "a:cs"):
        el = rPr.find(qn(tag))
        if el is None:
            el = rPr.makeelement(qn(tag), {})
            rPr.append(el)
        el.set("typeface", FONT)

def box(x, y, w, h, fill=None, line=None, lw=1.0, shape=MSO_SHAPE.RECTANGLE, radius=None):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if fill is None:
        s.fill.background()
    else:
        s.fill.solid(); s.fill.fore_color.rgb = fill
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line; s.line.width = Pt(lw)
    s.shadow.inherit = False
    if radius is not None and shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        s.adjustments[0] = radius
    return s

def text(x, y, w, h, runs, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, spacing=1.0, space_after=0):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = 0; tf.margin_right = 0; tf.margin_top = 0; tf.margin_bottom = 0
    paragraphs = runs if isinstance(runs, list) and runs and isinstance(runs[0], list) else [runs]
    for i, pline in enumerate(paragraphs):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = spacing
        p.space_after = Pt(space_after)
        for (t, size, bold, color) in pline:
            r = p.add_run(); r.text = t; setfont(r, size, bold, color)
    return tb

box(0, 0, 13.333, 7.5, fill=BG)
box(0, 0, 0.18, 7.5, fill=NAVY)

box(0.62, 0.5, 2.1, 0.36, fill=NAVY, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.35)
text(0.62, 0.555, 2.1, 0.3, [("单人挑战 · 规则要点", 11, True, WHITE)], align=PP_ALIGN.CENTER)
text(2.9, 0.53, 3.4, 0.32, [("2026 精简汇报版", 10.5, False, GREY_L)])
text(0.62, 0.98, 9.0, 0.62, [("24 点游戏：单人挑战与排行榜", 30, True, NAVY_D)])
text(0.62, 1.66, 11.9, 0.34, [("两种模式均在账号内独立完成，以个人最佳成绩进入对应排行榜", 12.5, False, GREY)])
box(0.62, 2.06, 12.1, 0.02, fill=LINE)

card_y, card_h, card_w = 2.32, 2.86, 5.86

def mode_card(x, tag, tag_color, tag_bg, title, big, big_unit, lines, foot):
    box(x, card_y, card_w, card_h, fill=WHITE, line=LINE, lw=1.1)
    box(x, card_y, card_w, 0.10, fill=tag_color)
    box(x + 0.34, card_y + 0.34, 0.6, 0.36, fill=tag_bg, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.3)
    text(x + 0.34, card_y + 0.405, 0.6, 0.28, [(tag, 12.5, True, tag_color)], align=PP_ALIGN.CENTER)
    text(x + 1.1, card_y + 0.34, 3.4, 0.36, [(title, 15.5, True, INK)], anchor=MSO_ANCHOR.MIDDLE)
    text(x + 0.36, card_y + 0.86, 2.2, 0.9, [(big, 42, True, tag_color)])
    text(x + 0.38, card_y + 1.62, 3.0, 0.3, [(big_unit, 12.5, True, GREY)])
    box(x + card_w - 2.72, card_y + 0.92, 0.015, 1.66, fill=LINE)
    item_runs = [[(k, 10.5, False, GREY_L), (v, 11.5, True, INK)] for k, v in lines]
    text(x + card_w - 2.5, card_y + 0.96, 2.34, 1.7, item_runs, spacing=1.15, space_after=7)
    box(x + 0.34, card_y + 2.22, card_w - 0.68, 0.44, fill=tag_bg)
    text(x + 0.5, card_y + 2.30, card_w - 1.0, 0.3, [(foot, 9.5, False, tag_color)])

mode_card(0.62, "A", GREEN, GREEN_L, "限时挑战", "5", "分钟倒计时",
          [("成绩口径  ", "答对题数"), ("同题数比较  ", "第 N 题计榜用时"), ("同分  ", "先取得者优先")],
          "时间用尽或罚时耗尽即结算，答对题数多者名次靠前")

mode_card(6.86, "B", TEAL, TEAL_L, "定量挑战", "10", "道题（答对）",
          [("成绩口径  ", "总计榜用时"), ("用时构成  ", "实际用时＋罚时"), ("同分  ", "先取得者优先")],
          "答满 10 题即结束，总计榜用时越短名次越靠前")

strip_y = 5.44
slots = [
    ("难度", "L1 加减级", "1–13，仅用 + −", GREEN),
    ("难度", "L2 四则级", "1–13，+ − × ÷", GREEN),
    ("作答", "点牌合并", "两牌＋算符合并，三步入题", NAVY),
    ("罚时", "答错 5 秒 · 跳题 10 秒", "无单题超时，卡题只耗本局时间", AMBER),
]
sw = 2.94
for i, (tag, head, sub, color) in enumerate(slots):
    x = 0.62 + i * (sw + 0.113)
    box(x, strip_y, sw, 1.16, fill=WHITE, line=LINE, lw=1.0)
    box(x, strip_y, 0.055, 1.16, fill=color)
    text(x + 0.26, strip_y + 0.16, sw - 0.42, 0.24, [(tag, 9.5, True, color)])
    text(x + 0.26, strip_y + 0.44, sw - 0.42, 0.32, [(head, 13, True, INK)])
    text(x + 0.26, strip_y + 0.82, sw - 0.42, 0.28, [(sub, 9.5, False, GREY_L)])

box(0.62, 6.86, 12.1, 0.015, fill=LINE)
text(0.62, 7.0, 8.8, 0.3, [("每账号在 A / B 两个榜、L1 / L2 两个难度下各保留一条最佳成绩", 10, False, GREY)])
text(10.6, 7.0, 2.12, 0.3, [("01 / 01", 10, True, GREY_L)], align=PP_ALIGN.RIGHT)

prs.save(r"D:\24game\docs\24点游戏_单人挑战与排行榜_一页.pptx")
print("saved slides:", len(prs.slides._sldIdLst))
