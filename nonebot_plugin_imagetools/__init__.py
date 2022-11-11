import math
import asyncio
import random
import datetime
from io import BytesIO
from typing import List, Union
from PIL.Image import Image as IMG
from pathlib import Path
from zipfile import ZipFile, ZIP_BZIP2

from nonebot.params import Depends
from nonebot.utils import run_sync
from nonebot.matcher import Matcher
from nonebot.typing import T_Handler
from nonebot import on_command, require
from nonebot.plugin import PluginMetadata
from nonebot.adapters.onebot.v11 import (
    Message,
    MessageSegment,
    Bot,
    MessageEvent,
    GroupMessageEvent,
)

require("nonebot_plugin_imageutils")
from nonebot_plugin_imageutils import BuildImage, Text2Image

from .utils import Command
from .data_source import commands
from .config import imagetools_config

__plugin_meta__ = PluginMetadata(
    name="图片操作",
    description="简单图片操作",
    usage="支持的指令：\n" + "、".join([cmd.keywords[0] for cmd in commands]),
    extra={
        "unique_name": "imagetools",
        "example": "旋转 [图片]",
        "author": "meetwq <meetwq@gmail.com>",
        "version": "0.1.4",
    },
)

FORWARD_TYPE = List[Union[str, Message, MessageSegment]]


help_cmd = on_command("图片操作", aliases={"图片工具"}, block=True, priority=12)


@run_sync
def help_image() -> BytesIO:
    def cmd_text(commands: List[Command], start: int = 1) -> str:
        texts = []
        for i, meme in enumerate(commands):
            text = f"{i + start}. " + "/".join(meme.keywords)
            texts.append(text)
        return "\n".join(texts)

    head_text = "简单图片操作，支持的操作："
    head = Text2Image.from_text(head_text, 30, weight="bold").to_image(padding=(20, 10))

    imgs: List[IMG] = []
    col_num = 2
    num_per_col = math.ceil(len(commands) / col_num)
    for idx in range(0, len(commands), num_per_col):
        text = cmd_text(commands[idx : idx + num_per_col], start=idx + 1)
        imgs.append(Text2Image.from_text(text, 30).to_image(padding=(20, 10)))
    w = max(sum((img.width for img in imgs)), head.width)
    h = head.height + max((img.height for img in imgs))
    frame = BuildImage.new("RGBA", (w, h), "white")
    frame.paste(head, alpha=True)
    current_w = 0
    for img in imgs:
        frame.paste(img, (current_w, head.height), alpha=True)
        current_w += img.width
    return frame.save_jpg()


@help_cmd.handle()
async def _():
    img = await help_image()
    if img:
        await help_cmd.finish(MessageSegment.image(img))


def create_matchers():
    def handler(command: Command) -> T_Handler:
        async def handle(
            bot: Bot,
            event: MessageEvent,
            matcher: Matcher,
            res: Union[str, BytesIO, List[BytesIO]] = Depends(command.func),
        ):
            if isinstance(res, str):
                await matcher.finish(res)
            elif isinstance(res, BytesIO):
                await matcher.finish(MessageSegment.image(res))
            else:
                msgs: FORWARD_TYPE = [MessageSegment.image(msg) for msg in res]
                if len(msgs):
                    await send_forward_msg(bot, event, imagetools_config.nickname[0], bot.self_id, msgs)
                    if imagetools_config.imagetools_upload_file:
                        await bot.send(event=event, message="\n图片制作完成，正在发送压缩包，请稍等...", at_sender=True)
                        await upload_file(bot, event, command.keywords[0], res)
                else:
                    await matcher.finish("未生成任何内容", at_sender=True)

        return handle

    for command in commands:
        on_command(
            command.keywords[0],
            aliases=set(command.keywords),
            block=True,
            priority=12,
        ).append_handler(handler(command))


create_matchers()


async def send_forward_msg(
    bot: Bot,
    event: MessageEvent,
    name: str,
    uin: str,
    msgs: FORWARD_TYPE,
):
    def to_json(msg):
        return {"type": "node", "data": {"name": name, "uin": uin, "content": msg}}

    messages = [to_json(msg) for msg in msgs]
    MAX_MESSAGES_NUM = imagetools_config.max_messages_num
    while len(messages):
        if isinstance(event, GroupMessageEvent):
            await bot.send_group_forward_msg(group_id=event.group_id, messages=messages[:MAX_MESSAGES_NUM])
        else:
            await bot.send_private_forward_msg(user_id=event.user_id, messages=messages[:MAX_MESSAGES_NUM])
        messages = messages[MAX_MESSAGES_NUM:]
        await asyncio.sleep(random.randint(3,5))


async def upload_file(
    bot: Bot,
    event: MessageEvent,
    name: str,
    res: Union[str, BytesIO, List[BytesIO]],
    format: str = "png",
):
    filename = f"{name}{int(datetime.datetime.now().timestamp())}.zip"
    file_path = Path(__file__).with_name(filename)
    """
    这里手动指定了文件类型，因为目前类型就PNG
    PIL的文件类型判断非常不稳定，建议手动指定，就先不改了
    """
    with ZipFile(file_path, "w", ZIP_BZIP2) as myzip:
        for r in range(len(res)):
            zip_filename = f"{r}.{format}"
            myzip.writestr(zip_filename, res[r].getbuffer())
    if isinstance(event, GroupMessageEvent):
        await bot.upload_group_file(group_id=event.group_id,file=str(file_path),name=filename)
    else:
        await bot.upload_private_file(user_id=event.user_id,file=str(file_path),name=filename)
    file_path.unlink()
