import math
from enum import Enum
from io import BytesIO
from typing import Callable

from PIL.Image import Image as IMG
from pil_utils import BuildImage

from .config import imagetools_config


def save_gif(frames: list[IMG], duration: float) -> BytesIO:
    output = BytesIO()
    frames[0].save(
        output,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=duration * 1000,
        loop=0,
        disposal=2,
        optimize=False,
    )

    # 没有超出最大大小，直接返回
    nbytes = output.getbuffer().nbytes
    if nbytes <= imagetools_config.imagetools_gif_max_size * 10**6:
        return output

    # 超出最大大小，帧数超出最大帧数时，缩减帧数
    n_frames = len(frames)
    gif_max_frames = imagetools_config.imagetools_gif_max_frames
    if n_frames > gif_max_frames:
        index = range(n_frames)
        ratio = n_frames / gif_max_frames
        index = (int(i * ratio) for i in range(gif_max_frames))
        new_duration = duration * ratio
        new_frames = [frames[i] for i in index]
        return save_gif(new_frames, new_duration)

    # 超出最大大小，帧数没有超出最大帧数时，缩小尺寸
    new_frames = [
        frame.resize((int(frame.width * 0.9), int(frame.height * 0.9)))
        for frame in frames
    ]
    return save_gif(new_frames, duration)


def get_avg_duration(image: IMG) -> float:
    if not getattr(image, "is_animated", False):
        return 0
    total_duration = 0
    n_frames = getattr(image, "n_frames", 1)
    for i in range(n_frames):
        image.seek(i)
        total_duration += image.info.get("duration", 20)
    return total_duration / n_frames / 1000


def split_gif(image: IMG) -> list[IMG]:
    frames: list[IMG] = []
    n_frames = getattr(image, "n_frames", 1)
    for i in range(n_frames):
        image.seek(i)
        frame = image.copy()
        frames.append(frame)
    image.seek(0)
    if image.info.__contains__("transparency"):
        frames[0].info["transparency"] = image.info["transparency"]
    return frames


class FrameAlignPolicy(Enum):
    """
    要叠加的gif长度大于基准gif时，是否延长基准gif长度以对齐两个gif
    """

    no_extend = 0
    """不延长"""
    extend_first = 1
    """延长第一帧"""
    extend_last = 2
    """延长最后一帧"""
    extend_loop = 3
    """以循环方式延长"""


def get_aligned_gif_indexes(
    gif_infos: list[tuple[int, float]],
    frame_num_target: int,
    duration_target: float,
    frame_align: FrameAlignPolicy = FrameAlignPolicy.no_extend,
) -> tuple[list[list[int]], list[int]]:
    """
    将gif按照目标帧数和帧间隔对齐
    :params
        * ``gif_infos``: 每个输入gif的帧数和帧间隔，帧间隔单位为秒
        * ``frame_num_target``: 目标gif的帧数
        * ``duration_target``: 目标gif的帧间隔，单位为秒
        * ``frame_align``: 要对齐的gif长度大于目标gif时，gif长度对齐方式
    :return
        * 输入gif的帧索引列表和目标gif的帧索引列表
    """

    frame_idxs_target: list[int] = list(range(frame_num_target))

    max_total_duration_input = max(
        frame_num * duration for frame_num, duration in gif_infos
    )
    total_duration_target = frame_num_target * duration_target
    if (
        diff_duration := max_total_duration_input - total_duration_target
    ) >= duration_target:
        diff_num = math.ceil(diff_duration / duration_target)

        if frame_align == FrameAlignPolicy.extend_first:
            frame_idxs_target = [0] * diff_num + frame_idxs_target

        elif frame_align == FrameAlignPolicy.extend_last:
            frame_idxs_target += [frame_num_target - 1] * diff_num

        elif frame_align == FrameAlignPolicy.extend_loop:
            frame_num_total = frame_num_target
            # 重复目标gif，直到每个gif总时长之差在1个间隔以内，或总帧数超出最大帧数
            while (
                frame_num_total + frame_num_target
                <= imagetools_config.imagetools_gif_max_frames
            ):
                frame_num_total += frame_num_target
                frame_idxs_target += list(range(frame_num_target))
                total_duration = frame_num_total * duration_target
                if all(
                    math.fabs(
                        round(total_duration / duration / frame_num)
                        * duration
                        * frame_num
                        - total_duration
                    )
                    <= duration_target
                    for frame_num, duration in gif_infos
                ):
                    break

    frame_idxs_input: list[list[int]] = []
    for frame_num, duration in gif_infos:
        frame_idx = 0
        time_start = 0
        frame_idxs: list[int] = []
        for i in range(len(frame_idxs_target)):
            while frame_idx < frame_num:
                if (
                    frame_idx * duration
                    <= i * duration_target - time_start
                    < (frame_idx + 1) * duration
                ):
                    frame_idxs.append(frame_idx)
                    break
                else:
                    frame_idx += 1
                    if frame_idx >= frame_num:
                        frame_idx = 0
                        time_start += frame_num * duration
        frame_idxs_input.append(frame_idxs)

    return frame_idxs_input, frame_idxs_target


