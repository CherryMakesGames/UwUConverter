import av


def convert_video(file_path, output_file_path, output_format):
    input_file = av.open(file_path)
    output_file = av.open(output_file_path, "w")

    try:
        if output_format in ("mp4", "mkv", "mov"):
            remux(input_file, output_file)

        elif output_format == "webm":
            transcode(
                input_file,
                output_file,
                "vp8",
                "libopus"
            )

        elif output_format == "avi":
            transcode(
                input_file,
                output_file,
                "libsvtav1",
                "libmp3lame"
            )

        else:
            raise ValueError(
                "Unsupported video output format: "
                + output_format
            )

    finally:
        input_file.close()
        output_file.close()


def remux(input_file, output_file):
    stream_map = {}

    for in_stream in input_file.streams:
        if in_stream.type not in ("video", "audio"):
            continue

        out_stream = output_file.add_stream_from_template(
            in_stream
        )

        stream_map[in_stream.index] = out_stream

    for packet in input_file.demux():
        if packet.dts is None:
            continue

        if packet.stream.index not in stream_map:
            continue

        packet.stream = stream_map[packet.stream.index]
        output_file.mux(packet)


def transcode(
    input_file,
    output_file,
    video_encoder,
    audio_encoder
):
    stream_map = {}

    for in_stream in input_file.streams:
        if in_stream.type == "video":
            frame_rate = in_stream.average_rate or 30

            out_stream = output_file.add_stream(
                video_encoder,
                rate=frame_rate
            )

            out_stream.width = (
                in_stream.codec_context.width
            )

            out_stream.height = (
                in_stream.codec_context.height
            )

            out_stream.pix_fmt = "yuv420p"
            stream_map[in_stream.index] = out_stream

        elif in_stream.type == "audio":
            sample_rate = (
                in_stream.codec_context.sample_rate
                or 48000
            )

            out_stream = output_file.add_stream(
                audio_encoder,
                rate=sample_rate
            )

            if in_stream.codec_context.layout is not None:
                out_stream.layout = (
                    in_stream.codec_context.layout
                )

            stream_map[in_stream.index] = out_stream

    for packet in input_file.demux():
        if packet.stream.index not in stream_map:
            continue

        out_stream = stream_map[packet.stream.index]

        for frame in packet.decode():
            for output_packet in out_stream.encode(frame):
                output_file.mux(output_packet)

    for out_stream in stream_map.values():
        for packet in out_stream.encode():
            output_file.mux(packet)
