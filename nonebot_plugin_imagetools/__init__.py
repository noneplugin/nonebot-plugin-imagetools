import math
import imghdr
import tempfile
from io import BytesIO
from itertools import chain
from datetime import datetime
from typing import List, Union
from PIL.Image import Image as IMG
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
from nonebot.log import logger

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
        "version": "0.1.7",
    },
)


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
                if len(res) > imagetools_config.imagetools_zip_threshold:
                    zip_file = zip_images(res)
                    filename = f"{command.keywords[0]}_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.zip"
                    try:
                        await upload_file(bot, event, zip_file, filename)
                    except:
                        logger.warning("上传文件失败")

                msgs: List[Message] = [
                    Message(MessageSegment.image(msg)) for msg in res
                ]
                max_forward_msg_num = imagetools_config.max_forward_msg_num
                # 超出最大转发消息条数时，改为一条消息包含多张图片
                if len(msgs) > max_forward_msg_num:
                    step = math.ceil(len(msgs) / max_forward_msg_num)
                    msgs = [
                        Message(chain.from_iterable(msgs[i : i + step]))
                        for i in range(0, len(msgs) - 1, step)
                    ]
                await send_forward_msg(bot, event, "imagetools", bot.self_id, msgs)

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
    msgs: List[Message],
):
    def to_json(msg):
        return {"type": "node", "data": {"name": name, "uin": uin, "content": msg}}

    messages = [to_json(msg) for msg in msgs]
    if isinstance(event, GroupMessageEvent):
        await bot.call_api(
            "send_group_forward_msg", group_id=event.group_id, messages=messages
        )
    else:
        await bot.call_api(
            "send_private_forward_msg", user_id=event.user_id, messages=messages
        )


def zip_images(files: List[BytesIO]):
    output = BytesIO()
    with ZipFile(output, "w", ZIP_BZIP2) as zip_file:
        for i, file in enumerate(files):
            file_bytes = file.getvalue()
            ext = imghdr.what(None, h=file_bytes)
            zip_file.writestr(f"{i}.{ext}", file_bytes)
    return output


async def upload_file(
    bot: Bot,
    event: MessageEvent,
    file: BytesIO,
    filename: str,
):
    with tempfile.NamedTemporaryFile("wb+") as f:
        f.write(file.getbuffer())
        if isinstance(event, GroupMessageEvent):
            await bot.call_api(
                "upload_group_file", group_id=event.group_id, file=f.name, name=filename
            )
        else:
            await bot.call_api(
                "upload_private_file", user_id=event.user_id, file=f.name, name=filename
            )