Maker = Callable[[list[BuildImage]], BuildImage]


def merge_gif(imgs: list[BuildImage], func: Maker) -> BytesIO:
    """
    合并动图
    :params
      * ``imgs``: 输入图片列表
      * ``func``: 图片处理函数，输入imgs，返回处理后的图片
    """
    images = [img.image for img in imgs]
    gif_images = [image for image in images if getattr(image, "is_animated", False)]

    if len(gif_images) == 1:
        frames: list[IMG] = []
        frame_num = getattr(gif_images[0], "n_frames", 1)
        duration = get_avg_duration(gif_images[0])
        for i in range(frame_num):
            frame_images: list[IMG] = []
            for image in images:
                if getattr(image, "is_animated", False):
                    image.seek(i)
                frame_images.append(image.copy())
            frame = func([BuildImage(image) for image in frame_images])
            frames.append(frame.image)
        return save_gif(frames, duration)

    gif_infos = [
        (getattr(image, "n_frames", 1), get_avg_duration(image)) for image in gif_images
    ]
    target_duration = min(duration for _, duration in gif_infos)
    target_gif_idx = [
        i for i, (_, duration) in enumerate(gif_infos) if duration == target_duration
    ][0]
    target_frame_num = gif_infos[target_gif_idx][0]
    gif_infos.pop(target_gif_idx)
    frame_idxs, target_frame_idxs = get_aligned_gif_indexes(
        gif_infos, target_frame_num, target_duration, FrameAlignPolicy.extend_loop
    )
    frame_idxs.insert(target_gif_idx, target_frame_idxs)

    frames: list[IMG] = []
    for i in range(len(target_frame_idxs)):
        frame_images: list[IMG] = []
        gif_idx = 0
        for image in images:
            if getattr(image, "is_animated", False):
                image.seek(frame_idxs[gif_idx][i])
                gif_idx += 1
            frame_images.append(image.copy())
        frame = func([BuildImage(image) for image in frame_images])
        frames.append(frame.image)

    return save_gif(frames, target_duration)


def make_jpg_or_gif(imgs: list[BuildImage], func: Maker) -> BytesIO:
    """
    制作静图或者动图
    :params
      * ``imgs``: 输入图片列表
      * ``func``: 图片处理函数，输入imgs，返回处理后的图片
    """
    images = [img.image for img in imgs]
    if all(not getattr(image, "is_animated", False) for image in images):
        return func(imgs).save_jpg()

    return merge_gif(imgs, func)


def make_png_or_gif(imgs: list[BuildImage], func: Maker) -> BytesIO:
    """
    制作静图或者动图
    :params
      * ``imgs``: 输入图片列表
      * ``func``: 图片处理函数，输入imgs，返回处理后的图片
    """
    images = [img.image for img in imgs]
    if all(not getattr(image, "is_animated", False) for image in images):
        return func(imgs).save_png()

    return merge_gif(imgs, func)
