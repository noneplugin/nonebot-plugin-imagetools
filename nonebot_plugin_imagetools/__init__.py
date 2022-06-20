from io import BytesIO
from typing import Union

from nonebot.params import Depends
from nonebot.matcher import Matcher
from nonebot.typing import T_Handler
from nonebot import on_command, require
from nonebot.plugin import PluginMetadata
from nonebot.adapters.onebot.v11 import Message, MessageSegment

require("nonebot_plugin_imageutils")

from .utils import Command
from .data_source import commands

__plugin_meta__ = PluginMetadata(
    name="图片操作",
    description="简单图片操作",
    usage="支持的指令：\n" + "、".join([cmd.keywords[0] for cmd in commands]),
    extra={
        "unique_name": "imagetools",
        "example": "旋转 [图片]",
        "author": "meetwq <meetwq@gmail.com>",
        "version": "0.1.1",
    },
)


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
