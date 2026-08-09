import io
import os
import pathlib

import av
from PIL import Image

from video_converter import remux


VIDEO_SETTINGS = {
    ".mp4": ("libx264", "aac", "yuv420p"),
    ".mov": ("libx264", "aac", "yuv420p"),
    ".mkv": ("libx264", "aac", "yuv420p"),
    ".avi": ("mpeg4", "libmp3lame", "yuv420p"),
    ".webm": ("libvpx-vp9", "libopus", "yuv420p"),
}


def get_output_path(file_path, suffix):
    path = pathlib.Path(file_path)
    return str(path.with_name(path.stem + suffix + path.suffix.lower()))


def compress_video_lossless(file_path):
    output_file_path = get_output_path(file_path, "_lossless")
    input_container = av.open(file_path)
    output_container = av.open(output_file_path, "w")
    try:
        remux(input_container, output_container)
    finally:
        input_container.close()
        output_container.close()
    return output_file_path


def compress_video_by_percent(file_path, percent):
    if not 1 <= percent <= 99:
        raise ValueError("Video compression percent must be between 1 and 99")

    target_fraction = 1.0 - (percent / 100.0)
    output_file_path = get_output_path(file_path, f"_compressed_{percent}")
    original_size = os.path.getsize(file_path)
    target_size = max(int(original_size * target_fraction), 256000)

    probe = av.open(file_path)
    try:
        duration = get_duration_seconds(probe)
    finally:
        probe.close()

    if duration <= 0:
        raise ValueError("Could not determine a valid video duration")

    total_bitrate = int(target_size * 8 / duration * 0.94)
    audio_bitrate = min(128000, max(48000, int(total_bitrate * 0.16)))
    video_bitrate = max(100000, total_bitrate - audio_bitrate)

    encode_video_to_bitrate(
        file_path,
        output_file_path,
        video_bitrate,
        audio_bitrate,
    )

    final_size = os.path.getsize(output_file_path)
    if final_size > target_size * 1.08:
        ratio = target_size / final_size
        os.remove(output_file_path)
        encode_video_to_bitrate(
            file_path,
            output_file_path,
            max(80000, int(video_bitrate * ratio * 0.94)),
            max(32000, int(audio_bitrate * ratio)),
        )

    return output_file_path


def get_duration_seconds(container):
    if container.duration is not None:
        return float(container.duration) / av.time_base

    video_stream = next(
        (
            stream
            for stream in container.streams
            if stream.type == "video"
        ),
        None,
    )

    if (
        video_stream is not None
        and video_stream.duration is not None
        and video_stream.time_base is not None
    ):
        return float(video_stream.duration * video_stream.time_base)

    raise ValueError("Could not determine the video's duration")


def encode_video_to_bitrate(
    file_path,
    output_file_path,
    video_bitrate,
    audio_bitrate,
):
    extension = pathlib.Path(file_path).suffix.lower()
    settings = VIDEO_SETTINGS.get(extension)
    if settings is None:
        raise ValueError("Unsupported video compression format: " + extension)

    video_codec, audio_codec, pixel_format = settings
    input_container = av.open(file_path)
    output_container = av.open(output_file_path, "w")

    try:
        input_video = next(
            (
                stream
                for stream in input_container.streams
                if stream.type == "video"
            ),
            None,
        )
        input_audio = next(
            (
                stream
                for stream in input_container.streams
                if stream.type == "audio"
            ),
            None,
        )

        if input_video is None:
            raise ValueError("The input file contains no video stream")

        frame_rate = input_video.average_rate or 30
        output_video = output_container.add_stream(
            video_codec,
            rate=frame_rate,
        )
        output_video.width = input_video.codec_context.width
        output_video.height = input_video.codec_context.height
        output_video.pix_fmt = pixel_format
        output_video.bit_rate = video_bitrate

        if video_codec == "libx264":
            output_video.codec_context.options = {"preset": "medium"}
        elif video_codec == "libvpx-vp9":
            output_video.codec_context.options = {
                "deadline": "good",
                "cpu-used": "2",
            }

        output_audio = None
        if input_audio is not None:
            sample_rate = input_audio.codec_context.sample_rate or 48000
            output_audio = output_container.add_stream(
                audio_codec,
                rate=sample_rate,
            )
            output_audio.bit_rate = audio_bitrate

        for packet in input_container.demux():
            if packet.stream.index == input_video.index:
                for frame in packet.decode():
                    for encoded_packet in output_video.encode(frame):
                        output_container.mux(encoded_packet)
            elif (
                input_audio is not None
                and output_audio is not None
                and packet.stream.index == input_audio.index
            ):
                for frame in packet.decode():
                    for encoded_packet in output_audio.encode(frame):
                        output_container.mux(encoded_packet)

        for encoded_packet in output_video.encode():
            output_container.mux(encoded_packet)

        if output_audio is not None:
            for encoded_packet in output_audio.encode():
                output_container.mux(encoded_packet)
    finally:
        input_container.close()
        output_container.close()


