import os
import zipfile
from importlib import resources
from pathlib import Path

import PIL
import puremagic

import tests as tests_package
from cbz_converter.converter import cbz_convert


def get_asset(filename: str) -> str:
    return resources.files(tests_package).joinpath("assets", filename)


def test_convert_cb7_to_cbz(tmp_path):
    out = os.path.join(tmp_path, "out.cbz")
    assert cbz_convert(
        get_asset("bobby_make_believe_sample.cb7"),
        out,
    )
    assert puremagic.magic_file(out)[0].extension == ".cbz"


def test_convert_cb7_to_cbt(tmp_path):
    out = os.path.join(tmp_path, "out.cbt")
    assert cbz_convert(
        get_asset("bobby_make_believe_sample.cb7"),
        out,
    )
    assert puremagic.magic_file(out)[0].extension == ".cbt"


def test_convert_cb7_to_cbr(tmp_path):
    out = os.path.join(tmp_path, "out.cbr")
    assert not cbz_convert(
        get_asset("bobby_make_believe_sample.cb7"),
        out,
    )


def test_convert_cb7_to_cba(tmp_path):
    out = os.path.join(tmp_path, "out.cba")
    assert not cbz_convert(
        get_asset("bobby_make_believe_sample.cb7"),
        out,
    )


def test_convert_cb7_to_pdf(tmp_path):
    out = os.path.join(tmp_path, "out.pdf")
    assert cbz_convert(
        get_asset("bobby_make_believe_sample_dir.cb7"),
        out,
    )
    assert puremagic.magic_file(out)[0].extension == ".pdf"


def test_convert_cbz_downscale(tmp_path):
    max_size = 100
    out = os.path.join(tmp_path, "out.cbz")
    assert cbz_convert(
        get_asset("bobby_make_believe_sample.cbz"),
        out,
        max_size=max_size,
    )
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


def test_convert_cbt_downgrade(tmp_path):
    asset = get_asset("bobby_make_believe_sample_dir.cbt")
    out = os.path.join(tmp_path, "out.cbt")
    assert cbz_convert(
        asset,
        out,
        image_formats="jpeg",
        quality=1,  # Very poor
    )
    assert puremagic.magic_file(out)[0].extension == ".cbt"
    assert os.path.getsize(out) < os.path.getsize(asset)


def test_convert_cbr_to_cbz_with_gif(tmp_path):
    asset = get_asset("bobby_make_believe_sample.cbr")
    out = os.path.join(tmp_path, "out.cbz")
    assert cbz_convert(
        asset,
        out,
        image_formats=["gif", "png"],
    )
    assert puremagic.magic_file(out)[0].extension == ".cbz"
    extract_dir = os.path.join(tmp_path, "extracted")
    os.makedirs(extract_dir)
    with zipfile.ZipFile(out, "r") as zf:
        zf.extractall(path=extract_dir)
    images_paths = [img for img in Path(extract_dir).rglob("*") if img.is_file()]
    for image_path in images_paths:
        assert puremagic.magic_file(image_path)[0].extension == ".gif"

def test_convert_cbz_to_cb7_do_all(tmp_path):
    asset = get_asset("bobby_make_believe_sample_dir.cbz")
    out = os.path.join(tmp_path, "out.cb7")
    assert cbz_convert(
        asset,
        out,
        image_formats=["png", "webp"],
        quality=10,
        max_size=200,
    )
    assert puremagic.magic_file(out)[0].extension == ".cb7"


def test_convert_bad_to_cbz(tmp_path):
    out = os.path.join(tmp_path, "out.cbz")
    assert not cbz_convert(
        get_asset("README.md"),
        out,
    )


def test_convert_cbz_to_bad(tmp_path):
    out = os.path.join(tmp_path, "absolutely.not")
    assert not cbz_convert(
        get_asset("bobby_make_believe_sample_dir.cbz"),
        out,
    )