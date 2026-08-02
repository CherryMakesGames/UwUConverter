import os
import sys
import pathlib
import av
import make_key
import traceback
from PIL import Image
import rawpy
from pdf2docx import Converter

file_types = {
    # video files
    ".mp4": [
        ("convert to mp3", "Convert To MP3", "MP3"),
        ("convert to wav", "Convert To WAV", "WAV"),
        ("convert to flac", "Convert To FLAC", "FLAC"),
        ("convert to audio ogg", "Convert To Audio OGG", "OGG"),
        ("convert to opus", "Convert To OPUS", "OPUS"),
        ("convert to mkv", "Convert To MKV", "MKV"),
        ("convert to mov", "Convert To MOV", "MOV"),
        ("convert to avi", "Convert To AVI", "AVI"),
        ("convert to webm", "Convert To WEBM", "WEBM")
    ],
    ".mkv": [
        ("convert to mp3", "Convert To MP3", "MP3"),
        ("convert to flac", "Convert To FLAC", "FLAC"),
        ("convert to audio ogg", "Convert To Audio OGG", "OGG"),
        ("convert to opus", "Convert To OPUS", "OPUS"),
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
        ("convert to opus", "Convert To OPUS", "OPUS"),
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
        ("convert to opus", "Convert To OPUS", "OPUS"),
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
        ("convert to opus", "Convert To OPUS", "OPUS"),
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
        ("convert to wav", "Convert To WAV", "WAV"),
        ("convert to opus", "Convert To OPUS", "OPUS")
    ],
    ".wav": [
        ("convert to mp3", "Convert To MP3", "MP3"),
        ("convert to flac", "Convert To FLAC", "FLAC"),
        ("convert to audio ogg", "Convert To Audio OGG", "OGG"),
        ("convert to opus", "Convert To OPUS", "OPUS")
    ],
    ".ogg": [
        ("convert to mp3", "Convert To MP3", "MP3"),
        ("convert to flac", "Convert To FLAC", "FLAC"),
        ("convert to wav", "Convert To WAV", "WAV"),
        ("convert to opus", "Convert To OPUS", "OPUS")
    ],
    ".flac": [
        ("convert to mp3", "Convert To MP3", "MP3"),
        ("convert to wav", "Convert To WAV", "WAV"),
        ("convert to audio ogg", "Convert To Audio OGG", "OGG"),
        ("convert to opus", "Convert To OPUS", "OPUS")
    ],
    ".opus": [
        ("convert to mp3", "Convert To MP3", "MP3"),
        ("convert to wav", "Convert To WAV", "WAV"),
        ("convert to audio ogg", "Convert To Audio OGG", "OGG"),
        ("convert to flac", "Convert To FLAC", "FLAC"),
    ],
    # images
    ".png": [
        ("convert to jpg", "Convert To JPG", "JPG"),
        ("convert to jpeg", "Convert To JPEG", "JPEG"),
        ("convert to webp", "Convert To WEBP", "WEBP"),
        ("convert to ico", "Convert To ICO", "ICO"),
        ("convert to pdf", "Convert To PDF", "PDF")
    ],
    ".jpg": [
        ("convert to png", "Convert To PNG", "PNG"),
        ("convert to jpeg", "Convert To JPEG", "JPEG"),
        ("convert to webp", "Convert To WEBP", "WEBP"),
        ("convert to ico", "Convert To ICO", "ICO"),
        ("convert to pdf", "Convert To PDF", "PDF")
    ],
    ".jpeg": [
        ("convert to png", "Convert To PNG", "PNG"),
        ("convert to jpg", "Convert To JPG", "JPG"),
        ("convert to webp", "Convert To WEBP", "WEBP"),
        ("convert to ico", "Convert To ICO", "ICO"),
        ("convert to pdf", "Convert To PDF", "PDF")
    ],
    ".webp": [
        ("convert to png", "Convert To PNG", "PNG"),
        ("convert to jpg", "Convert To JPG", "JPG"),
        ("convert to jpeg", "Convert To JPEG", "JPEG"),
        ("convert to ico", "Convert To ICO", "ICO"),
        ("convert to pdf", "Convert To PDF", "PDF")
    ],
    ".ico": [
        ("convert to png", "Convert To PNG", "PNG"),
        ("convert to jpg", "Convert To JPG", "JPG"),
        ("convert to jpeg", "Convert To JPEG", "JPEG"),
        ("convert to webp", "Convert To WEBP", "WEBP"),
        ("convert to pdf", "Convert To PDF", "PDF")
    ],
    ".raw": [
        ("convert to png", "Convert To PNG", "PNG"),
        ("convert to jpg", "Convert To JPG", "JPG"),
        ("convert to jpeg", "Convert To JPEG", "JPEG"),
        ("convert to webp", "Convert To WEBP", "WEBP"),
        ("convert to ico", "Convert To ICO", "ICO"),
        ("convert to pdf", "Convert To PDF", "PDF")
    ],
    # documents
    ".pdf": [
        ("convert to docx", "Convert To DOCX", "DOCXFPDF")
    ],
    ".docx": [
        ("convert to pdf", "Convert To PDF", "DOCPDF"),
        ("convert to txt", "Convert To TXT", "TXT"),
        ("convert to odt", "Convert To ODT", "ODT"),
        ("convert to doc", "Convert To DOC", "DOC")
    ],
    ".txt": [
        ("convert to pdf", "Convert To PDF", "DOCPDF"),
        ("convert to odt", "Convert To ODT", "ODT"),
        ("convert to doc", "Convert To DOC", "DOC"),
        ("convert to docx", "Convert To DOCX", "DOCX")
    ],
    ".odt": [
        ("convert to pdf", "Convert To PDF", "DOCPDF"),
        ("convert to txt", "Convert To TXT", "TXT"),
        ("convert to doc", "Convert To DOC", "DOC"),
        ("convert to docx", "Convert To DOCX", "DOCX")
    ],
    ".doc": [
        ("convert to pdf", "Convert To PDF", "DOCPDF"),
        ("convert to txt", "Convert To TXT", "TXT"),
        ("convert to odt", "Convert To ODT", "ODT"),
        ("convert to docx", "Convert To DOCX", "DOCX")
    ],
    # excel etc.
    ".xlsx": [

    ],
    ".xls": [

    ],
    ".ods": [

    ],
    ".csv": [

    ],
    ".xlsb": [

    ]
}

