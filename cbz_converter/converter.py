import os
import tempfile
import zipfile

import img2pdf
import PIL


def cbz2pdf(
    input: str,
    output: str,
    image_format: str | None = None,
    quality: int | None = None,
    width: int | None = None,
    height: int | None = None,
) -> bool:
    """Converts a cbz file into another file.

    Parameters
    ----------
    input : str
        Path to a cbz file.
    output : str
        Path to file to be created.
    image_format : str | None (optional)
        If provided, the file format to be forced for each image in the cbz archive (jpg, png...).
    quality : int | None (optional)
        If provided, allows to lower the quality of the images (0 is worst, 100 is best).
        Only supported for file types : avif, jpg, webp.
    width : int | None (optional)
        If provided, images will be resized to this maximum width.
    height : int | None (optional)
        If provided, images will be resized to this maximum height.

    Returns
    -------
    bool
        True for success.
    """
    os.makedirs(os.path.dirname(output), exist_ok=True)
    with (
        zipfile.ZipFile(input, "r") as zf,
        tempfile.TemporaryDirectory() as tempdir,
        open(output, "wb") as out,
    ):
        try:
            zf.extractall(path=tempdir)
            images_filenames_in = [
                os.path.join(tempdir, filename)
                for filename in sorted(os.listdir(tempdir))
            ]
            images_filenames_out = []
            if (
                quality is not None
                or width is not None
                or height is not None
                or image_format is not None
            ):
                for image_filename_in in images_filenames_in:
                    image = PIL.Image.open(image_filename_in)

                    if width is not None or height is not None:
                        # Some images are rotated, work with that
                        image_width = min(image.size)
                        image_heigth = max(image.size)
                        ratio = min(
                            (width or image_width) / image_width,
                            (height or image_heigth) / image_heigth,
                        )
                        image = image.resize(
                            size=(int(image.width * ratio), int(image.height * ratio)),
                            resample=PIL.Image.Resampling.LANCZOS,
                        )

                    image_file_ext_in = os.path.splitext(image_filename_in)[1]
                    image_file_ext_out = image_format or image_file_ext_in
                    image_file_ext_out = image_file_ext_out.lower()

                    if image_file_ext_out[0] != '.':
                        image_file_ext_out = '.' + image_file_ext_out
                    if image_file_ext_out == ".jpeg":
                        image_file_ext_out = ".jpg"
                    if image_file_ext_in == ".jpeg":
                        image_file_ext_in = ".jpg"

                    if image_file_ext_out != image_file_ext_in:
                        image_filename_out = image_filename_in + image_file_ext_out
                    else:
                        image_filename_out = image_filename_in
                    
                    # Only use quality argument if provided.
                    quality_dict = {'quality':quality} if quality is not None else {}
                    image.save(
                        image_filename_out, optimize=True, **quality_dict
                    )
                    images_filenames_out.append(image_filename_out)
            else:
                images_filenames_out = images_filenames_in

            out.write(img2pdf.convert(images_filenames_out))
            return True
        except Exception as e:
            print(f"Error converting pdf : {e}")
            return False
