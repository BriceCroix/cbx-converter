import sys

try:
    from PySide6 import QtWidgets

    from .gui import MyWidget

    _has_pyside = True
except ImportError():
    _has_pyside = False

from . import cli


def main():
    if _has_pyside and len(sys.argv) == 1:
        app = QtWidgets.QApplication([])
        widget = MyWidget()
        widget.resize(800, 600)
        widget.show()
        sys.exit(app.exec())
    else:
        cli.main()


if __name__ == "__main__":
    main()
