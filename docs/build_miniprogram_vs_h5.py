"""Build the mini program vs H5 decision brief (DOCX)."""
from __future__ import annotations

import os
from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "小程序vsH5_方案对比.docx")

CJK = "微软雅黑"
LATIN = "Segoe UI"
CLR_TITLE = RGBColor(0x1B, 0x2A, 0x3A)
CLR_HEAD = RGBColor(0x2C, 0x5A, 0xA8)
CLR_MUTED = RGBColor(0x5B, 0x64, 0x70)
CLR_WHITE = RGBColor(0xFF, 0xFF, 0xFF)
CLR_ACCENT = RGBColor(0x0F, 0x6B, 0x5C)
FILL_HEAD = "2C5AA8"
FILL_BOX = "EAF1FB"
FILL_ALT = "F7F9FC"
FILL_WARN = "FFF4E5"
BORDER = "C9D3E0"


def set_font(run, size=10.5, bold=False, color=None):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.name = LATIN
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    rfonts.set(qn("w:ascii"), LATIN)
    rfonts.set(qn("w:hAnsi"), LATIN)
    rfonts.set(qn("w:eastAsia"), CJK)
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


def para(text="", size=10.5, bold=False, color=None, space_after=4, align=None):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.25
    if align is not None:
        p.alignment = align
    if text:
        r = p.add_run(text)
        set_font(r, size, bold, color)
    return p


def head(text, size=13):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(4)
    r = p.add_run(text)
    set_font(r, size, True, CLR_HEAD)
    return p


def bullet(text, bold_prefix=""):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.2
    if bold_prefix:
        r = p.add_run(bold_prefix)
        set_font(r, 10.5, True)
    r = p.add_run(text)
    set_font(r, 10.5)
    return p


def make_table(headers, rows, widths):
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    table_borders(table)
    cell_margins(table)
    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.width = Cm(widths[i])
        shade(cell, FILL_HEAD)
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        set_font(r, 9, True, CLR_WHITE)
    for idx, row in enumerate(rows):
        cells = table.add_row().cells
        for i, value in enumerate(row):
            cells[i].width = Cm(widths[i])
            cells[i].vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            if idx % 2 == 1:
                shade(cells[i], FILL_ALT)
            p = cells[i].paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.1
            if i == 0:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run(value)
            set_font(r, 8.6, i == 0)
    return table


doc = Document()
sec = doc.sections[0]
sec.page_width = Cm(21)
sec.page_height = Cm(29.7)
sec.top_margin = Cm(1.8)
sec.bottom_margin = Cm(1.6)
sec.left_margin = Cm(2.0)
sec.right_margin = Cm(2.0)

normal = doc.styles["Normal"]
normal.font.name = LATIN
normal.font.size = Pt(10.5)
normal.element.rPr.rFonts.set(qn("w:eastAsia"), CJK)

# Title
p = doc.add_paragraph()
p.paragraph_format.space_after = Pt(2)
r = p.add_run("24 点项目：小程序 vs H5 方案对比")
set_font(r, 20, True, CLR_TITLE)

p = doc.add_paragraph()
p.paragraph_format.space_after = Pt(10)
r = p.add_run("汇报对象：导师 / 学院　·　2026-11-05　·　用于决定活动入口形态与服务器方案")
set_font(r, 9.5, False, CLR_MUTED)

# Conclusion box
box = doc.add_table(rows=1, cols=1)
box.alignment = WD_TABLE_ALIGNMENT.CENTER
box.autofit = False
box_border = OxmlElement("w:tblBorders")
for edge in ("top", "left", "bottom", "right"):
    el = OxmlElement(f"w:{edge}")
    el.set(qn("w:val"), "single")
    el.set(qn("w:sz"), "4")
    el.set(qn("w:space"), "0")
    el.set(qn("w:color"), "B7C8E8")
    box_border.append(el)
box._tbl.tblPr.append(box_border)
cell = box.rows[0].cells[0]
cell.width = Cm(16.6)
shade(cell, FILL_BOX)
cell_margins(box, 140, 140, 160, 160)
p = cell.paragraphs[0]
p.paragraph_format.space_after = Pt(4)
r = p.add_run("结论：先做 H5 + 迁移导师服务器，小程序（web-view 套壳）作为二期并行评估。")
set_font(r, 11, True, CLR_ACCENT)
p2 = cell.add_paragraph()
p2.paragraph_format.space_after = Pt(0)
p2.paragraph_format.line_spacing = 1.2
r2 = p2.add_run("换服务器是两条路都要做的事；小程序里的游戏仍然是现在的 H5，先迁移不会浪费。")
set_font(r2, 9.8, False, CLR_TITLE)

