import shlex
from io import BytesIO
from typing import List
from typing_extensions import Literal
from nonebot.params import CommandArg, Depends
from nonebot.adapters.onebot.v11 import Message, MessageEvent, unescape

from nonebot_plugin_imageutils import BuildImage

from .utils import download_url


def Imgs():
    async def dependency(event: MessageEvent, msg: Message = CommandArg()):
        img_segs = msg["image"]
        if event.reply:
            img_segs = event.reply.message["image"].extend(img_segs)
        return [
            BuildImage.open(BytesIO(await download_url(msg_seg.data["url"])))
            for msg_seg in img_segs
        ]

    return Depends(dependency)


def Img():
    async def dependency(imgs: List[BuildImage] = Imgs()):
        if len(imgs) == 1:
            return imgs[0]

    return Depends(dependency)


def Arg():
    async def dependency(msg: Message = CommandArg()):
        return unescape(msg.extract_plain_text().strip())

    return Depends(dependency)


def Args():
    async def dependency(arg: str = Arg()):
        try:
            args = shlex.split(arg)
        except:
            args = arg.split()
        args = [a for a in args if a]
        return args

    return Depends(dependency)


def NoArg():
    async def dependency(arg: Literal[""] = Arg()):
        return

    return Depends(dependency)
