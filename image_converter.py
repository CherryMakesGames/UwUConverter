import pathlib

from PIL import Image

from image_safety import open_image_safely


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


IMAGE_INPUT_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".ico",
    ".tif",
    ".tiff",
    ".raw",
}


def open_input_image(file_path):
    if pathlib.Path(file_path).suffix.lower() == ".raw":
        import rawpy

        with rawpy.imread(file_path) as raw_image:
            rgb = raw_image.postprocess()
            return Image.fromarray(rgb)

    return open_image_safely(
        file_path
    )


def convert_images_to_pdf(
    file_paths,
    output_file_path,
):
    paths = [
        pathlib.Path(path)
        for path in file_paths
    ]

    if len(paths) < 2:
        raise ValueError(
            "Select at least two images to create one PDF."
        )

    unsupported = [
        str(path)
        for path in paths
        if path.suffix.lower() not in IMAGE_INPUT_EXTENSIONS
    ]

    if unsupported:
        raise ValueError(
            "Unsupported image selected for combined PDF: "
            + unsupported[0]
        )

    pages = []

    try:
        for path in paths:
            image = open_input_image(
                path
            )

            prepared = None

            try:
                prepared = prepare_for_pdf(
                    image
                )
                prepared.load()

                # Copy each page so it remains valid after the source image
                # and its underlying file handle are closed.
                pages.append(
                    prepared.copy()
                )

            finally:
                if (
                    prepared is not None
                    and prepared is not image
                ):
                    prepared.close()

                image.close()

        first_page = pages[0]
        first_page.save(
            output_file_path,
            "PDF",
            save_all=True,
            append_images=pages[1:],
        )

    finally:
        for page in pages:
            page.close()


def convert_image(file_path, output_file_path, output_format):
    if output_format not in IMAGE_OUTPUTS:
        raise ValueError(
            "Unsupported image output format: "
            + output_format
        )

    image = open_input_image(
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
