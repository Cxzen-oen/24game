"""Build a single-slide briefing deck: gameplay + competition rules only."""

from __future__ import annotations

import os

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Cm, Pt

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "24点竞技游戏（玩法与竞技规则）.pptx")

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
    """lines: list of dicts {text,size,bold,color,space_before,line_spacing}"""
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


def card(slide, x, y, w, h, accent, tint, title, lines, title_size=14.5, body_size=11):
    body = rounded(slide, x, y, w, h, tint, line=accent, radius=0.05, line_w=1.25)
    # accent bar on the left
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Cm(x), Cm(y + 0.35), Cm(0.22), Cm(h - 0.7))
    bar.fill.solid()
    bar.fill.fore_color.rgb = accent
    bar.line.fill.background()
    bar.shadow.inherit = False
    textbox(slide, x + 0.55, y + 0.32, w - 0.9, 0.9,
            [{"text": title, "size": title_size, "bold": True, "color": accent}])
    specs = []
    for i, ln in enumerate(lines):
        specs.append({
            "text": ln,
            "size": body_size,
            "color": NAVY,
            "space_before": 4 if i else 6,
            "line_spacing": 1.12,
        })
    textbox(slide, x + 0.55, y + 1.35, w - 0.95, h - 1.7, specs)
    return body


