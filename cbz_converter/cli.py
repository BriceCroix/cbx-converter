import argparse
import os
from pathlib import Path

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
        help="Image format to be forced on each image (jpg, png...). Can be useful when creating cbz"
        " but target device does not support all image types (e.g webp).",
        type=str,
    )

    parser.add_argument(
        "-q",
        "--quality",
        help="Integer between 0 (lowest) and 100 (highest) to downgrade the quality "
        "of images.",
        type=int,
    )
    parser.add_argument(
        "-W", "--width", help="Maximum width of output in pixels.", type=int
    )
    parser.add_argument(
        "-H", "--height", help="Maximum height of output in pixels.", type=int
    )
    args = parser.parse_args()

    if os.path.isfile(args.cbz):
        files = [args.cbz]
    else:
        files = sorted(list(Path(args.cbz).rglob("*.[cC][bB][zZ]")))

    for i_file in files:
        o_file = compute_output_path(i_file, args.output)
        print(f"Creating {o_file}... ", end="", flush=True)
        if cbz_convert(
            i_file,
            o_file,
            image_format=args.format,
            quality=args.quality,
            width=args.width,
            height=args.height,
        ):
            print("Done !")
        else:
            print("ERROR !")
