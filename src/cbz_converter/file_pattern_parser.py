import os
import re
from pathlib import Path


def compute_output_path(input_path: str, output_path_pattern: str = "%F.pdf") -> str:
    """Computes the output path according to given pattern.

    Supported matchers are :
    - `%f` : The file stem (`/tmp/dir/myfile.cbz` -> `myfile`)
    - `%F` : The file stem with path (`/tmp/dir/myfile.cbz` -> `/tmp/dir/myfile`)
    - `%e` : The file extension (`/tmp/dir/myfile.cbz` -> `cbz`)
    - `%p` : The file parent only (`/tmp/dir/myfile.cbz` -> `dir`)
    - `%P` : The file parent whole path (`/tmp/dir/myfile.cbz` -> `/tmp/dir`)
    - `%Q` : The file parent's parent whole path (`/tmp/dir/myfile.cbz` -> `/tmp`)

    Parameters
    ----------
    output_path_pattern : str
        The output path pattern
    input_path : str
        The input path.

    Returns
    -------
    str
        Output path pattern with matchers replaced.

    Examples
    --------

    >>> compute_output_path("/home/dir/myfile.cbz", "%F.pdf")
    '/home/dir/myfile.pdf'
    >>> compute_output_path("/home/dir/myfile.cbz", "%P/%p-%f.pdf")
    '/home/dir/dir-myfile.pdf'
    >>> compute_output_path("/home/dir/myfile.cbz", "%P-converted/%f.%e.pdf")
    '/home/dir-converted/myfile.cbz.pdf'
    >>> compute_output_path("/home/documents/dir/myfile.cbz", "%Q-converted/%p/%f.pdf")
    '/home/documents-converted/dir/myfile.pdf'
    """
    path = Path(os.path.abspath(input_path))

    # Map the matchers to their corresponding path components
    replacements = {
        "%f": path.stem,
        "%F": str(path.parent / path.stem),
        "%e": path.suffix[1:] if path.suffix else "",
        "%p": path.parent.name,
        "%P": str(path.parent),
        "%Q": str(path.parent.parent),
    }

    # Compile a regex pattern to match any of the defined tokens safely in a single pass
    pattern = re.compile("|".join(re.escape(key) for key in replacements))

    # Perform the substitution using a lookup lambda function
    return pattern.sub(lambda match: replacements[match.group(0)], output_path_pattern)


if __name__ == "__main__":
    import doctest

    doctest.testmod()