def compress_image_lossless(file_path):
    extension = pathlib.Path(file_path).suffix.lower()
    output_file_path = get_output_path(file_path, "_lossless")
    image = Image.open(file_path)

    try:
        if extension in (".jpg", ".jpeg"):
            image.save(
                output_file_path,
                quality="keep",
                optimize=True,
                subsampling="keep",
            )
        elif extension == ".webp":
            image.save(output_file_path, lossless=True, method=6)
        elif extension == ".png":
            image.save(output_file_path, optimize=True, compress_level=9)
        else:
            raise ValueError(
                "Compression only supports PNG, JPG, JPEG, and WEBP"
            )
    finally:
        image.close()

    return output_file_path


def compress_image_by_percent(file_path, percent):
    if not 1 <= percent <= 99:
        raise ValueError("Image compression percent must be between 1 and 99")

    extension = pathlib.Path(file_path).suffix.lower()
    output_file_path = get_output_path(file_path, f"_compressed_{percent}")
    target_fraction = 1.0 - (percent / 100.0)
    target_size = max(int(os.path.getsize(file_path) * target_fraction), 1024)
    image = Image.open(file_path)

    try:
        if extension in (".jpg", ".jpeg", ".webp"):
            save_lossy_image_near_target(
                image,
                extension,
                output_file_path,
                target_size,
            )
        elif extension == ".png":
            save_png_near_target(image, output_file_path, target_size)
        else:
            raise ValueError(
                "Compression only supports PNG, JPG, JPEG, and WEBP"
            )
    finally:
        image.close()

    return output_file_path


def save_lossy_image_near_target(
    image,
    extension,
    output_file_path,
    target_size,
):
    if extension in (".jpg", ".jpeg") and image.mode != "RGB":
        image = image.convert("RGB")

    lowest_quality = 5
    highest_quality = 95
    best_bytes = None

    while lowest_quality <= highest_quality:
        quality = (lowest_quality + highest_quality) // 2
        memory_file = io.BytesIO()

        if extension in (".jpg", ".jpeg"):
            image.save(
                memory_file,
                format="JPEG",
                quality=quality,
                optimize=True,
            )
        else:
            image.save(memory_file, format="WEBP", quality=quality, method=6)

        current_bytes = memory_file.getvalue()
        if len(current_bytes) <= target_size:
            best_bytes = current_bytes
            lowest_quality = quality + 1
        else:
            highest_quality = quality - 1

    if best_bytes is None:
        memory_file = io.BytesIO()
        if extension in (".jpg", ".jpeg"):
            image.save(memory_file, format="JPEG", quality=5, optimize=True)
        else:
            image.save(memory_file, format="WEBP", quality=5, method=6)
        best_bytes = memory_file.getvalue()

    pathlib.Path(output_file_path).write_bytes(best_bytes)


def save_png_near_target(image, output_file_path, target_size):
    candidates = []

    lossless_file = io.BytesIO()
    image.save(lossless_file, format="PNG", optimize=True, compress_level=9)
    candidates.append(lossless_file.getvalue())

    rgba_image = image.convert("RGBA")
    for colors_count in (256, 128, 64, 32, 16, 8):
        quantized = rgba_image.quantize(
            colors=colors_count,
            method=Image.Quantize.FASTOCTREE,
        )
        memory_file = io.BytesIO()
        quantized.save(
            memory_file,
            format="PNG",
            optimize=True,
            compress_level=9,
        )
        candidates.append(memory_file.getvalue())

    under_target = [
        candidate for candidate in candidates if len(candidate) <= target_size
    ]

    if under_target:
        selected = max(under_target, key=len)
    else:
        selected = min(candidates, key=len)

    pathlib.Path(output_file_path).write_bytes(selected)
