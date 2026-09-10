import os
import shutil
import tarfile
import tempfile
import zipfile
from enum import Enum
from pathlib import Path

import acefile
import img2pdf
import PIL
import puremagic
import py7zr
import rarfile
from natsort import natsorted
from safe_result import safe
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

def safe_cbx_extension(ext: str) -> str:
    """Converts an archive extension to its comic book archive equivalent,
    and removes leading dot if any.

    Parameters
    ----------
    ext : str
        The extension to check.

    Returns
    -------
    str
        Archive extension

    Example
    -------

    >>> safe_cbx_extension(".JPEG")
    'jpeg'
    >>> safe_cbx_extension("rar")
    'cbr'
    >>> safe_cbx_extension(".7z")
    'cb7'
    >>> safe_cbx_extension(".zip")
    'cbz'
    >>> safe_cbx_extension(".tar")
    'cbt'
    >>> safe_cbx_extension("ace")
    'cba'
    """
    ext = ext.lower().strip()
    if ext[0] == ".":
        ext = ext[1:]

    match ext:
        case "zip":
            return "cbz"
        case "rar":
            return "cbr"
        case "tar":
            return "cbt"
        case "ace":
            return "cba"
        case "7z":
            return "cb7"
        case _:
            return ext


class ConvertResult(Enum):
    Copied = 0
    Converted = 1
    Skipped = 2

    def __str__(self):
        match self:
            case ConvertResult.Copied:
                return "Copied"
            case ConvertResult.Converted:
                return "Converted"
            case ConvertResult.Skipped:
                return "Skipped"


@safe
def cbx_convert(
    input: str,
    output: str,
    image_formats: list[str] | str | None = None,
    quality: int | None = None,
    max_size: int | None = None,
    skip_when_nothing_to_do: bool = False,
) -> ConvertResult:
    """Converts a cbz file into another file.
    If there is nothing to do, the file is simply copied to destination.

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
    skip_when_nothing_to_do : bool
        If True, Skips file when nothing to do, otherwise file is copied to destination.

    Returns
    -------
    ConvertResult
        Operation performed on file.
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
        input_magic_extension = safe_extension(puremagic.magic_file(input)[0].extension)

        images_modified = False

        match input_magic_extension:
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
                    tf.extractall(path=input_tempdir, filter="tar")
            case "cba" | "ace":
                with acefile.open(input, "r") as af:
                    af.extractall(path=input_tempdir)
            case _:
                raise RuntimeError(
                    f'Unrecognized magic extension "{input_magic_extension}"'
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
                image_filename_in_absolute = os.path.join(
                    input_tempdir, image_filename_in
                )

                image_modified = False

                with PIL.Image.open(image_filename_in_absolute) as img:
                    # .copy() loads the image into memory and detaches it from the physical file
                    # This is because on windows PIL keeps a handle on the file
                    image = img.copy()

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
                        image_modified = True

                image_file_ext_in = safe_extension(
                    os.path.splitext(image_filename_in)[1]
                )
                image_file_ext_out = image_file_ext_in
                if image_formats is not None and image_file_ext_in not in image_formats:
                    image_file_ext_out = image_formats[0]
                    image_modified = True

                image_filename_out = (
                    os.path.splitext(image_filename_in)[0] + "." + image_file_ext_out
                )

                # Only use quality argument if provided.
                quality_dict = {}
                if quality is not None:
                    image_modified = True
                    quality_dict = {"quality": quality}

                image_filename_out_absolute = os.path.join(
                    output_tempdir, image_filename_out
                )
                os.makedirs(os.path.dirname(image_filename_out_absolute), exist_ok=True)
                if image_modified:
                    if image_file_ext_out == "jpg":
                        image = image.convert("RGB")
                    image.save(
                        image_filename_out_absolute,
                        optimize=True,
                        **quality_dict,
                    )
                else:
                    shutil.copyfile(
                        image_filename_in_absolute, image_filename_out_absolute
                    )
                images_filenames_out.append(image_filename_out)
                images_modified = images_modified or image_modified
        else:
            shutil.copytree(input_tempdir, output_tempdir, dirs_exist_ok=True)
            images_filenames_out = images_filenames_in

        output_ext = safe_extension(os.path.splitext(output)[1])

        if images_modified or safe_cbx_extension(output_ext) != safe_cbx_extension(
            input_magic_extension
        ):
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
                    raise RuntimeError(f'Unsupported output format "{output_ext}"')
            return ConvertResult.Converted
        else:
            if skip_when_nothing_to_do:
                return ConvertResult.Skipped
            shutil.copyfile(input, output)
            return ConvertResult.Copied
