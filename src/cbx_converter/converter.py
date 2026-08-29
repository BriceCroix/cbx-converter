import os
import shutil
import tarfile
import tempfile
import zipfile
from pathlib import Path

import acefile
import img2pdf
import PIL
import puremagic
import py7zr
import rarfile
from natsort import natsorted
from tqdm import tqdm


def safe_extension(ext: str) -> str:
    """Converts an extension to its canonical equivalent, groups similar
    extensions together, and removes leading dot if any.

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

    >>> safe_extension(".JPEG")
    'jpg'
    >>> safe_extension("jpe")
    'jpg'
    >>> safe_extension("png")
    'png'
    >>> safe_extension(".zip")
    'zip'
    """
    ext = ext.lower().strip()
    if ext[0] == ".":
        ext = ext[1:]

    match ext:
        case "jpg" | "jpeg" | "jpe" | "jif" | "jfif" | "jfi":
            return "jpg"
        case _:
            return ext


def cbz_convert(
    input: str,
    output: str,
    image_formats: list[str] | str | None = None,
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
    image_formats : list[str] | str | None (optional)
        If provided, the file formats to be forced for each image in the cbz archive
        (jpg, png...).
    quality : int | None (optional)
        If provided, allows to lower the quality of the images (0 is worst, 100 is best)
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
        if isinstance(image_formats, str):
            image_formats = [image_formats]
        # remove duplicates
        image_formats = list(dict.fromkeys([safe_extension(f) for f in image_formats]))

    with (
        tempfile.TemporaryDirectory() as input_tempdir,
        tempfile.TemporaryDirectory() as output_tempdir,
    ):
        try:
            magic_extension = safe_extension(puremagic.magic_file(input)[0].extension)

            match magic_extension:
                case "cbz" | "zip":
                    with zipfile.ZipFile(input, "r") as zf:
                        zf.extractall(path=input_tempdir)
                case "cbr" | "rar":
                    with rarfile.RarFile(input, "r") as rf:
                        rf.extractall(path=input_tempdir)
                case "cb7" | "7z":
                    with py7zr.SevenZipFile(input, "r") as sf:
                        sf.extractall(path=input_tempdir)
                case "cbt" | "tar":
                    with tarfile.TarFile(input, "r") as tf:
                        tf.extractall(path=input_tempdir, filter='tar')
                case "cba" | "ace":
                    with acefile.open(input, "r") as af:
                        af.extractall(path=input_tempdir)
                case _:
                    raise RuntimeError(
                        f'Unrecognized magic extension "{magic_extension}"'
                    )

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

                    image_file_ext_in = safe_extension(
                        os.path.splitext(image_filename_in)[1]
                    )
                    image_file_ext_out = safe_extension(
                        image_file_ext_in
                        if image_formats is None or image_file_ext_in in image_formats
                        else image_formats[0]
                    )

                    image_filename_out = (
                        os.path.splitext(image_filename_in)[0]
                        + "."
                        + image_file_ext_out
                    )

                    if image_file_ext_out == "jpg":
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

            output_ext = safe_extension(os.path.splitext(output)[1])
            match output_ext:
                case "pdf":
                    images_filenames_out_absolute = [
                        os.path.join(output_tempdir, image_filename_out)
                        for image_filename_out in images_filenames_out
                    ]
                    with open(output, "wb") as out:
                        out.write(img2pdf.convert(images_filenames_out_absolute))
                case "cbz" | "zip":
                    with zipfile.ZipFile(output, "w") as out:
                        for image_filename_out in tqdm(
                            images_filenames_out, desc="Writing", leave=False
                        ):
                            out.write(
                                os.path.join(output_tempdir, image_filename_out),
                                image_filename_out,
                            )
                case "cbr" | "rar" | "cba" | "ace":
                    # rarfile and acefile would throw an exception anyway.
                    raise RuntimeError(
                        f"{output_ext} files can only be read but not written"
                    )
                case "cb7" | "7z":
                    with py7zr.SevenZipFile(output, "w") as out:
                        for image_filename_out in tqdm(
                            images_filenames_out, desc="Writing", leave=False
                        ):
                            out.write(
                                os.path.join(output_tempdir, image_filename_out),
                                image_filename_out,
                            )
                case "cbt" | "tar":
                    with tarfile.TarFile(output, "w") as out:
                        for image_filename_out in tqdm(
                            images_filenames_out, desc="Writing", leave=False
                        ):
                            image_filename_out_absolute = os.path.join(
                                output_tempdir, image_filename_out
                            )
                            with open(image_filename_out_absolute, "rb") as img:
                                out.addfile(
                                    out.gettarinfo(
                                        image_filename_out_absolute,
                                        image_filename_out,
                                    ),
                                    img,
                                )
                case _:
                    raise f"Unsupported format : {output_ext}"
            return True
        except Exception as e:  # noqa: BLE001
            print(f"Error converting file {input} : {e}")
            return False
