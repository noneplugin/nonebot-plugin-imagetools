# nonebot-plugin-imagetools

[Nonebot2](https://github.com/nonebot/nonebot2) 插件，用于一些简单图片操作


### 安装

- 使用 nb-cli

```
nb plugin install nonebot_plugin_imagetools
```

- 使用 pip

```
pip install nonebot_plugin_imagetools
```

#### 配置驱动器​

插件需要“客户端型驱动器”（如 httpx）来下载图片等，驱动器安装和配置参考 [NoneBot 选择驱动器](https://nonebot.dev/docs/advanced/driver)

同时需要在 `.env.*` 配置文件中启用对应的驱动器，例如：

```
DRIVER=~fastapi+~httpx+~websockets
```


### 配置项

#### `imagetools_gif_max_size`
 - 类型：`float`
 - 默认：10
 - 说明：限制生成的 gif 文件大小，单位为 Mb

#### `imagetools_gif_max_frames`
 - 类型：`int`
 - 默认：100
 - 说明：限制生成的 gif 文件帧数

#### `imagetools_multiple_image_config`
 - 类型：[MultipleImageConfig](https://github.com/noneplugin/nonebot-plugin-imagetools/blob/main/nonebot_plugin_imagetools/config.py)
 - 说明：输出多张图片时的发送方式

`MultipleImageConfig` 中的具体配置项：

##### `send_one_by_one`
 - 类型：`bool`
 - 默认：`False`
 - 说明：是否逐个发送图片，默认为 `False`，即一次性发送所有图片

##### `direct_send_threshold`
 - 类型：`int`
 - 默认：`10`
 - 说明：输出图片数量大于该数目时，不再直接发送，视配置以文件或合并转发消息的形式发送

##### `send_zip_file`
 - 类型：`bool`
 - 默认：`True`
 - 说明：输出图片数量大于 `direct_send_threshold` 时，是否打包为zip以文件形式发送

##### `send_forward_msg`
 - 类型：`bool`
 - 默认：`False`
 - 说明：输出图片数量大于 `direct_send_threshold` 时，是否发送合并转发消息

配置示例：
```
imagetools_multiple_image_config='
{
  "send_one_by_one": false,
  "direct_send_threshold": 10,
  "send_zip_file": true,
  "send_forward_msg": true
}
'
```


> [!NOTE]
>
> 本插件使用 [nonebot-plugin-alconna](https://github.com/nonebot/plugin-alconna) 插件来发送图片和文件，具体支持的平台和行为请参考该插件的文档


### 使用

**以下命令需要加[命令前缀](https://v2.nonebot.dev/docs/api/config#Config-command_start) (默认为`/`)，可自行设置为空**

操作名 + [图片] 或 回复图片

发送“图片操作”可显示支持的指令列表


#### 支持的操作
 - 水平翻转/左翻/右翻
 - 竖直翻转/上翻/下翻
 - 旋转 + 角度
 - 缩放 + 尺寸或百分比，如：`缩放 100x100`；`缩放 200x`；`缩放 150%`
 - 裁剪 + 尺寸或比例，如：`裁剪 100x100`；`裁剪 2:1`
 - 反相/反色
 - 灰度图/黑白
 - 轮廓
 - 浮雕
 - 模糊
 - 锐化
 - 像素化 + 像素尺寸，默认为 8
 - 颜色滤镜 + 16进制颜色代码 或 颜色名称，如：`颜色滤镜 #66ccff`；`颜色滤镜 green`
 - 纯色图 + 16进制颜色代码 或 颜色名称
 - 渐变图 [+ 角度] + 颜色列表，如：`渐变图 红色 黄色`；`渐变图 45 红色 黄色`
 - gif倒放/倒放
 - gif正放倒放/正放倒放
 - gif变速 + 倍率，如：`gif变速 0.5x`；`gif变速 50%`
 - gif分解 [+ 间隔时间] + 至少两张图片，间隔时间默认为`100`，单位为`ms`
 - gif合成 + 至少两张图片
 - 四宫格
 - 九宫格
 - 横向拼接 + 至少两张图片
 - 纵向拼接 + 至少两张图片
 - 文字转图 + 文字，支持少量BBcode，详见 [pil-utils](https://github.com/MeetWq/pil-utils)