# 1
head("一、为什么不是“二选一”")
bullet("两条路都需要服务器、数据库、域名和 HTTPS；小程序只是把 H5 装进微信入口，不能替代后端和部署。")
bullet("H5 上线快、不审核；小程序胜在公众号文章内一键进入、微信身份、最近使用可复访。")
bullet("先迁 H5 保活动，再决定要不要花 3～5 周做小程序，风险最低。", "建议：")

# 2 comparison table
head("二、三种方案对比")
headers = ["维度", "A. H5 + 换服务器", "B. web-view 小程序", "C. 原生小程序"]
rows = [
    ["用户入口", "阅读原文、二维码、官网/群链接", "公众号文章内小程序卡片，一键进入", "同 B"],
    ["微信体验", "普通网页，需登录或游客", "小程序壳 + 微信身份 + 最近使用", "最原生"],
    ["开发量", "0（现有 H5）", "壳 + 登录桥，约 3～5 天", "前端重写 1～2 周+"],
    ["上线周期", "约 1 周（域名现成）", "约 3～5 周（备案 + 审核）", "4～6 周+"],
    ["必要资质", "域名 + HTTPS", "非个人主体 + 备案 + 业务域名 + 公众号", "同 B，另加类目要求"],
    ["登录身份", "用户名密码 / 游客", "wx.login + 一次性 ticket", "同 B"],
    ["持续玩", "服务端存档；靠收藏/历史", "服务端存档 + 微信最近使用", "同 B"],
    ["审核风险", "无", "中：纯 web-view 易判无实质内容", "中高：类目/游戏判定"],
    ["服务器", "需要（建议 4C8G 起）", "同样需要", "同样需要"],
    ["适合", "活动近、入口不限微信", "公众号为主、能等 3～5 周", "长期产品、愿意重写"],
]
make_table(headers, rows, [2.6, 4.7, 4.9, 4.4])

# 3 key differences
head("三、关键差异（大白话）")
bullet("公众号正文不能放普通外链，H5 只能走文末“阅读原文”或二维码；小程序卡片可以放在正文里，点一下直接进。", "文章里怎么点：")
bullet("H5 游客只认浏览器，换设备就丢；小程序用微信身份，点进来就是同一个人。web-view 里不能直接 wx.login，需要后端做一次性 ticket 桥。", "用户是谁：")
bullet("纯 web-view 容易被判“无实质内容/类目不符”。要加原生首页、规则、排行榜、关于页，web-view 只承载玩法，并按工具/教育类目申报。", "审核风险：")

# 4 timeline table
head("四、时间与成本")
headers2 = ["项目", "A. H5 + 换服务器", "B. web-view 小程序"]
rows2 = [
    ["服务器迁移", "1～2 天", "1～2 天（同样要做）"],
    ["域名 / HTTPS", "有域名 1～3 天；新备案 7～20 个工作日", "同左"],
    ["小程序注册 / 认证", "—", "1～3 个工作日"],
    ["小程序备案", "—", "1～22 个工作日"],
    ["开发", "0", "壳 + 登录桥 3～5 天"],
    ["审核", "—", "1～7 天"],
    ["总计", "约 1 周（域名现成）", "约 3～5 周"],
    ["额外费用", "服务器 + 域名", "小程序认证约 300 元/年"],
]
make_table(headers2, rows2, [4.2, 6.4, 6.0])

# 5 recommendation
head("五、推荐路线")
para("第一步（本周）：把 H5 迁到导师服务器，配域名和 HTTPS，按活动规模压测。", 10.5, True)
para("第二步（并行评估）：满足“学校非个人主体 + 已备案域名 + 活动在 3～5 周后”三条，再启动 B 方案；否则先不启动。", 10.5)
para("第三步（文章发布）：有公众号且已关联小程序，文章插小程序卡片；没有就先用“阅读原文”/二维码放 H5。", 10.5)

# 6 decision box
head("六、请导师拍板的 4 件事")
bullet("两周内、一个月后，还是本学期内？", "活动时间：")
bullet("必须正文一键进入，还是“阅读原文”/二维码也能接受？", "入口要求：")
bullet("能否提供非个人主体、认证材料、公众号、备案域名？", "主体与资料：")
bullet("预计多少人同时在线？服务器用现有 2C2G，还是换 4C8G/8C16G？", "规模与预算：")

p = doc.add_paragraph()
p.paragraph_format.space_before = Pt(12)
r = p.add_run("一句话：换服务器是必做的，小程序是加分项，不是替代项。")
set_font(r, 10.5, True, CLR_ACCENT)

# Footer
footer = sec.footer.paragraphs[0]
footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = footer.add_run("24 点项目 · 小程序 vs H5 方案对比 · 2026-11-05")
set_font(r, 8, False, CLR_MUTED)

doc.save(OUT)
print(OUT)
