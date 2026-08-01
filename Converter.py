import av
import os
import sys
import make_key

file_types = {
    ".mp4": [
        ("convert to mp3", "Convert To MP3", "MP3"),
        ("convert to wav", "Convert To WAV", "WAV")
    ]
}

av.logging.set_level(av.logging.VERBOSE)

if __name__ == "__main__":
    make_key.CreateExtensions(file_types)
    
