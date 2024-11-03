from dataclasses import dataclass
from typing import Callable

from nonebot_plugin_alconna import Args, Image, MultiVar

from .functions import (
    blur,
    color_image,
    color_mask,
    contour,
    crop,
    emboss,
    flip_horizontal,
    flip_vertical,
    four_grid,
    gif_change_fps,
    gif_join,
    gif_obverse_reverse,
    gif_reverse,
    gif_split,
    gradient_image,
    grey,
    horizontal_join,
    invert,
    nine_grid,
    pixelate,
    resize,
    rotate,
    sharpen,
    t2p,
    vertical_join,
)

arg_text = Args["arg", str]
arg_texts = Args["args", MultiVar(str, "+")]
arg_image = Args["img", Image]
arg_images = Args["imgs", MultiVar(Image, "+")]
arg_num_image = Args["num?", int, 0]["img", Image]
arg_num_images = Args["num?", int, 0]["imgs", MultiVar(Image, "+")]
arg_text_image = Args["arg", str]["img", Image]


@dataclass
class Command:
    keywords: tuple[str, ...]
    args: Args
    func: Callable


commands = [
    Command(("水平翻转", "左翻", "右翻"), arg_image, flip_horizontal),
    Command(("竖直翻转", "上翻", "下翻"), arg_image, flip_vertical),
    Command(("灰度图", "黑白"), arg_image, grey),
    Command(("旋转",), arg_num_image, rotate),
    Command(("缩放",), arg_text_image, resize),
    Command(("裁剪",), arg_text_image, crop),
    Command(("反相", "反色"), arg_image, invert),
    Command(("轮廓",), arg_image, contour),
    Command(("浮雕",), arg_image, emboss),
    Command(("模糊",), arg_image, blur),
    Command(("锐化",), arg_image, sharpen),
    Command(("像素化",), arg_num_image, pixelate),
    Command(("颜色滤镜",), arg_text_image, color_mask),
    Command(("纯色图",), arg_text, color_image),
    Command(("渐变图",), arg_texts, gradient_image),
    Command(("gif倒放", "倒放"), arg_image, gif_reverse),
    Command(("gif正放倒放", "正放倒放"), arg_image, gif_obverse_reverse),
    Command(("gif变速",), arg_text_image, gif_change_fps),
    Command(("gif分解",), arg_image, gif_split),
    Command(("gif合成",), arg_num_images, gif_join),
    Command(("四宫格",), arg_image, four_grid),
    Command(("九宫格",), arg_image, nine_grid),
    Command(("横向拼接",), arg_images, horizontal_join),
    Command(("纵向拼接",), arg_images, vertical_join),
    Command(("文字转图",), arg_text, t2p),
]
