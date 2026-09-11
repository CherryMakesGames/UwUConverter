import warnings

from PIL import Image


# Pillow's default hard decompression-bomb error is around 179 MP.
# UwUConverter deliberately works with very large local artwork, so it uses a
# larger bounded limit rather than disabling Pillow's protection completely.
UWU_MAX_IMAGE_PIXELS = 300_000_000


def open_image_safely(
    file_path,
):
    previous_limit = (
        Image.MAX_IMAGE_PIXELS
    )

    # Pillow raises DecompressionBombError at roughly 2x MAX_IMAGE_PIXELS.
    # Raise its internal threshold only while opening this selected local file,
    # then enforce UwUConverter's own stricter 300 MP limit ourselves.
    Image.MAX_IMAGE_PIXELS = (
        UWU_MAX_IMAGE_PIXELS
    )

    try:
        with warnings.catch_warnings():
            warnings.simplefilter(
                "ignore",
                Image.DecompressionBombWarning,
            )

            image = Image.open(
                file_path
            )

        width, height = image.size
        pixels = width * height

        if pixels > UWU_MAX_IMAGE_PIXELS:
            image.close()

            raise ValueError(
                "Image is too large for UwUConverter's safety limit.\\n\\n"
                + "Size: "
                + f"{width:,} x {height:,} "
                + f"({pixels:,} pixels)\\n"
                + "Limit: "
                + f"{UWU_MAX_IMAGE_PIXELS:,} pixels"
            )

        return image

    finally:
        Image.MAX_IMAGE_PIXELS = (
            previous_limit
        )
