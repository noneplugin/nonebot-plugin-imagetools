from nonebot import get_plugin_config
from pydantic import BaseModel


class Config(BaseModel):
    imagetools_zip_threshold: int = 10
    """
    输出图片数量大于该数目时，打包为zip以文件形式发送
    """


imagetools_config = get_plugin_config(Config)
