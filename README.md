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


### 使用

**以下命令需要加[命令前缀](https://v2.nonebot.dev/docs/api/config#Config-command_start) (默认为`/`)，可自行设置为空**

操作名 + [图片] 或 回复图片

#### 支持的操作
 - 水平翻转/左翻/右翻
 - 竖直翻转/上翻/下翻
 - 旋转 + 角度
 - 缩放 + 尺寸或百分比，如：`缩放 100x100`；`缩放 200x`；`缩放 150%`
 - 裁剪 + 尺寸或比例，如：`裁剪 100x100`；`裁剪 2:1`
 - 反相/反色
 - 轮廓
 - 浮雕
 - 模糊
 - 锐化
 - 像素化 + 像素尺寸，默认为 8
 - 颜色滤镜 + 16进制颜色代码 或 颜色名称，如：`颜色滤镜 #66ccff`；`颜色滤镜 green`
 - 纯色图 + 16进制颜色代码 或 颜色名称
 - gif倒放/倒放
 - gif分解
 - 九宫格
 - 文字转图 + 文字，支持少量BBcode
