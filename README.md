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


### 配置项

#### `imagetools_zip_threshold`
 - 类型：`int`
 - 默认：`20`
 - 说明：输出图片数量大于该数目时，打包为zip文件并上传

#### `imagetools_max_forward_msg_num`
 - 类型：`int`
 - 默认：`99`
 - 说明：输出图片数量小于该数目时，发送合并转发消息


> [!NOTE]
>
> 本插件使用 [nonebot-plugin-saa](https://github.com/felinae98/nonebot-plugin-send-anything-anywhere) 插件来发送图片和合并转发消息，具体支持的平台和行为请参考该插件的文档
>
> 本插件使用 [nonebot-plugin-alconna](https://github.com/nonebot/plugin-alconna) 插件来发送文件，具体支持的平台和行为请参考该插件的文档


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
 - 文字转图 + 文字，支持少量BBcode
