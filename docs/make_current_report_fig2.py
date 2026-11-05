
from PIL import Image, ImageDraw, ImageFont
import math

W, H = 1800, 900
BG = "#F7F9FC"; NAVY = "#0F3D5C"; TEAL = "#1E7A55"; GREY = "#5A6670"; LINE = "#C9D8E3"
CARD = "#FFFFFF"; SOFT = "#EAF1F6"; WARN = "#B7791F"

B = "C:/Windows/Fonts/msyhbd.ttc"; R = "C:/Windows/Fonts/msyh.ttc"
def f(s, b=False): return ImageFont.truetype(B if b else R, s)
img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img)

def rr(x1,y1,x2,y2,r=20,fill=CARD,outline=LINE,w=2):
    d.rounded_rectangle([x1,y1,x2,y2], radius=r, fill=fill, outline=outline, width=w)
def text(x,y,s,size=22,bold=False,color=NAVY,anchor="la"):
    d.text((x,y), s, font=f(size,bold), fill=color, anchor=anchor)
def arrow(x1,y1,x2,y2,color=NAVY,w=4):
    d.line([x1,y1,x2,y2], fill=color, width=w)
    a = math.atan2(y2-y1,x2-x1); L=16
    for s in (-0.5,0.5):
        d.line([x2,y2,x2-L*math.cos(a+s),y2-L*math.sin(a+s)], fill=color, width=w)

rr(80, 200, 800, 660, 24, CARD, NAVY, 3)
d.rectangle([80, 200, 96, 660], fill=TEAL)
text(120, 228, "RUNNING  对局进行中", 30, True, NAVY)
text(120, 270, "建局时固定牌序；A 模式写入 deadline", 21, False, GREY)
items = [
    ("正确答案", "correct + 1，记下该题计榜用时，开下一题"),
    ("错误答案", "wrong + 1，罚时 5 秒，本题关闭，开下一题"),
    ("主动跳题", "skipped + 1，罚时 10 秒，本题关闭，开下一题"),
    ("题池耗尽", "重新洗牌题池，计数与计时不清零"),
    ("断线 / 刷新", "服务端计时继续；后端可按 gameId 读取原局"),
]
y = 310
for k, v in items:
    d.ellipse([122, y+7, 132, y+17], fill=TEAL)
    text(148, y, k, 21, True, NAVY)
    text(330, y, v, 20, False, GREY)
    y += 58
text(120, 615, "每次写操作：行锁 + revision 校验 + actionId 幂等", 20, False, TEAL)

rr(1000, 170, 1700, 430, 24, CARD, TEAL, 3)
d.rectangle([1000, 170, 1016, 430], fill=TEAL)
text(1040, 198, "FINISHED  正常结束", 30, True, NAVY)
lines = [
    "A 模式：倒计时归零（含罚时耗尽）；答对 ≥ 1 题才上榜",
    "B 模式：答对第 10 题即结束，取实际用时 + 罚时",
    "写入 game_results（一局仅一条），再按规则更新 personal_bests",
    "四个榜（A/B × L1/L2）直接读取 personal_bests",
]
y = 248
for s in lines:
    d.ellipse([1042, y+7, 1052, y+17], fill=TEAL)
    text(1068, y, s, 20, False, GREY)
    y += 42

rr(1000, 520, 1700, 680, 24, CARD, WARN, 2)
text(1040, 548, "ABANDONED  主动退出", 27, True, NAVY)
text(1040, 592, "二次确认后结束；不写 game_results、不建档、不上榜", 20, False, GREY)
text(1040, 632, "现状：B 局若关闭页面不再回来，可能长期停在 RUNNING", 19, False, WARN)

arrow(800, 360, 1000, 300, TEAL, 4)
text(885, 282, "A 到时 / B 满 10", 20, False, TEAL, "mm")
arrow(800, 540, 1000, 580, WARN, 3)
text(885, 505, "玩家退出", 20, False, WARN, "mm")

rr(1000, 720, 1700, 810, 18, SOFT, LINE, 2)
text(1030, 742, "结算链路", 20, True, NAVY)
text(1170, 743, "game_results → personal_bests → /api/leaderboard", 20, False, GREY)

text(80, 730, "games：RUNNING / FINISHED / ABANDONED", 21, True, NAVY)
text(80, 770, "game_puzzles：OPEN / SOLVED / WRONG / SKIPPED", 21, True, NAVY)
text(80, 815, "说明：A 模式零题仍写历史，但不建最佳；被判无效的退出局不产生成绩。", 19, False, GREY)

img = img.crop((40, 120, 1740, 860))
img.save(r"D:\24game\docs\report_fig2_lifecycle.png")
print("saved", img.size)