av.logging.set_level(av.logging.VERBOSE)

def ConvertFile(file_path, convert_type):
    input_file = None
    output_file = None
    
    output_file_pre_suffix = file_path.removesuffix(pathlib.Path(file_path).suffix)
    output_file_path = output_file_pre_suffix + '.' + convert_type.lower()
    
    try:     
        match convert_type.lower():
            
            # video file conversions
            
            case "mp4" | "mkv" | "mov" :
                input_file = av.open(file_path)
                output_file = av.open(output_file_path, 'w')
                Remux(input_file, output_file)
                pass
            case "webm":
                input_file = av.open(file_path)
                output_file = av.open(output_file_path, 'w')
                Transcode(input_file, output_file, "vp8", "libopus")
                pass
            case "avi":
                input_file = av.open(file_path)
                output_file = av.open(output_file_path, 'w')
                Transcode(input_file, output_file, "libsvtav1", "libmp3lame")
                pass
            
            # audio file conversions
            
            case "mp3" | "wav" | "flac" | "ogg" | "opus":
                input_file = av.open(file_path)
                output_file = av.open(output_file_path, "w")

                audio_codecs = {
                    "mp3": "libmp3lame",
                    "wav": "pcm_s16le",
                    "flac": "flac",
                    "ogg": "vorbis",
                    "opus": "libopus"
                }

                TranscodeAudio(
                    input_file,
                    output_file,
                    audio_codecs[convert_type.lower()]
                )
            
            # image file conversions
            
            case "png" | "jpg" | "jpeg" | "webp" | "ico" | "pdf":
                if pathlib.Path(file_path).suffix.lower() == ".raw":
                    with rawpy.imread(file_path) as raw_image:
                        rgb = raw_image.postprocess()
                        image = Image.fromarray(rgb)
                else:
                    image = Image.open(file_path)

                try:
                    if convert_type.lower() in ("jpg", "jpeg"):
                        if image.mode in ("RGBA", "LA"):
                            background = Image.new(
                                "RGB",
                                image.size,
                                (255, 255, 255)
                            )

                            alpha = image.getchannel("A")

                            background.paste(
                                image,
                                mask=alpha
                            )

                            image = background

                        elif image.mode != "RGB":
                            image = image.convert("RGB")

                    elif convert_type.lower() == "pdf":
                        if image.mode in ("RGBA", "LA", "P"):
                            background = Image.new(
                                "RGB",
                                image.size,
                                (255, 255, 255)
                            )

                            if image.mode == "P":
                                image = image.convert("RGBA")

                            if image.mode in ("RGBA", "LA"):
                                background.paste(
                                    image,
                                    mask=image.getchannel("A")
                                )
                                image = background
                            else:
                                image = image.convert("RGB")

                    image.save(output_file_path)
                finally:
                    image.close()
            
            # document file conversions
            
            case "DOCXFPDF":
                pdf_file = input_file
                
                docx_file = output_file_path = output_file_pre_suffix + ".pdf"
                
                cv = Converter(pdf_file)
                cv.convert(docx_file)
                cv.close()
                pass
            
            case _:
                pass
    finally:
        if input_file is not None:
            input_file.close()

        if output_file is not None:
            output_file.close()

def Remux(input_file, output_file):
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

def Transcode(input_file, output_file, encoderVideo, encoderAudio):
    stream_map = {}

    for in_stream in input_file.streams:
        if in_stream.type == "video":
            out_stream = output_file.add_stream(
                encoderVideo,
                rate=in_stream.average_rate
            )

            out_stream.width = in_stream.codec_context.width
            out_stream.height = in_stream.codec_context.height
            out_stream.pix_fmt = "yuv420p"

            stream_map[in_stream.index] = out_stream

        elif in_stream.type == "audio":
            out_stream = output_file.add_stream(
                encoderAudio,
                rate=in_stream.codec_context.sample_rate
            )

            out_stream.layout = in_stream.codec_context.layout
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

def TranscodeAudio(input_file, output_file, encoder):
    input_stream = next(
        (
            stream
            for stream in input_file.streams
            if stream.type == "audio"
        ),
        None
    )

    if input_stream is None:
        raise ValueError("The input file contains no audio stream")

    sample_rate = input_stream.codec_context.sample_rate or 48000

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

    # Flush remaining encoded audio
    for packet in output_stream.encode():
        output_file.mux(packet)

if __name__ == "__main__":
    try:
        if len(sys.argv) > 2:
            ConvertFile(sys.argv[1], sys.argv[2])
        else: 
            make_key.CreateExtensions(file_types)
    except Exception:
        traceback.print_exc()
        input("\nPress Enter to close...")