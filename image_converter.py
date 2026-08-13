import pathlib

from PIL import Image


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
        image = Image.open(file_path)

    try:
        if output_format in ("jpg", "jpeg"):
            image = prepare_for_jpeg(image)

        elif output_format == "pdf":
            image = prepare_for_pdf(image)

        image.save(output_file_path)

    finally:
        image.close()


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
