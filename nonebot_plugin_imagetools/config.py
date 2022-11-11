from pydantic import BaseModel, Extra
from typing import List

from nonebot import get_driver

class Config(BaseModel, extra=Extra.ignore):
    nickname: List[str] = ["Bot"]
    max_messages_num: int = 99
    imagetools_upload_file: bool = False

imagetools_config = Config.parse_obj(get_driver().config.dict())