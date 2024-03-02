import imghdr
import math
from datetime import datetime
from io import BytesIO
from typing import List, Union
from zipfile import ZIP_BZIP2, ZipFile

from nonebot import on_command, require
from nonebot.matcher import Matcher
from nonebot.params import Depends
from nonebot.plugin import PluginMetadata, inherit_supported_adapters
from nonebot.typing import T_Handler
from nonebot.utils import run_sync
from PIL.Image import Image as IMG
from pil_utils import BuildImage, Text2Image

require("nonebot_plugin_alconna")

from nonebot_plugin_alconna import Image, UniMessage

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
        matcher: Matcher,
        res: Union[str, BytesIO, List[BytesIO]] = Depends(command.func),
    ):
        if isinstance(res, str):
            await matcher.finish(res)
        elif isinstance(res, BytesIO):
            await UniMessage.image(raw=res).send()
        else:
            if len(res) > imagetools_config.imagetools_zip_threshold:
                zip_file = zip_images(res)
                time_str = datetime.now().strftime("%Y-%m-%d_%H%M%S")
                filename = f"{command.keywords[0]}_{time_str}.zip"
                await UniMessage.file(
                    raw=zip_file.getvalue(), name=filename, mimetype="application/zip"
                ).send()
            else:
                await UniMessage(Image(raw=img) for img in res).send()

    return handle


def create_matchers():
    for command in commands:
        matcher = on_command(
            command.keywords[0], aliases=set(command.keywords), block=True, priority=12
        )
        matcher.append_handler(handler(command))


create_matchers()


def zip_images(files: List[BytesIO]):
    output = BytesIO()
    with ZipFile(output, "w", ZIP_BZIP2) as zip_file:
        for i, file in enumerate(files):
            file_bytes = file.getvalue()
            ext = imghdr.what(None, h=file_bytes)
            zip_file.writestr(f"{i}.{ext}", file_bytes)
    return output
