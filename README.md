# CBX converter

Simple module/executable to convert Comic Book Archive files (`.cbz`/`.cbr`/`.cbt`/`.cba`/`.cb7`)
to pdf or to different archive types.

Can also be used to lower the size of files (by down-scaling and/or degrading quality) and/or to
convert images in cbx file to other format (for instance if your reader does not support cbx
containing `webp` images).

A GUI is available when no argument is provided in the CLI.

## Features

- Can convert from types :
  - `cbz` (comic book `zip`)
  - `cbr` (comic book `rar`)
  - `cbt` (comic book `tar`)
  - `cba` (comic book `ace`)
  - `cb7` (comic book `7z`)
- Can convert to types :
  - `cbz`
  - `cbt`
  - `cb7`
  - `pdf` (with no additional size than the contained images)
- Can convert internal images from and to any type supported by [`pillow`](https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html)
- Can compress/downscale internal images to gain some space (loss of quality)

## Install

Standalone executables are available [in the release section here](https://github.com/BriceCroix/cbx-converter/releases/).

Otherwise the app can be run from this repository using [`uv`](https://docs.astral.sh/uv/).

If you want to enable the GUI, be sure to run `uv sync --all-extras` beforehand.

## How to use

### Command-line interface

```bash
uv run cbx_converter <CBX> [--output <OUT>]
```

- `<CBX>` can either be a `.cbz`/`.cbr`/`.cbt`/`.cba`/`.cb7` file or a directory containing files.
- `<OUT>` (optional) the file to create, or a file pattern to use when parsing a directory.

Many other options are available on the command line, use the following to learn about all of them :

```bash
uv run cbx_converter --help
```

### User interface (GUI)

If you want to enable the GUI, be sure to run `uv sync --all-extras` beforehand. The GUI is enabled
by default on releases.

The GUI will pop up automatically when no argument is provided.

```bash
uv run cbx_converter
```
