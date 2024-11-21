import math
import re
from io import BytesIO
from typing import Optional

from PIL import ImageFilter, ImageOps
from PIL.Image import Transpose
from PIL.ImageColor import colormap
from pil_utils import BuildImage, Text2Image
from pil_utils.gradient import ColorStop, LinearGradient
from pil_utils.typing import ColorType

from .color_table import color_table
from .utils import Maker, get_avg_duration, make_png_or_gif, save_gif, split_gif

colors = "|".join(colormap.keys())
color_pattern_str = rf"#[a-fA-F0-9]{{6}}|{colors}"

num_256 = r"(25[0-5]|2[0-4][0-9]|[0-1]?[0-9]?[0-9])"
color_pattern_num = rf"(?:rgb)?\(?\s*{num_256}[\s,]+{num_256}[\s,]+{num_256}\s*\)?;?"


def flip_horizontal(img: BuildImage):
    return make_png_or_gif(
        [img], lambda imgs: imgs[0].transpose(Transpose.FLIP_LEFT_RIGHT)
    )


def flip_vertical(img: BuildImage):
    return make_png_or_gif(
        [img], lambda imgs: imgs[0].transpose(Transpose.FLIP_TOP_BOTTOM)
    )


def grey(img: BuildImage):
    return make_png_or_gif([img], lambda imgs: imgs[0].convert("L"))


def rotate(num: Optional[int], img: BuildImage):
    angle = num or 90
    return make_png_or_gif([img], lambda imgs: imgs[0].rotate(angle, expand=True))


def resize(arg: str, img: BuildImage):
    w, h = img.size
    match1 = re.fullmatch(r"(\d{1,4})?[*xX, ](\d{1,4})?", arg)
    match2 = re.fullmatch(r"(\d{1,3})%", arg)
    make: Optional[Maker] = None
    if match1:
        w = match1.group(1)
        h = match1.group(2)
        if not w and h:
            make = lambda imgs: imgs[0].resize_height(int(h))
        elif w and not h:
            make = lambda imgs: imgs[0].resize_width(int(w))
        elif w and h:
            make = lambda imgs: imgs[0].resize((int(w), int(h)))
    elif match2:
        ratio = int(match2.group(1)) / 100
        make = lambda imgs: imgs[0].resize((int(w * ratio), int(h * ratio)))
    if not make:
        return "请使用正确的尺寸格式，如：100x100、100x、50%"
    return make_png_or_gif([img], make)


def crop(arg: str, img: BuildImage):
    w, h = img.size
    match1 = re.fullmatch(r"(\d{1,4})[*xX, ](\d{1,4})", arg)
    match2 = re.fullmatch(r"(\d{1,2})[:：比](\d{1,2})", arg)
    make: Optional[Maker] = None
    if match1:
        w = int(match1.group(1))
        h = int(match1.group(2))
        make = lambda imgs: imgs[0].resize_canvas((w, h), bg_color="white")
    elif match2:
        wp = int(match2.group(1))
        hp = int(match2.group(2))
        size = min(w / wp, h / hp)
        make = lambda imgs: imgs[0].resize_canvas((int(wp * size), int(hp * size)))
    if not make:
        return "请使用正确的裁剪格式，如：100x100、2:1"
    return make_png_or_gif([img], make)


def invert(img: BuildImage):
    def make(imgs: list[BuildImage]) -> BuildImage:
        img = imgs[0]
        result = BuildImage.new("RGB", img.size, "white")
        result.paste(img, alpha=True)
        return BuildImage(ImageOps.invert(result.image))

    return make_png_or_gif([img], make)


def contour(img: BuildImage):
    return make_png_or_gif([img], lambda imgs: imgs[0].filter(ImageFilter.CONTOUR))


def emboss(img: BuildImage):
    return make_png_or_gif([img], lambda imgs: imgs[0].filter(ImageFilter.EMBOSS))


def blur(img: BuildImage):
    return make_png_or_gif([img], lambda imgs: imgs[0].filter(ImageFilter.BLUR))


