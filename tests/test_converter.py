import filecmp
import os
import zipfile
from importlib import resources
from pathlib import Path

import PIL
import puremagic
import pytest

import tests as tests_package
from cbx_converter.converter import ConvertResult, cbx_convert


def get_asset(filename: str) -> str:
    return resources.files(tests_package).joinpath("assets", filename)

@pytest.mark.parametrize(
    "in_file",
    [
        "_dir.cb7",
        "_dir.cbt",
        "_dir.cbz",
        ".cb7",
        ".cbr",
        ".cbt",
        ".cbz",
    ],
)
@pytest.mark.parametrize(
    "out_fmt",
    [".cbz", ".cbt", ".cb7", ".pdf", ".epub"],
)
def test_convert_format(tmp_path, in_file, out_fmt):
    out = os.path.join(tmp_path, f"out{out_fmt}")
    res = cbx_convert(
        get_asset(f"bobby_make_believe_sample{in_file}"),
        out,
    )
    assert res.is_ok()
    assert (
        res.value == ConvertResult.Converted
        if out_fmt.split(".")[1] != in_file.split(".")[1]
        else ConvertResult.Copied
    )

    # puremagic flags epub as zip, which it is...
    if out_fmt != ".epub":
        assert puremagic.magic_file(out)[0].extension == out_fmt


@pytest.mark.parametrize(
    "out_fmt",
    [".cba", ".cbr"],
)
def test_convert_proprietary_format(tmp_path, out_fmt):
    out = os.path.join(tmp_path, f"out{out_fmt}")
    assert cbx_convert(
        get_asset("bobby_make_believe_sample.cb7"),
        out,
    ).is_err()


def test_convert_cbz_downscale(tmp_path):
    max_size = 100
    out = os.path.join(tmp_path, "out.cbz")
    res = cbx_convert(
        get_asset("bobby_make_believe_sample.cbz"),
        out,
        max_size=max_size,
    )
    assert res.is_ok()
    assert res.value == ConvertResult.Converted
    assert puremagic.magic_file(out)[0].extension == ".cbz"
    extract_dir = os.path.join(tmp_path, "extracted")
    os.makedirs(extract_dir)
    with zipfile.ZipFile(out, "r") as zf:
        zf.extractall(path=extract_dir)
    images_paths = [img for img in Path(extract_dir).rglob("*") if img.is_file()]
    for image_path in images_paths:
        img = PIL.Image.open(image_path)
        width, height = img.size
        assert max(width, height) == max_size


def test_convert_cbz_downscale_very_large(tmp_path):
    max_size = 1000000
    out = os.path.join(tmp_path, "out.cbz")
    res = cbx_convert(
        get_asset("bobby_make_believe_sample.cbz"),
        out,
        max_size=max_size,
    )
    assert res.is_ok()
    assert res.value == ConvertResult.Copied
    assert puremagic.magic_file(out)[0].extension == ".cbz"
    extract_dir = os.path.join(tmp_path, "extracted")
    os.makedirs(extract_dir)
    with zipfile.ZipFile(out, "r") as zf:
        zf.extractall(path=extract_dir)
    images_paths = [img for img in Path(extract_dir).rglob("*") if img.is_file()]
    for image_path in images_paths:
        img = PIL.Image.open(image_path)
        width, height = img.size
        assert max(width, height) < max_size


def test_convert_cbt_downgrade(tmp_path):
    asset = get_asset("bobby_make_believe_sample_dir.cbt")
    out = os.path.join(tmp_path, "out.cbt")
    res = cbx_convert(
        asset,
        out,
        image_formats="jpeg",
        quality=1,  # Very poor
    )
    assert res.is_ok()
    assert res.value == ConvertResult.Converted
    assert puremagic.magic_file(out)[0].extension == ".cbt"
    assert os.path.getsize(out) < os.path.getsize(asset)


def test_convert_cbr_to_cbz_with_gif(tmp_path):
    asset = get_asset("bobby_make_believe_sample.cbr")
    out = os.path.join(tmp_path, "out.cbz")
    res = cbx_convert(
        asset,
        out,
        image_formats=["gif", "png"],
    )
    assert res.is_ok()
    assert res.value == ConvertResult.Converted
    assert puremagic.magic_file(out)[0].extension == ".cbz"
    extract_dir = os.path.join(tmp_path, "extracted")
    os.makedirs(extract_dir)
    with zipfile.ZipFile(out, "r") as zf:
        zf.extractall(path=extract_dir)
    images_paths = [img for img in Path(extract_dir).rglob("*") if img.is_file()]
    for image_path in images_paths:
        assert puremagic.magic_file(image_path)[0].extension == ".gif"


def test_convert_bad_to_cbz(tmp_path):
    out = os.path.join(tmp_path, "out.cbz")
    assert cbx_convert(
        get_asset("README.md"),
        out,
    ).is_err()


def test_convert_cbz_to_bad(tmp_path):
    out = os.path.join(tmp_path, "absolutely.not")
    assert cbx_convert(
        get_asset("bobby_make_believe_sample_dir.cbz"),
        out,
    ).is_err()


@pytest.mark.parametrize(
    "in_file",
    [
        "_dir.cb7",
        "_dir.cbt",
        "_dir.cbz",
        ".cb7",
        ".cbr",
        ".cbt",
        ".cbz",
    ],
)
def test_convert_identic_copy(tmp_path, in_file):
    input = get_asset(f"bobby_make_believe_sample{in_file}")
    out = os.path.join(tmp_path, f"out.{in_file.split('.')[1]}")
    res = cbx_convert(input, out, image_formats="jpg")
    assert res.is_ok()
    assert res.value == ConvertResult.Copied
    assert filecmp.cmp(input, out)


@pytest.mark.parametrize(
    "in_file",
    [
        "_dir.cb7",
        "_dir.cbt",
        "_dir.cbz",
        ".cb7",
        ".cbr",
        ".cbt",
        ".cbz",
    ],
)
def test_convert_identic_skip(tmp_path, in_file):
    input = get_asset(f"bobby_make_believe_sample{in_file}")
    out = os.path.join(tmp_path, f"out.{in_file.split('.')[1]}")
    res = cbx_convert(input, out, image_formats="jpg", skip_when_nothing_to_do=True)
    assert res.is_ok()
    assert res.value == ConvertResult.Skipped
    assert not Path(out).exists()
