import re
from typing import List
from PIL.Image import Image as IMG
from PIL.ImageColor import colormap
from PIL import Image, ImageFilter, ImageOps

from nonebot_plugin_imageutils import BuildImage, text2image
from nonebot.adapters.onebot.v11 import Message, MessageSegment

from .utils import save_gif
from .depends import Arg, Img, NoArg

colors = "|".join(colormap.keys())
color_pattern = rf"#[a-fA-F0-9]{{6}}|{colors}"


def flip_horizontal(img: BuildImage = Img(), arg=NoArg()):
    return img.transpose(Image.FLIP_LEFT_RIGHT).save_jpg()


def flip_vertical(img: BuildImage = Img(), arg=NoArg()):
    return img.transpose(Image.FLIP_TOP_BOTTOM).save_jpg()


def grey(img: BuildImage = Img(), arg=NoArg()):
    return img.convert("L").save_jpg()


def rotate(img: BuildImage = Img(), arg: str = Arg()):
    angle = None
    if not arg:
        angle = 90
    elif arg.isdigit():
        angle = int(arg)
    if angle:
        return img.rotate(angle, expand=True).save_jpg()


def resize(img: BuildImage = Img(), arg: str = Arg()):
    w, h = img.size
    match1 = re.fullmatch(r"(\d{1,4})?[*xX, ](\d{1,4})?", arg)
    match2 = re.fullmatch(r"(\d{1,3})%", arg)
    if match1:
        w = match1.group(1)
        h = match1.group(2)
        if not w and h:
            return img.resize_height(int(h)).save_jpg()
        elif w and not h:
            return img.resize_width(int(w)).save_jpg()
        elif w and h:
            return img.resize((int(w), int(h))).save_jpg()
    elif match2:
        ratio = int(match2.group(1)) / 100
        return img.resize((int(w * ratio), int(h * ratio))).save_jpg()
    return "请使用正确的尺寸格式，如：100x100、100x、50%"


def crop(img: BuildImage = Img(), arg: str = Arg()):
    w, h = img.size
    match1 = re.fullmatch(r"(\d{1,4})[*xX, ](\d{1,4})", arg)
    match2 = re.fullmatch(r"(\d{1,2})[:：比](\d{1,2})", arg)
    if match1:
        w = int(match1.group(1))
        h = int(match1.group(2))
        return img.resize_canvas((w, h), bg_color="white").save_jpg()
    elif match2:
        wp = int(match2.group(1))
        hp = int(match2.group(2))
        size = min(w / wp, h / hp)
        return img.resize_canvas((int(wp * size), int(hp * size))).save_jpg()
    return "请使用正确的裁剪格式，如：100x100、2:1"


def invert(img: BuildImage = Img(), arg=NoArg()):
    return BuildImage(ImageOps.invert(img.convert("RGB").image)).save_jpg()


def contour(img: BuildImage = Img(), arg=NoArg()):
    return img.filter(ImageFilter.CONTOUR).save_jpg()  # type: ignore


def emboss(img: BuildImage = Img(), arg=NoArg()):
    return img.filter(ImageFilter.EMBOSS).save_jpg()  # type: ignore


def blur(img: BuildImage = Img(), arg=NoArg()):
    return img.filter(ImageFilter.BLUR).save_jpg()  # type: ignore


def sharpen(img: BuildImage = Img(), arg=NoArg()):
    return img.filter(ImageFilter.SHARPEN).save_jpg()  # type: ignore


def pixelate(img: BuildImage = Img(), arg: str = Arg()):
    num = None
    if not arg:
        num = 8
    elif arg.isdigit():
        num = int(arg)
    if num:
        image = img.image
        image = image.resize((img.width // num, img.height // num), resample=0)
        image = image.resize(img.size, resample=0)
        return BuildImage(image).save_jpg()


def color_mask(img: BuildImage = Img(), arg: str = Arg()):
    if re.fullmatch(color_pattern, arg):
        return img.color_mask(arg).save_jpg()
    else:
        return "请使用正确的颜色格式，如：#66ccff、red"


def color_image(arg: str = Arg()):
    if re.fullmatch(color_pattern, arg):
        return BuildImage.new("RGB", (500, 500), arg).save_jpg()
    else:
        return "请使用正确的颜色格式，如：#66ccff、red"


def gif_reverse(img: BuildImage = Img(), arg=NoArg()):
    image = img.image
    if getattr(image, "is_animated", False):
        duration = image.info["duration"] / 1000
        frames: List[IMG] = []
        for i in range(image.n_frames):
            image.seek(i)
            frames.append(image.convert("RGB"))
        frames.reverse()
        return save_gif(frames, duration)


def gif_split(img: BuildImage = Img(), arg=NoArg()):
    image = img.image
    msg = Message()
    if getattr(image, "is_animated", False):
        for i in range(image.n_frames):
            image.seek(i)
            msg += MessageSegment.image(BuildImage(image.convert("RGB")).save_jpg())
    return msg


def nine_grid(img: BuildImage = Img(), arg=NoArg()):
    img = img.square()
    w = img.width
    l = img.width // 3
    boxes = [
        (0, 0, l, l),
        (l, 0, l * 2, l),
        (l * 2, 0, w, l),
        (0, l, l, l * 2),
        (l, l, l * 2, l * 2),
        (l * 2, l, w, l * 2),
        (0, l * 2, l, w),
        (l, l * 2, l * 2, w),
        (l * 2, l * 2, w, w),
    ]
    msg = Message()
    for box in boxes:
        msg += MessageSegment.image(img.crop(box).save_jpg())
    return msg


def t2p(arg: str = Arg()):
    return BuildImage(text2image(arg, padding=(20, 20), max_width=1000)).save_png()
