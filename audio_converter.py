import av


AUDIO_CODECS = {
    "mp3": "libmp3lame",
    "wav": "pcm_s16le",
    "flac": "flac",
    "ogg": "vorbis",
    "opus": "libopus"
}


def convert_audio(file_path, output_file_path, output_format):
    encoder = AUDIO_CODECS.get(output_format)

    if encoder is None:
        raise ValueError(
            "Unsupported audio output format: "
            + output_format
        )

    input_file = av.open(file_path)
    output_file = av.open(output_file_path, "w")

    try:
        transcode_audio(
            input_file,
            output_file,
            encoder
        )
    finally:
        input_file.close()
        output_file.close()


def transcode_audio(input_file, output_file, encoder):
    input_stream = next(
        (
            stream
            for stream in input_file.streams
            if stream.type == "audio"
        ),
        None
    )

    if input_stream is None:
        raise ValueError(
            "The input file contains no audio stream"
        )

    sample_rate = (
        input_stream.codec_context.sample_rate
        or 48000
    )

    output_stream = output_file.add_stream(
        encoder,
        rate=sample_rate
    )

    if encoder == "libmp3lame":
        output_stream.bit_rate = 320000

    elif encoder == "vorbis":
        output_stream.codec_context.options = {
            "strict": "-2"
        }
        output_stream.bit_rate = 192000

    elif encoder == "libopus":
        output_stream.bit_rate = 192000

    for frame in input_file.decode(input_stream):
        for packet in output_stream.encode(frame):
            output_file.mux(packet)

    for packet in output_stream.encode():
        output_file.mux(packet)
