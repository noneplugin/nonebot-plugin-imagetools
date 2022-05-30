import httpx
import asyncio
import imageio
from io import BytesIO
from dataclasses import dataclass
from PIL.Image import Image as IMG
from typing import Callable, List, Tuple

from nonebot.log import logger


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
