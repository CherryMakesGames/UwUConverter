"""Container-safe PyAV conversion with automatic compatible codec fallback."""
from pathlib import Path
import av

# Codec identifiers returned by AV streams may have aliases; only copy known
# container-safe pairs, otherwise transcode to a supported target pair.
COPYABLE = {
    "mp4": ({"h264", "hevc", "mpeg4", "av1"}, {"aac", "mp3", "alac"}),
    "mov": ({"h264", "hevc", "mpeg4", "prores", "av1"}, {"aac", "mp3", "alac", "pcm_s16le"}),
    "mkv": (None, None),  # Matroska accepts many codecs; muxer can still reject some.
    "webm": ({"vp8", "vp9", "av1"}, {"vorbis", "opus"}),
    "avi": ({"mpeg4", "mpeg2video", "mjpeg"}, {"mp3", "pcm_s16le"}),
}
FALLBACK = {
    "mp4": (["libx264", "h264", "mpeg4"], ["aac"]),
    "mov": (["libx264", "h264", "mpeg4"], ["aac"]),
    "mkv": (["libx264", "h264", "mpeg4"], ["aac", "libopus"]),
    "webm": (["libvpx-vp9", "libvpx", "vp9", "vp8"], ["libopus", "libvorbis", "vorbis"]),
    "avi": (["mpeg4", "mjpeg"], ["libmp3lame", "mp3", "pcm_s16le"]),
}


def _encoder_available(name):
    try:
        av.codec.Codec(name, "w")
        return True
    except Exception:
        return False


def choose_encoder(candidates):
    for encoder in candidates:
        if _encoder_available(encoder):
            return encoder
    raise RuntimeError("No compatible encoder available for this output container: " + ", ".join(candidates))


def needs_transcoding(input_file, output_format):
    if output_format not in COPYABLE:
        raise ValueError("Unsupported video output format: " + output_format)
    video_allowed, audio_allowed = COPYABLE[output_format]
    for stream in input_file.streams:
        if stream.type not in ("video", "audio"):
            continue
        if video_allowed is not None and stream.type == "video" and stream.codec_context.name.lower() not in video_allowed:
            return True
        if audio_allowed is not None and stream.type == "audio" and stream.codec_context.name.lower() not in audio_allowed:
            return True
    return False


def convert_video(file_path, output_file_path, output_format):
    output_format = output_format.lower()
    if output_format not in FALLBACK:
        raise ValueError("Unsupported video output format: " + output_format)
    source = Path(file_path)
    destination = Path(output_file_path)
    if source.resolve() == destination.resolve():
        raise ValueError("Input and output paths must differ")
    with av.open(str(source)) as input_file:
        must_transcode = needs_transcoding(input_file, output_format)
    if not must_transcode:
        try:
            with av.open(str(source)) as input_file, av.open(str(destination), "w", format=("matroska" if output_format == "mkv" else output_format)) as output_file:
                remux(input_file, output_file)
            return
        except (av.AVError if hasattr(av, "AVError") else Exception, ValueError, OSError):
            # Even a known codec may be rejected by the actual muxer. Retry
            # from the original source, not from a partially written output.
            destination.unlink(missing_ok=True)
    video_names, audio_names = FALLBACK[output_format]
    with av.open(str(source)) as input_file:
        has_video = any(s.type == "video" for s in input_file.streams)
        has_audio = any(s.type == "audio" for s in input_file.streams)
    vencoder = choose_encoder(video_names) if has_video else None
    aencoder = choose_encoder(audio_names) if has_audio else None
    with av.open(str(source)) as input_file, av.open(str(destination), "w", format=("matroska" if output_format == "mkv" else output_format)) as output_file:
        transcode(input_file, output_file, vencoder, aencoder)


def remux(input_file, output_file):
    stream_map = {}
    for stream in input_file.streams:
        if stream.type in ("video", "audio"):
            stream_map[stream.index] = output_file.add_stream_from_template(stream)
    for packet in input_file.demux():
        if packet.dts is None or packet.stream.index not in stream_map:
            continue
        packet.stream = stream_map[packet.stream.index]
        output_file.mux(packet)


def transcode(input_file, output_file, video_encoder, audio_encoder):
    stream_map = {}
    for incoming in input_file.streams:
        if incoming.type == "video" and video_encoder:
            outgoing = output_file.add_stream(video_encoder, rate=incoming.average_rate or 30)
            outgoing.width = incoming.codec_context.width
            outgoing.height = incoming.codec_context.height
            outgoing.pix_fmt = "yuv420p"
            stream_map[incoming.index] = outgoing
        elif incoming.type == "audio" and audio_encoder:
            rate = incoming.codec_context.sample_rate or 48000
            # Opus encoders normally require 48kHz; PyAV resamples on encode
            # where supported. Never copy an incompatible input audio codec.
            if "opus" in audio_encoder:
                rate = 48000
            outgoing = output_file.add_stream(audio_encoder, rate=rate)
            stream_map[incoming.index] = outgoing
    if not stream_map:
        raise ValueError("No video or audio streams to convert")
    for packet in input_file.demux():
        outgoing = stream_map.get(packet.stream.index)
        if outgoing is None:
            continue
        for frame in packet.decode():
            for encoded in outgoing.encode(frame):
                output_file.mux(encoded)
    for outgoing in stream_map.values():
        for encoded in outgoing.encode():
            output_file.mux(encoded)
