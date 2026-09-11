import pathlib
import warnings

from PIL import Image


# Pillow's default decompression-bomb hard error triggers at about 179 MP.
# UwUConverter is often used deliberately on very large local artwork, so use
# a larger but still bounded limit instead of disabling the protection.
UWU_MAX_IMAGE_PIXELS = 300_000_000


IMAGE_OUTPUTS = {
    "png",
    "jpg",
    "jpeg",
    "webp",
    "ico",
    "tif",
    "tiff",
    "pdf"
}


def convert_image(file_path, output_file_path, output_format):
    if output_format not in IMAGE_OUTPUTS:
        raise ValueError(
            "Unsupported image output format: "
            + output_format
        )

    if pathlib.Path(file_path).suffix.lower() == ".raw":
        import rawpy

        with rawpy.imread(file_path) as raw_image:
            rgb = raw_image.postprocess()
            image = Image.fromarray(rgb)
    else:
        image = open_large_image_safely(
            file_path
        )

    try:
        if output_format in ("jpg", "jpeg"):
            image = prepare_for_jpeg(image)

        elif output_format == "pdf":
            image = prepare_for_pdf(image)

        image.save(output_file_path)

    finally:
        image.close()


def open_large_image_safely(
    file_path,
):
    previous_limit = (
        Image.MAX_IMAGE_PIXELS
    )

    # Pillow raises DecompressionBombError at 2x MAX_IMAGE_PIXELS. Raise the
    # internal threshold just long enough to inspect the image ourselves.
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
                "Image is too large for UwUConverter's safety limit.\n\n"
                + "Size: "
                + f"{width:,} x {height:,} "
                + f"({pixels:,} pixels)\n"
                + "Limit: "
                + f"{UWU_MAX_IMAGE_PIXELS:,} pixels"
            )

        return image

    finally:
        Image.MAX_IMAGE_PIXELS = (
            previous_limit
        )


def prepare_for_jpeg(image):
    if image.mode in ("RGBA", "LA"):
        background = Image.new(
            "RGB",
            image.size,
            (255, 255, 255)
        )

        alpha = image.getchannel("A")
        background.paste(image, mask=alpha)
        return background

    if image.mode != "RGB":
        return image.convert("RGB")

    return image


def prepare_for_pdf(image):
    if image.mode not in ("RGBA", "LA", "P"):
        return image

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
        return background

    return image.convert("RGB")
