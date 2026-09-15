import sys

from . import cli


def main():
    if len(sys.argv) == 1:
        try:
            from . import gui

            gui.main()
        except (ImportError, ModuleNotFoundError) as _:
            cli.main()

    else:
        cli.main()


if __name__ == "__main__":
    main()
