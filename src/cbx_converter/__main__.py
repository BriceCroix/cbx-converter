import sys

from . import cli


def main():
    if len(sys.argv) == 1:
        try:
            from PySide6 import QtWidgets

            from .gui import MyWidget

            app = QtWidgets.QApplication([])
            widget = MyWidget()
            widget.resize(800, 600)
            widget.show()
            sys.exit(app.exec())
        except ImportError() as _:
            cli.main()

    else:
        cli.main()


if __name__ == "__main__":
    main()
