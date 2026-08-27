# CBZ converter

Simple module to convert Comic Book Archives (`.cbz`/`.cbr`/`.cbt`/`.cba`/`.cb7`) files to pdf or to
different archive types.

Can also be used to lower the size of files (by down-scaling and/or degrading quality) and/or to
convert images in cbx file to other format (for instance if your reader does not support cbx
containing `webp` images).

## How to use

```bash
uv run cbz_converter <CBX> [--output <OUT>]
```

- `<CBX>` can either be a `.cbz`/`.cbr`/`.cbt`/`.cba`/`.cb7` file or a directory containing files.
- `<OUT>` (optional) the file to create, or a file pattern to use when parsing a directory.

Use the following to learn about all options :

```bash
uv run cbz_converter --help
```
