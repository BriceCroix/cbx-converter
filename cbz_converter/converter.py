import os
import shutil
import tempfile
import zipfile
from pathlib import Path

import img2pdf
import PIL
from natsort import natsorted
from tqdm import tqdm


def safe_img_extension(ext: str) -> str:
    """Converts an image extension to its canonical equivalent.

    Parameters
    ----------
    ext : str
        The extension to check.

    Returns
    -------
    str
        The canonical equivalent of given extension

    Example
    -------

    >>> safe_img_extension("JPEG")
    'jpg'
    >>> safe_img_extension("jpe")
    'jpg'
    >>> safe_img_extension("png")
    'png'
    """
    match ext.lower().strip():
        case "jpg" | "jpeg" | "jpe" | "jif" | "jfif" | "jfi":
            return "jpg"
        case _:
            return ext.lower().strip()


def cbz_convert(
    input: str,
    output: str,
    image_formats: list[str] | None = None,
    quality: int | None = None,
    max_size: int | None = None,
) -> bool:
    """Converts a cbz file into another file.

    Parameters
    ----------
    input : str
        Path to a cbz file.
    output : str
        Path to file to be created.
    image_formats : str | None (optional)
        If provided, the file formats to be forced for each image in the cbz archive (jpg, png...).
    quality : int | None (optional)
        If provided, allows to lower the quality of the images (0 is worst, 100 is best).
        Only supported for file types : avif, jpg, webp.
    max_size : int | None (optional)
        If provided, images will be resized with this value as their width or height.

    Returns
    -------
    bool
        True for success.
    """
    os.makedirs(os.path.dirname(output), exist_ok=True)

    if image_formats is not None:
        image_formats = list({safe_img_extension(f) for f in image_formats})

    with (
        zipfile.ZipFile(input, "r") as zf,
        tempfile.TemporaryDirectory() as input_tempdir,
        tempfile.TemporaryDirectory() as output_tempdir,
    ):
        try:
            zf.extractall(path=input_tempdir)
            images_filenames_in = natsorted(
                [
                    os.path.relpath(p, start=input_tempdir)
                    for p in Path(input_tempdir).rglob("*")
                    if p.is_file()
                ]
            )
            images_filenames_out = []

            # If there is anything to do on the images themselves
            if quality is not None or max_size is not None or image_formats is not None:
                for image_filename_in in tqdm(
                    images_filenames_in, desc="Processing", leave=False
                ):
                    image = PIL.Image.open(
                        os.path.join(input_tempdir, image_filename_in)
                    )

                    if max_size is not None:
                        size = max(image.size)
                        if size > max_size:
                            ratio = max_size / size
                            image = image.resize(
                                size=(
                                    int(image.width * ratio),
                                    int(image.height * ratio),
                                ),
                                resample=PIL.Image.Resampling.LANCZOS,
                            )

                    image_file_ext_in = safe_img_extension(
                        os.path.splitext(image_filename_in)[1]
                    )
                    image_file_ext_out = (
                        image_file_ext_in
                        if image_formats is None or image_file_ext_in in image_formats
                        else image_formats[0]
                    )

                    if image_file_ext_out[0] != ".":
                        image_file_ext_out = "." + image_file_ext_out

                    if image_file_ext_out != image_file_ext_in:
                        image_filename_out = (
                            os.path.splitext(image_filename_in)[0] + image_file_ext_out
                        )
                    else:
                        image_filename_out = image_filename_in

                    if image_file_ext_out == ".jpg":
                        image = image.convert("RGB")

                    # Only use quality argument if provided.
                    quality_dict = {"quality": quality} if quality is not None else {}

                    image_filename_out_absolute = os.path.join(
                        output_tempdir, image_filename_out
                    )
                    os.makedirs(
                        os.path.dirname(image_filename_out_absolute), exist_ok=True
                    )
                    image.save(
                        image_filename_out_absolute,
                        optimize=True,
                        **quality_dict,
                    )
                    images_filenames_out.append(image_filename_out)
            else:
                shutil.copytree(input_tempdir, output_tempdir, dirs_exist_ok=True)
                images_filenames_out = images_filenames_in

            output_ext = os.path.splitext(output)[1].lower()
            if output_ext == ".pdf":
                images_filenames_out_absolute = [
                    os.path.join(output_tempdir, image_filename_out)
                    for image_filename_out in images_filenames_out
                ]
                with open(output, "wb") as out:
                    out.write(img2pdf.convert(images_filenames_out_absolute))
            elif output_ext == ".cbz":
                with zipfile.ZipFile(output, "w") as out:
                    for image_filename_out in tqdm(
                        images_filenames_out, desc="Writing", leave=False
                    ):
                        out.write(
                            os.path.join(output_tempdir, image_filename_out),
                            image_filename_out,
                        )
            else:
                raise f"Unsupported format : {output_ext}"
            return True
        except Exception as e:  # noqa: BLE001
            print(f"Error converting file {input} : {e}")
            return False


if __name__ == "__main__":
    import doctest

    doctest.testmod(verbose=True)
