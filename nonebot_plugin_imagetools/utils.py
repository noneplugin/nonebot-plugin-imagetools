import httpx
import asyncio
import imageio
from io import BytesIO
from dataclasses import dataclass
from PIL.Image import Image as IMG
from typing import Callable, List, Protocol, Tuple

from nonebot.log import logger
from nonebot_plugin_imageutils import BuildImage


@dataclass
class Command:
    keywords: Tuple[str, ...]
    func: Callable


def save_gif(frames: List[IMG], duration: float) -> BytesIO:
    output = BytesIO()
    imageio.mimsave(output, frames, format="gif", duration=duration)
    return output


async def download_url(url: str) -> bytes:
    async with httpx.AsyncClient() as client:
        for i in range(3):
            try:
                resp = await client.get(url, timeout=20)
                resp.raise_for_status()
                return resp.content
            except Exception as e:
                logger.warning(f"Error downloading {url}, retry {i}/3: {e}")
                await asyncio.sleep(3)
    raise Exception(f"{url} 下载失败！")


class Maker(Protocol):
    def __call__(self, img: BuildImage) -> BuildImage:
        ...


def get_avg_duration(image: IMG) -> float:
    if not getattr(image, "is_animated", False):
        return 0
    total_duration = 0
    for i in range(image.n_frames):
        image.seek(i)
        total_duration += image.info["duration"]
    return total_duration / image.n_frames


def make_jpg_or_gif(img: BuildImage, func: Maker) -> BytesIO:
    """
    制作静图或者动图
    :params
      * ``img``: 输入图片，如头像
      * ``func``: 图片处理函数，输入img，返回处理后的图片
    """
    image = img.image
    if not getattr(image, "is_animated", False):
        return func(img.convert("RGBA")).save_jpg()
    else:
        duration = get_avg_duration(image) / 1000
        frames: List[IMG] = []
        for i in range(image.n_frames):
            image.seek(i)
            frames.append(func(BuildImage(image).convert("RGBA")).image)
        return save_gif(frames, duration)
