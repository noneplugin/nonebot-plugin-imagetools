from nonebot import get_plugin_config
from pydantic import BaseModel


class MultipleImageConfig(BaseModel):
    send_one_by_one: bool = False
    """
    是否逐个发送图片，默认为 `False`，即一次性发送所有图片
    """
    direct_send_threshold: int = 10
    """
    输出图片数量大于该数目时，不再直接发送，视配置以文件或合并转发消息的形式发送
    """
    send_zip_file: bool = True
    """
    输出图片数量大于 `direct_send_threshold` 时，是否打包为zip以文件形式发送
    """
    send_forward_msg: bool = False
    """
    输出图片数量大于 `direct_send_threshold` 时，是否发送合并转发消息
    """


class Config(BaseModel):
    imagetools_gif_max_size: float = 10
    imagetools_gif_max_frames: int = 100
    imagetools_multiple_image_config: MultipleImageConfig = MultipleImageConfig()


imagetools_config = get_plugin_config(Config)
