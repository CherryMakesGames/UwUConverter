import os
import sys
import pathlib
import av
import make_key
import traceback

file_types = {
    # video files
    ".mp4": [
        ("convert to mp3", "Convert To MP3", "MP3"),
        ("convert to wav", "Convert To WAV", "WAV"),
        ("convert to flac", "Convert To FLAC", "FLAC"),
        ("convert to audio ogg", "Convert To Audio OGG", "OGG"),
        ("convert to mkv", "Convert To MKV", "MKV"),
        ("convert to mov", "Convert To MOV", "MOV"),
        ("convert to avi", "Convert To AVI", "AVI"),
        ("convert to webm", "Convert To WEBM", "WEBM")
    ],
    ".mkv": [
        ("convert to mp3", "Convert To MP3", "MP3"),
        ("convert to flac", "Convert To FLAC", "FLAC"),
        ("convert to audio ogg", "Convert To Audio OGG", "OGG"),
        ("convert to wav", "Convert To WAV", "WAV"),
        ("convert to mp4", "Convert To MP4", "MP4"),
        ("convert to mov", "Convert To MOV", "MOV"),
        ("convert to avi", "Convert To AVI", "AVI"),
        ("convert to webm", "Convert To WEBM", "WEBM")
    ],
    ".mov": [
        ("convert to mp3", "Convert To MP3", "MP3"),
        ("convert to flac", "Convert To FLAC", "FLAC"),
        ("convert to audio ogg", "Convert To Audio OGG", "OGG"),
        ("convert to wav", "Convert To WAV", "WAV"),
        ("convert to mp4", "Convert To MP4", "MP4"),
        ("convert to avi", "Convert To AVI", "AVI"),
        ("convert to webm", "Convert To WEBM", "WEBM"),
        ("convert to mkv", "Convert To MKV", "MKV")
    ],
    ".avi": [
        ("convert to mp3", "Convert To MP3", "MP3"),
        ("convert to flac", "Convert To FLAC", "FLAC"),
        ("convert to audio ogg", "Convert To Audio OGG", "OGG"),
        ("convert to mp4", "Convert To MP4", "MP4"),
        ("convert to wav", "Convert To WAV", "WAV"),
        ("convert to webm", "Convert To WEBM", "WEBM"),
        ("convert to mkv", "Convert To MKV", "MKV"),
        ("convert to mov", "Convert To MOV", "MOV")
    ],
    ".webm": [
        ("convert to mp3", "Convert To MP3", "MP3"),
        ("convert to flac", "Convert To FLAC", "FLAC"),
        ("convert to audio ogg", "Convert To Audio OGG", "OGG"),
        ("convert to wav", "Convert To WAV", "WAV"),
        ("convert to mp4", "Convert To MP4", "MP4"),
        ("convert to avi", "Convert To AVI", "AVI"),
        ("convert to mkv", "Convert To MKV", "MKV"),
        ("convert to mov", "Convert To MOV", "MOV")
    ],
    # audio files
    ".mp3": [
        ("convert to mp3", "Convert To MP3", "MP3"),
        ("convert to flac", "Convert To FLAC", "FLAC"),
        ("convert to audio ogg", "Convert To Audio OGG", "OGG"),
        ("convert to wav", "Convert To WAV", "WAV")
    ],
    ".wav": [
        ("convert to mp3", "Convert To MP3", "MP3"),
        ("convert to flac", "Convert To FLAC", "FLAC"),
        ("convert to audio ogg", "Convert To Audio OGG", "OGG")
    ],
    ".ogg": [
        ("convert to mp3", "Convert To MP3", "MP3"),
        ("convert to flac", "Convert To FLAC", "FLAC"),
        ("convert to wav", "Convert To WAV", "WAV")
    ],
    ".flac": [
        ("convert to mp3", "Convert To MP3", "MP3"),
        ("convert to wav", "Convert To WAV", "WAV"),
        ("convert to audio ogg", "Convert To Audio OGG", "OGG")
    ],
    # images

    # documents
}

av.logging.set_level(av.logging.VERBOSE)

def ConvertFile(file_path, convert_type):
    input_file = av.open(file_path)
    output_file_pre_suffix = file_path.removesuffix(pathlib.Path(file_path).suffix)
    output_file = av.open(output_file_pre_suffix + '.' + convert_type, 'w')
    
    try:     
        match convert_type.lower():
            case "mp4" | "mkv" | "webm" | "mov" | "avi":
                stream_map = {}

                for in_stream in input_file.streams:
                    if in_stream.type not in ("video", "audio"):
                        continue    
                    out_stream = output_file.add_stream_from_template(in_stream)
                    stream_map[in_stream.index] = out_stream

                for packet in input_file.demux():
                    if packet.dts is None:
                        continue

                    if packet.stream.index not in stream_map:
                        continue

                    packet.stream = stream_map[packet.stream.index]
                    output_file.mux(packet)
                pass
            case "mp3" | "wav" | "flac" | "ogg":
                stream_map = {}

                for in_stream in input_file.streams:
                    if in_stream.type not in ("audio"):
                        continue    
                    out_stream = output_file.add_stream_from_template(in_stream)
                    stream_map[in_stream.index] = out_stream

                for packet in input_file.demux():
                    if packet.dts is None:
                        continue

                    if packet.stream.index not in stream_map:
                        continue

                    packet.stream = stream_map[packet.stream.index]
                    output_file.mux(packet)
                pass
            case _:
                pass
    finally:
        input_file.close()
        output_file.close()

if __name__ == "__main__":
    try:
        if len(sys.argv) > 2:
            ConvertFile(sys.argv[1], sys.argv[2])
        else: 
            make_key.CreateExtensions(file_types)
    except Exception:
        traceback.print_exc()
        input("\nPress Enter to close...")
