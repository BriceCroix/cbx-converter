import argparse
import os
from pathlib import Path

from natsort import natsorted
from tqdm import tqdm

from .converter import cbz_convert
from .file_pattern_parser import compute_output_path


def main():
    parser = argparse.ArgumentParser(
        description="CBZ converter CLI", formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "cbz",
        help="Input cbz file, or directory containing cbz files, that will be scanned recursively.",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="%F.pdf",
        help="""Output file pattern. Extension must be provided.

Supported matchers are :
- `%%f` : The file stem (`/tmp/dir/myfile.cbz` -> `myfile`)
- `%%F` : The file stem with path (`/tmp/dir/myfile.cbz` -> `/tmp/dir/myfile`)
- `%%e` : The file extension (`/tmp/dir/myfile.cbz` -> `cbz`)
- `%%p` : The file parent only (`/tmp/dir/myfile.cbz` -> `dir`)
- `%%P` : The file parent whole path (`/tmp/dir/myfile.cbz` -> `/tmp/dir`)
- `%%Q` : The file parent's parent whole path (`/tmp/dir/myfile.cbz` -> `/tmp`)

Examples :
- `%%F.pdf`
- `%%Q/%%p-converted/%%f.cbz`""",
    )

    parser.add_argument(
        "-f",
        "--format",
        help="Comma-separated list of accepted image formats in the comic book archives (jpg, png, "
        "etc...). If an image format that is not in the list is encountered, the image will be "
        "converted to the first format in this list.",
        type=str,
    )

    parser.add_argument(
        "-q",
        "--quality",
        help="Integer between 0 (lowest) and 100 (highest) to downgrade the quality "
        "of images (jpg default is 75).",
        type=int,
    )
    parser.add_argument(
        "-s", "--size", help="Maximum width and height of images.", type=int
    )
    args = parser.parse_args()

    if os.path.isfile(args.cbz):
        files = [args.cbz]
    else:
        files = natsorted(Path(args.cbz).rglob("*.[cC][bB][zZrRaAtT7]"))

    for i_file in (pbar := tqdm(files)):
        pbar.set_postfix_str(i_file)
        o_file = compute_output_path(i_file, args.output)
        if not cbz_convert(
            i_file,
            o_file,
            image_formats=[f.strip().lower() for f in args.format.split(",")],
            quality=args.quality,
            max_size=args.size,
        ):
            print(f"ERROR on converting {i_file} to {o_file}")
