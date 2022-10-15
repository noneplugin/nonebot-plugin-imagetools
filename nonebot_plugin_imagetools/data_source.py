from .utils import Command
from .functions import *

commands = [
    Command(("水平翻转", "左翻", "右翻"), flip_horizontal),
    Command(("竖直翻转", "上翻", "下翻"), flip_vertical),
    Command(("旋转",), rotate),
    Command(("缩放",), resize),
    Command(("裁剪",), crop),
    Command(("反相", "反色"), invert),
    Command(("轮廓",), contour),
    Command(("浮雕",), emboss),
    Command(("模糊",), blur),
    Command(("锐化",), sharpen),
    Command(("像素化",), pixelate),
    Command(("颜色滤镜",), color_mask),
    Command(("纯色图",), color_image),
    Command(("gif倒放", "倒放"), gif_reverse),
    Command(("gif分解",), gif_split),
    Command(("四宫格",), four_grid),
    Command(("九宫格",), nine_grid),
    Command(("文字转图",), t2p),
]
