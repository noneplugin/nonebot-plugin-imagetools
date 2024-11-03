from io import BytesIO
from typing import Callable

from PIL.Image import Image as IMG
from pil_utils import BuildImage


def save_gif(frames: list[IMG], duration: float) -> BytesIO:
    output = BytesIO()
    frames[0].save(
        output,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=duration * 1000,
        loop=0,
        disposal=2,
        optimize=False,
    )
    return output


Maker = Callable[[BuildImage], BuildImage]


def get_avg_duration(image: IMG) -> float:
    if not getattr(image, "is_animated", False):
        return 0
    total_duration = 0
    n_frames = getattr(image, "n_frames", 1)
    for i in range(n_frames):
        image.seek(i)
        total_duration += image.info.get("duration", 20)
    return total_duration / n_frames


def split_gif(image: IMG) -> list[IMG]:
    frames: list[IMG] = []
    n_frames = getattr(image, "n_frames", 1)
    for i in range(n_frames):
        image.seek(i)
        frame = image.copy()
        frames.append(frame)
    image.seek(0)
    if image.info.__contains__("transparency"):
        frames[0].info["transparency"] = image.info["transparency"]
    return frames


def make_jpg_or_gif(img: BuildImage, func: Maker) -> BytesIO:
    """
    制作静图或者动图
    :params
      * ``img``: 输入图片
      * ``func``: 图片处理函数，输入img，返回处理后的图片
    """
    image = img.image
    if not getattr(image, "is_animated", False):
        return func(img).save_jpg()
    else:
        frames = split_gif(image)
        duration = get_avg_duration(image) / 1000
        frames = [func(BuildImage(frame)).image for frame in frames]
        return save_gif(frames, duration)
