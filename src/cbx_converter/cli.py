import argparse
import os
from pathlib import Path

from natsort import natsorted
from prettytable import PrettyTable
from tqdm import tqdm

from .converter import ConvertResult, cbx_convert
from .file_pattern_parser import compute_output_path


def main():
    parser = argparse.ArgumentParser(
        description="CBX converter CLI", formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "cbx",
        help="Input cbz, cbr, cbt, cba, or cb7 file, or directory containing cbx files, that will be scanned recursively.",
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
    parser.add_argument(
        "-i",
        "--ignore",
        "--skip",
        help="Skip copying files to destination when nothing to do.",
        action="store_true",
    )
    args = parser.parse_args()

    if os.path.isfile(args.cbx):
        files = [args.cbx]
    else:
        files = natsorted(Path(args.cbx).rglob("*.[cC][bB][zZrRaAtT7]"))

    table = PrettyTable()
    table.field_names = ["Input file", "Output file", "Status", "File size change"]
    for i_file in (pbar := tqdm(files)):
        pbar.set_postfix_str(str(i_file))
        o_file = compute_output_path(i_file, args.output)

        res = cbx_convert(
            i_file,
            o_file,
            image_formats=[f.strip().lower() for f in args.format.split(",")]
            if args.format is not None
            else None,
            quality=args.quality,
            max_size=args.size,
            skip_when_nothing_to_do=args.ignore,
        )
        table.add_row(
            [
                i_file,
                o_file,
                str(res.value) if res.is_ok() else f"Error : {res.error}",
                f"{100.0 * os.path.getsize(o_file) / os.path.getsize(i_file) - 100:+.1f} %"
                if res.is_ok() and res.value != ConvertResult.Skipped
                else "NA",
            ]
        )
    print(table)
