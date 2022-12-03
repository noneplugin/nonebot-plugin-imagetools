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

本插件使用了 [go-cqhttp](https://github.com/Mrs4s/go-cqhttp) 的 `send_group_forward_msg` 和 `send_private_forward_msg` 接口 来发送合并转发消息，使用了 `upload_group_file` 和 `upload_private_file` 接口 来上传文件

发送私聊合并转发消息需要使用 `v1.0.0-rc2` 版本以上的 go-cqhttp

上传私聊文件需要使用 `v1.0.0-rc3` 版本以上的 go-cqhttp


### 配置项

<details>
<summary>展开/收起</summary>

#### `imagetools_zip_threshold`
 - 类型：`int`
 - 默认：`20`
 - 说明：输出图片数量大于该数目时，打包为zip以文件形式发送

#### `max_forward_msg_num`
 - 类型：`int`
 - 默认：`99`
 - 说明：合并转发消息条数上限

</details>


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
 - gif合成 
 - 四宫格
 - 九宫格
 - 文字转图 + 文字，支持少量BBcode
