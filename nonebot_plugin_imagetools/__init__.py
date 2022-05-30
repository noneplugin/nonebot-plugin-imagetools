from io import BytesIO
from typing import Union

from nonebot.params import Depends
from nonebot.matcher import Matcher
from nonebot.typing import T_Handler
from nonebot import on_command, require
from nonebot.adapters.onebot.v11 import Message, MessageSegment

require("nonebot_plugin_imageutils")

from .utils import Command
from .data_source import commands


__help__plugin_name__ = "imagetools"
__des__ = "简单图片操作"
__cmd__ = "支持的指令：\n" + "、".join([cmd.keywords[0] for cmd in commands])
__example__ = """
旋转 [图片]
""".strip()
__usage__ = f"{__des__}\n\nUsage:\n{__cmd__}\n\nExamples:\n{__example__}"


def create_matchers():
    def handler(command: Command) -> T_Handler:
        async def handle(
            matcher: Matcher,
            res: Union[str, BytesIO, Message, MessageSegment] = Depends(command.func),
        ):
            if isinstance(res, BytesIO):
                await matcher.finish(MessageSegment.image(res))
            else:
                await matcher.finish(res)

        return handle

    for command in commands:
        on_command(
            command.keywords[0],
            aliases=set(command.keywords),
            block=True,
            priority=12,
        ).append_handler(handler(command))


create_matchers()
