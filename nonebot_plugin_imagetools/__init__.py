import imghdr
import math
import tempfile
from datetime import datetime
from io import BytesIO
from pathlib import Path
from zipfile import ZIP_BZIP2, ZipFile

from nonebot import require
from nonebot.adapters import Bot, Event
from nonebot.matcher import Matcher
from nonebot.plugin import PluginMetadata, inherit_supported_adapters
from nonebot.typing import T_State
from nonebot.utils import run_sync
from PIL.Image import Image as IMG
from pil_utils import BuildImage, Text2Image

require("nonebot_plugin_alconna")

from nonebot_plugin_alconna import (
    AlcMatches,
    Alconna,
    CustomNode,
    Image,
    UniMessage,
    on_alconna,
)
from nonebot_plugin_alconna.builtins.extensions.reply import ReplyMergeExtension
from nonebot_plugin_alconna.uniseg.tools import image_fetch

from .command import Command, commands
from .config import Config, imagetools_config

__plugin_meta__ = PluginMetadata(
    name="图片操作",
    description="简单图片操作",
    usage="发送“图片操作”查看支持的指令",
    type="application",
    homepage="https://github.com/noneplugin/nonebot-plugin-imagetools",
    config=Config,
    supported_adapters=inherit_supported_adapters("nonebot_plugin_alconna"),
)


help_cmd = on_alconna(
    "图片操作", aliases={"图片工具"}, block=True, priority=13, use_cmd_start=True
)


@help_cmd.handle()
async def _():
    img = await run_sync(help_image)()
    await UniMessage.image(raw=img).send()


def help_image() -> BytesIO:
    head_text = "简单图片操作，支持的操作："
    head = Text2Image.from_text(head_text, 30, font_style="bold").to_image(
        padding=(20, 10)
    )
    col_imgs: list[IMG] = []
    col_num = 2
    num_per_col = math.ceil(len(commands) / col_num)
    for idx in range(0, len(commands), num_per_col):
        text_imgs: list[IMG] = []
        for i, command in enumerate(commands[idx : idx + num_per_col]):
            text = f"{idx + i + 1}. " + "/".join(command.keywords)
            text_img = Text2Image.from_text(text, 30).to_image()
            text_imgs.append(text_img)
        w = max(img.width for img in text_imgs) + 40
        h = sum(img.height for img in text_imgs) + 20
        col_img = BuildImage.new("RGBA", (w, h), "white")
        current_h = 10
        for img in text_imgs:
            col_img.paste(img, (20, current_h), alpha=True)
            current_h += img.height
        col_imgs.append(col_img.image)
    w = max(sum(img.width for img in col_imgs), head.width)
    h = head.height + max(img.height for img in col_imgs)
    frame = BuildImage.new("RGBA", (w, h), "white")
    frame.paste(head, alpha=True)
    current_w = 0
    for img in col_imgs:
        frame.paste(img, (current_w, head.height), alpha=True)
        current_w += img.width
    return frame.save_jpg()


def create_matcher(command: Command):
    command_matcher = on_alconna(
        Alconna(command.keywords[0], command.args),
        aliases=set(command.keywords[1:]),
        block=True,
        priority=13,
        use_cmd_start=True,
        extensions=[ReplyMergeExtension()],
    )

    @command_matcher.handle()
    async def _(
        bot: Bot,
        event: Event,
        state: T_State,
        matcher: Matcher,
        alc_matches: AlcMatches,
    ):
        async def fetch_image(image: Image):
            content = await image_fetch(event, bot, state, image)
            if content:
                return BuildImage.open(BytesIO(content))
            await matcher.finish("图片下载失败")

        args = alc_matches.all_matched_args
        if image := args.get("img"):
            args["img"] = await fetch_image(image)
        if images := args.get("imgs"):
            args["imgs"] = [await fetch_image(image) for image in images]

        result = await run_sync(command.func)(**args)

        if isinstance(result, str):
            await matcher.finish(result)
        elif isinstance(result, BytesIO):
            await UniMessage.image(raw=result).send()
        elif isinstance(result, list):
            await send_multiple_images(bot, event, command, result)
        else:
            await matcher.finish("出错了，请稍后再试")


def create_matchers():
    for command in commands:
        create_matcher(command)


create_matchers()


async def send_multiple_images(
    bot: Bot, event: Event, command: Command, images: list[BytesIO]
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


def zip_images(files: list[BytesIO]):
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
    images: list[BytesIO],
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
            msgs: list[V11Msg],
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
    await UniMessage.reference(
        *[
            CustomNode(uid, name, UniMessage.image(raw=img.getvalue()), time)
            for img in images
        ]
    ).send()
