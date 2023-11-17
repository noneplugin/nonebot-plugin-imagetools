import shlex
import traceback
from io import BytesIO
from typing import List

from nonebot.adapters import Bot, Event, Message
from nonebot.log import logger
from nonebot.params import CommandArg, Depends
from nonebot.typing import T_State
from nonebot_plugin_alconna import Image, Reply, UniMessage, image_fetch
from pil_utils import BuildImage
from typing_extensions import Literal


def Imgs():
    async def dependency(
        bot: Bot, event: Event, state: T_State, arg: Message = CommandArg()
    ):
        imgs: List[bytes] = []

        msg = await UniMessage.generate(message=arg, event=event, bot=bot)
        msg_with_reply = UniMessage()
        for seg in msg:
            if isinstance(seg, Reply):
                if isinstance(seg.msg, Message):
                    msg_with_reply.extend(seg.msg)
            else:
                msg_with_reply.append(seg)

        for seg in msg_with_reply:
            if isinstance(seg, Image):
                try:
                    result = await image_fetch(
                        bot=bot, event=event, state=state, img=seg
                    )
                    if isinstance(result, bytes):
                        imgs.append(result)
                except:
                    logger.warning(f"Fail to fetch image: {traceback.format_exc()}")

        return [BuildImage.open(BytesIO(img)) for img in imgs]

    return Depends(dependency)


def Img():
    async def dependency(imgs: List[BuildImage] = Imgs()):
        if len(imgs) == 1:
            return imgs[0]

    return Depends(dependency)


def Arg():
    async def dependency(arg: Message = CommandArg()):
        return arg.extract_plain_text().strip()

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
