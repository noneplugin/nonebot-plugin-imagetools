import imghdr
import math
import tempfile
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import List, Union
from zipfile import ZIP_BZIP2, ZipFile

from nonebot import on_command, require
from nonebot.adapters import Bot, Event
from nonebot.matcher import Matcher
from nonebot.params import Depends
from nonebot.plugin import PluginMetadata, inherit_supported_adapters
from nonebot.typing import T_Handler
from nonebot.utils import run_sync
from PIL.Image import Image as IMG
from pil_utils import BuildImage, Text2Image

require("nonebot_plugin_alconna")

from nonebot_plugin_alconna import CustomNode, Image, Reference, UniMessage

from .config import Config, imagetools_config
from .data_source import commands
from .utils import Command

__plugin_meta__ = PluginMetadata(
    name="图片操作",
    description="简单图片操作",
    usage="发送“图片操作”查看支持的指令",
    type="application",
    homepage="https://github.com/noneplugin/nonebot-plugin-imagetools",
    config=Config,
    supported_adapters=inherit_supported_adapters("nonebot_plugin_alconna"),
    extra={
        "example": "旋转 [图片]",
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
    w = max(sum(img.width for img in imgs), head.width)
    h = head.height + max(img.height for img in imgs)
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
    await UniMessage.image(raw=img).send()


def handler(command: Command) -> T_Handler:
    async def handle(
        bot: Bot,
        event: Event,
        matcher: Matcher,
        res: Union[str, BytesIO, List[BytesIO]] = Depends(command.func),
    ):
        if isinstance(res, str):
            await matcher.finish(res)
        elif isinstance(res, BytesIO):
            await UniMessage.image(raw=res).send()
        else:
            await send_multiple_images(bot, event, command, res)

    return handle


def create_matchers():
    for command in commands:
        matcher = on_command(
            command.keywords[0], aliases=set(command.keywords), block=True, priority=12
        )
        matcher.append_handler(handler(command))


create_matchers()


async def send_multiple_images(
    bot: Bot, event: Event, command: Command, images: List[BytesIO]
):
    config = imagetools_config.imagetools_multiple_image_config

    if len(images) <= config.direct_send_threshold:
        if config.send_one_by_one:
            for img in images:
                await UniMessage.image(raw=img).send()
        else:
            await UniMessage(Image(raw=img) for img in images).send()

    else:
        if config.send_zip_file:
            zip_file = zip_images(images)
            time_str = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            filename = f"{command.keywords[0]}_{time_str}.zip"
            await send_file(bot, event, filename, zip_file.getvalue())

        if config.send_forward_msg:
            await send_forward_msg(bot, event, images)


def zip_images(files: List[BytesIO]):
    output = BytesIO()
    with ZipFile(output, "w", ZIP_BZIP2) as zip_file:
        for i, file in enumerate(files):
            file_bytes = file.getvalue()
            ext = imghdr.what(None, h=file_bytes)
            zip_file.writestr(f"{i}.{ext}", file_bytes)
    return output


async def send_file(bot: Bot, event: Event, filename: str, content: bytes):
    try:
        from nonebot.adapters.onebot.v11 import Bot as V11Bot
        from nonebot.adapters.onebot.v11 import Event as V11Event
        from nonebot.adapters.onebot.v11 import GroupMessageEvent as V11GMEvent

        async def upload_file_v11(
            bot: V11Bot, event: V11Event, filename: str, content: bytes
        ):
            with tempfile.TemporaryDirectory() as temp_dir:
                with open(Path(temp_dir) / filename, "wb") as f:
                    f.write(content)
                if isinstance(event, V11GMEvent):
                    await bot.call_api(
                        "upload_group_file",
                        group_id=event.group_id,
                        file=f.name,
                        name=filename,
                    )
                else:
                    await bot.call_api(
                        "upload_private_file",
                        user_id=event.get_user_id(),
                        file=f.name,
                        name=filename,
                    )

        if isinstance(bot, V11Bot) and isinstance(event, V11Event):
            await upload_file_v11(bot, event, filename, content)
            return

    except ImportError:
        pass

    await UniMessage.file(raw=content, name=filename, mimetype="application/zip").send()


async def send_forward_msg(
    bot: Bot,
    event: Event,
    images: List[BytesIO],
):
    try:
        from nonebot.adapters.onebot.v11 import Bot as V11Bot
        from nonebot.adapters.onebot.v11 import Event as V11Event
        from nonebot.adapters.onebot.v11 import GroupMessageEvent as V11GMEvent
        from nonebot.adapters.onebot.v11 import Message as V11Msg
        from nonebot.adapters.onebot.v11 import MessageSegment as V11MsgSeg

        async def send_forward_msg_v11(
            bot: V11Bot,
            event: V11Event,
            name: str,
            uin: str,
            msgs: List[V11Msg],
        ):
            messages = [
                {"type": "node", "data": {"name": name, "uin": uin, "content": msg}}
                for msg in msgs
            ]
            if isinstance(event, V11GMEvent):
                await bot.call_api(
                    "send_group_forward_msg", group_id=event.group_id, messages=messages
                )
            else:
                await bot.call_api(
                    "send_private_forward_msg",
                    user_id=event.get_user_id(),
                    messages=messages,
                )

        if isinstance(bot, V11Bot) and isinstance(event, V11Event):
            await send_forward_msg_v11(
                bot,
                event,
                "imagetools",
                bot.self_id,
                [V11Msg(V11MsgSeg.image(img)) for img in images],
            )
            return

    except ImportError:
        pass

    uid = bot.self_id
    name = "imagetools"
    time = datetime.now()
    await UniMessage(
        Reference(
            content=[
                CustomNode(
                    uid, name, time, await UniMessage.image(raw=img.getvalue()).export()
                )
                for img in images
            ]
        )
    ).send()