def build():
    prs = Presentation()
    prs.slide_width = Cm(W)
    prs.slide_height = Cm(H)
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    # ---------- background
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Cm(W), Cm(H))
    bg.fill.solid()
    bg.fill.fore_color.rgb = WHITE
    bg.line.fill.background()
    bg.shadow.inherit = False

    # left accent band
    band = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Cm(0.55), Cm(H))
    band.fill.solid()
    band.fill.fore_color.rgb = BLUE
    band.line.fill.background()

    # ---------- header
    textbox(slide, 1.5, 0.9, 18, 1.5,
            [{"text": "24 点竞技游戏", "size": 30, "bold": True, "color": NAVY}])
    textbox(slide, 1.5, 2.35, 20, 0.9,
            [{"text": "双人同题 × 点牌合并作答 × 双模式竞速", "size": 13.5, "color": MUTED}])

    pill(slide, 25.2, 1.05, 3.3, 0.85, "玩法与规则", BLUE, size=11)
    pill(slide, 28.8, 1.05, 3.95, 0.85, "首版定稿 V1.1", RGBColor(0x8A, 0x98, 0xAD), size=11)

    # ---------- rule strip
    strip = rounded(slide, 1.5, 3.45, 30.8, 1.75, GRAY_BG, line=GRAY_LINE, radius=0.10)
    textbox(slide, 2.0, 3.72, 2.4, 1.1,
            [{"text": "基本规则", "size": 13, "bold": True, "color": BLUE}],
            anchor=MSO_ANCHOR.MIDDLE)
    textbox(slide, 4.6, 3.62, 26.9, 1.4,
            [{"text": "每题给出 4 个 1–13 的整数，每个数字必须且只用一次，结果精确等于 24。"
                      "点两张牌 + 一个算符即合并成一张新牌，括号由点击顺序决定；四张并成一张完成作答。",
              "size": 13, "color": NAVY, "line_spacing": 1.12},
             {"text": "双人同题同序 · 不可跳题 · 答错可撤销重试不扣分 · 单题 60 秒超时自动收走",
              "size": 11.5, "color": MUTED, "space_before": 4}],
            anchor=MSO_ANCHOR.MIDDLE)

    # ---------- core rules
    y_c = 5.7
    h_c = 4.35
    textbox(slide, 1.5, 5.15, 14, 0.6,
            [{"text": "一、首版范围：少做功能，做对核心", "size": 14, "bold": True, "color": NAVY}])

    card(slide, 1.5, y_c, 9.6, h_c, GREEN, GREEN_LT, "双人 · 同题同序",
         ["仅 2 人自动匹配，不做多人房", "开局固定题序，逐题下发", "正确答案始终留在服务端"])
    card(slide, 12.1, y_c, 9.6, h_c, BLUE, BLUE_LT, "合并作答 · 精确判题",
         ["点牌合并，括号由点击顺序决定", "服务端逐条校验合并链", "允许中间分数，禁止除零"])
    card(slide, 22.7, y_c, 9.6, h_c, PURPLE, PURPLE_LT, "题池 · 参数化生成",
         ["三档难度：加减 / 四则 / 扩展", "数字 1–13，单局不重复", "可解率校验通过才发布"])

    # ---------- two modes
    y_m = 10.75
    h_m = 4.5
    textbox(slide, 1.5, 10.22, 14, 0.6,
            [{"text": "二、固定两种模式：统一胜负口径", "size": 14, "bold": True, "color": NAVY}])

    # Mode A
    a = rounded(slide, 1.5, y_m, 15.1, h_m, ORANGE_LT, line=ORANGE, radius=0.05, line_w=1.25)
    textbox(slide, 2.1, y_m + 0.35, 13.6, 1.0,
            [{"text": "模式 A · 限时赛：90 / 180 / 300 秒", "size": 14.5, "bold": True, "color": ORANGE}])
    textbox(slide, 2.1, y_m + 1.35, 13.9, 2.9,
            [{"text": "匹配页显示「可作答约 N 题」，到点封盘。", "size": 11.5, "space_before": 0},
             {"text": "先比答对题数；相同比最后一题正确提交的累计用时。", "size": 11.5, "space_before": 7},
             {"text": "仍相同则平局；错误数与超时数不参与胜负。", "size": 11.5, "space_before": 7}])

    # Mode B
    b = rounded(slide, 17.2, y_m, 15.1, h_m, BLUE_LT, line=BLUE, radius=0.05, line_w=1.25)
    textbox(slide, 17.8, y_m + 0.35, 13.6, 1.0,
            [{"text": "模式 B · 定题赛：5 / 10 / 20 题", "size": 14.5, "bold": True, "color": BLUE}])
    textbox(slide, 17.8, y_m + 1.35, 13.9, 2.9,
            [{"text": "匹配页显示「预计用时 X 分 Y 秒」；全局上限 600 秒。", "size": 11.5, "space_before": 0},
             {"text": "先比完成题数；相同再比最后一次正确提交用时。", "size": 11.5, "space_before": 7},
             {"text": "只有完整完成设定题数才刷新个人最快纪录。", "size": 11.5, "space_before": 7}])

    # ---------- account & records
    y_a = 15.75
    acc = rounded(slide, 1.5, y_a, 30.8, 2.55, GRAY_BG, line=GRAY_LINE, radius=0.06)
    textbox(slide, 2.0, y_a + 0.22, 4.2, 0.8,
            [{"text": "三、账号与战绩", "size": 12.5, "bold": True, "color": NAVY}])

    chips = [
        ("基础战绩", "按模式统计胜 / 负 / 平", GREEN),
        ("限时赛", "答对题数与累计答对题数", ORANGE),
        ("定题赛", "完整完成的最快用时", BLUE),
        ("首版后置", "排行榜 · 段位 · 观战 · 回放", PURPLE),
    ]
    cx = 5.0
    widths = [5.0, 6.4, 6.4, 7.3]
    for (t, s, col), cw in zip(chips, widths):
        rounded(slide, cx, y_a + 0.28, cw, 2.0, WHITE, line=GRAY_LINE, radius=0.08)
        textbox(slide, cx + 0.3, y_a + 0.45, cw - 0.6, 0.7,
                [{"text": t, "size": 11.5, "bold": True, "color": col}])
        textbox(slide, cx + 0.3, y_a + 1.18, cw - 0.6, 0.9,
                [{"text": s, "size": 10.5, "color": MUTED, "line_spacing": 1.1}])
        cx += cw + 0.5

    # ---------- footer
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Cm(1.5), Cm(18.35), Cm(30.8), Cm(0.03))
    line.fill.solid()
    line.fill.fore_color.rgb = GRAY_LINE
    line.line.fill.background()
    textbox(slide, 1.5, 18.45, 24, 0.55,
            [{"text": "服务端统一计时、判题与结算；断线超时判负，存档失败的对局标为无效。", 
              "size": 9.5, "color": MUTED}])
    textbox(slide, 27.5, 18.45, 4.8, 0.55,
            [{"text": "01", "size": 9.5, "bold": True, "color": RGBColor(0x9A, 0xA3, 0xAD)},
             ], align=PP_ALIGN.RIGHT)

    prs.save(OUT)
    print("saved:", OUT)


if __name__ == "__main__":
    build()