def sharpen(img: BuildImage):
    return make_png_or_gif([img], lambda imgs: imgs[0].filter(ImageFilter.SHARPEN))


def pixelate(num: Optional[int], img: BuildImage):
    num = num or 8

    def make(imgs: list[BuildImage]) -> BuildImage:
        img = imgs[0]
        image = img.image
        image = image.resize((img.width // num, img.height // num), resample=0)
        image = image.resize(img.size, resample=0)
        return BuildImage(image)

    return make_png_or_gif([img], make)


def color_mask(arg: str, img: BuildImage):
    if re.fullmatch(color_pattern_str, arg):
        color = arg
    elif match := re.fullmatch(color_pattern_num, arg):
        color = tuple(map(int, match.groups()))
        assert len(color) == 3
    elif arg in color_table:
        color = color_table[arg]
    else:
        return "请使用正确的颜色格式，如：#66ccff、red、红色、102,204,255"
    return make_png_or_gif([img], lambda imgs: imgs[0].color_mask(color))


def color_image(arg: str):
    if re.fullmatch(color_pattern_str, arg):
        color = arg
    elif match := re.fullmatch(color_pattern_num, arg):
        color = tuple(map(int, match.groups()))
        assert len(color) == 3
    elif arg in color_table:
        color = color_table[arg]
    else:
        return "请使用正确的颜色格式，如：#66ccff、red、红色、102,204,255"
    return BuildImage.new("RGB", (500, 500), color).save_png()


def gradient_image(args: list[str]):
    if not args:
        return
    angle = 0
    if args[0] in ["上下", "竖直"]:
        angle = 90
        args = args[1:]
    elif args[0] in ["左右", "水平"]:
        angle = 0
        args = args[1:]
    elif args[0].isdigit():
        angle = int(args[0])
        args = args[1:]
    if not args:
        return

    colors: list[ColorType] = []
    for arg in args:
        if re.fullmatch(color_pattern_str, arg):
            color = arg
        elif match := re.fullmatch(color_pattern_num, arg):
            color = tuple(map(int, match.groups()))
            assert len(color) == 3
        elif arg in color_table:
            color = color_table[arg]
        else:
            return "请使用正确的颜色格式，如：#66ccff、red、红色、102,204,255"
        colors.append(color)

    img_w = 500
    img_h = 500
    angle *= math.pi / 180
    if math.sqrt(img_w**2 + img_h**2) * math.cos(angle) <= img_w:
        dy = img_h / 2
        dx = dy / math.tan(angle)
    else:
        dx = img_w / 2
        dy = dx * math.tan(angle)

    gradient = LinearGradient(
        (img_w / 2 - dx, img_h / 2 - dy, img_w / 2 + dx, img_h / 2 + dy),
        [ColorStop(i / (len(colors) - 1), color) for i, color in enumerate(colors)],
    )
    img = gradient.create_image((img_w, img_h))
    return BuildImage(img).save_png()


def gif_reverse(img: BuildImage):
    image = img.image
    if not getattr(image, "is_animated", False):
        return "请发送 gif 格式的图片"
    frames = split_gif(image)
    duration = get_avg_duration(image)
    return save_gif(frames[::-1], duration)


def gif_obverse_reverse(img: BuildImage):
    image = img.image
    if not getattr(image, "is_animated", False):
        return "请发送 gif 格式的图片"
    frames = split_gif(image)
    duration = get_avg_duration(image)
    frames = frames + frames[-2::-1]
    return save_gif(frames, duration)


def gif_change_fps(arg: str, img: BuildImage):
    image = img.image
    if not getattr(image, "is_animated", False):
        return "请发送 gif 格式的图片"
    duration = get_avg_duration(image)
    p_float = r"\d{0,3}\.?\d{1,3}"
    if match := re.fullmatch(rf"({p_float})(?:x|X|倍速?)", arg):
        duration /= float(match.group(1))
    elif match := re.fullmatch(rf"({p_float})%", arg):
        duration /= float(match.group(1)) / 100
    elif match := re.fullmatch(rf"({p_float})fps", arg, re.I):
        duration = 1 / float(match.group(1))
    elif match := re.fullmatch(rf"({p_float})(m?)s", arg, re.I):
        duration = (
            float(match.group(1)) / 1000 if match.group(2) else float(match.group(1))
        )
    else:
        return "请使用正确的倍率格式，如：0.5x、50%、20FPS、0.05s"
    if duration < 0.02:
        return (
            f"帧间隔必须 大于 0.02 s（小于等于 50 FPS），\n"
            f"超过该限制可能会导致 GIF 显示速度不正常。\n"
            f"当前帧间隔为 {duration:.3f} s ({1 / duration:.1f} FPS)"
        )
    frames = split_gif(image)
    return save_gif(frames, duration)


def gif_split(img: BuildImage):
    image = img.image
    if not getattr(image, "is_animated", False):
        return "请发送 gif 格式的图片"
    frames = split_gif(image)
    return [BuildImage(frame).save_png() for frame in frames]


def gif_join(num: Optional[int], imgs: list[BuildImage]):
    duration = num or 100
    if len(imgs) < 2:
        return "gif合成至少需要2张图片"

    max_w = max([img.width for img in imgs])
    max_h = max([img.height for img in imgs])
    frames = [img.resize_canvas((max_w, max_h)).image for img in imgs]
    return save_gif(frames, duration / 1000)


def four_grid(img: BuildImage):
    img = img.square()
    a = img.width // 2
    boxes = [
        (0, 0, a, a),
        (a, 0, a * 2, a),
        (0, a, a, a * 2),
        (a, a, a * 2, a * 2),
    ]
    output: list[BytesIO] = []
    for box in boxes:
        output.append(img.crop(box).save_png())
    return output


def nine_grid(img: BuildImage):
    img = img.square()
    w = img.width
    a = img.width // 3
    boxes = [
        (0, 0, a, a),
        (a, 0, a * 2, a),
        (a * 2, 0, w, a),
        (0, a, a, a * 2),
        (a, a, a * 2, a * 2),
        (a * 2, a, w, a * 2),
        (0, a * 2, a, w),
        (a, a * 2, a * 2, w),
        (a * 2, a * 2, w, w),
    ]
    output: list[BytesIO] = []
    for box in boxes:
        output.append(img.crop(box).save_png())
    return output


def horizontal_join(imgs: list[BuildImage]):
    if len(imgs) < 2:
        return "图片拼接至少需要2张图片"

    def make(imgs: list[BuildImage]) -> BuildImage:
        img_h = min([img.height for img in imgs])
        imgs = [img.resize((img.width * img_h // img.height, img_h)) for img in imgs]
        img_w = sum([img.width for img in imgs])
        frame = BuildImage.new("RGB", (img_w, img_h), "white")
        x = 0
        for img in imgs:
            frame.paste(img, (x, 0))
            x += img.width
        return frame

    return make_png_or_gif(imgs, make)


def vertical_join(imgs: list[BuildImage]):
    if len(imgs) < 2:
        return "图片拼接至少需要2张图片"

    def make(imgs: list[BuildImage]) -> BuildImage:
        img_w = min([img.width for img in imgs])
        imgs = [img.resize((img_w, img.height * img_w // img.width)) for img in imgs]
        img_h = sum([img.height for img in imgs])
        frame = BuildImage.new("RGB", (img_w, img_h), "white")
        y = 0
        for img in imgs:
            frame.paste(img, (0, y))
            y += img.height
        return frame

    return make_png_or_gif(imgs, make)


def t2p(arg: str):
    text2img = Text2Image.from_bbcode_text(arg, 30)
    max_width = min(math.ceil(text2img.longest_line), 1000)
    img = text2img.to_image(max_width, bg_color="white", padding=(20, 20))
    return BuildImage(img).save_png()
