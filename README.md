# CBZ converter

Simple module to convert cbz files to pdf or to different cbz.

Can also be used to lower the size of files (by down-scaling and/or degrading quality) and/or to convert
images in cbz file to other format (for instance if your reader does not support cbz containing
`webp` images).

## How to use

```bash
uv run cbz_converter <CBZ> [--output <OUT>]
```

- `<CBZ>` can either be a `.cbz` file or a directory containing `.cbz` files.
- `<OUT>` (optional) the file to create, or a file pattern to use when parsing a directory.

Use the following to learn about all options :

```bash
uv run cbz_converter --help
```
