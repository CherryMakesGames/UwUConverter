import os
import sys
import pathlib
import av
import make_key

file_types = {
    ".mp4": [
        ("convert to mp3", "Convert To MP3", "MP3"),
        ("convert to wav", "Convert To WAV", "WAV"),
        ("convert to mkv", "Convert To MKV", "MKV")
    ],
    ".mkv": [
        ("convert to mp4", "Convert To MP4", "MP4"),
        ("convert to mp3", "Convert To MP3", "MP3"),
        ("convert to wav", "Convert To WAV", "WAV")
    ]
}

av.logging.set_level(av.logging.VERBOSE)

def ConvertFile(file_path, convert_type):
    input_file = av.open(file_path)
    output_file_pre_suffix = file_path.remove_suffix(pathlib.Path(file_path).suffix)
    output_file = av.open(output_file_pre_suffix + '.' + convert_type, 'w')

    match convert_type.lower():
        case "mp4":
            for in_stream in input_file.streams:
                out_stream = output_file.add_stream(template=in_stream)
                for packet in input_file.demux(in_stream):
                    if packet.dts is None:
                        print("***")
                        continue
                    packet.stream = out_stream
                    output_file.mux(packet)
            pass
        case "mp3":
            
            pass
        case _:
            pass
    input_file.close()
    output_file.close()

if __name__ == "__main__":
    if len(sys.argv) > 2:
        ConvertFile(sys.argv[1], sys.argv[2])
    else: 
        make_key.CreateExtensions(file_types)
    
