from pathlib import Path

from cbx_converter.file_pattern_parser import compute_output_path


def test_compute_output_path():
    assert compute_output_path("/home/dir/myfile.cbz", "%F.pdf") == Path(
        "/home/dir/myfile.pdf"
    )
    assert compute_output_path("/home/dir/myfile.cbz", "%P/%p-%f.pdf") == Path(
        "/home/dir/dir-myfile.pdf"
    )
