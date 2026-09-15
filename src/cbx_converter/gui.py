import os
import sys
from pathlib import Path

from natsort import natsorted
from PySide6 import QtCore, QtWidgets

from .converter import ConvertResult, cbx_convert
from .file_pattern_parser import compute_output_path


class ConversionWorker(QtCore.QThread):
    """Background thread to handle the conversion process without freezing the GUI."""

    progress = QtCore.Signal(int)
    row_updated = QtCore.Signal(int, str, str)  # row index, status, size change

    def __init__(self, files, output_pattern, formats, quality, size, skip):
        super().__init__()
        self.files = files
        self.output_pattern = output_pattern
        self.formats = formats
        self.quality = quality
        self.size = size
        self.skip = skip

    def run(self):
        for i, i_file in enumerate(self.files):
            o_file = compute_output_path(i_file, self.output_pattern)

            try:
                res = cbx_convert(
                    i_file,
                    o_file,
                    image_formats=self.formats,
                    quality=self.quality,
                    max_size=self.size,
                    skip_when_nothing_to_do=self.skip,
                )

                if res.is_ok():
                    status = str(res.value)
                    if res.value != ConvertResult.Skipped:
                        in_size = os.path.getsize(i_file)
                        out_size = os.path.getsize(o_file)
                        size_change = f"{100.0 * out_size / in_size - 100:+.1f} %"
                    else:
                        size_change = "NA"
                else:
                    status = f"Error : {res.error}"
                    size_change = "NA"

            except Exception as e:
                status = f"Error : {e}"
                size_change = "NA"

            self.row_updated.emit(i, status, size_change)
            self.progress.emit(i + 1)


class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Comic Book Archive converter")
        self.files = []

        # --- UI Components ---

        # Input selection
        self.btn_select_file = QtWidgets.QPushButton("Select File")
        self.btn_select_dir = QtWidgets.QPushButton("Select Directory")
        self.lbl_input_path = QtWidgets.QLabel("No input selected")

        # Options matching cli.py arguments
        self.le_output = QtWidgets.QLineEdit("%F.pdf")
        self.le_output.setPlaceholderText("%F.pdf")
        self.le_output.setToolTip("""The output file pattern. Extension must be provided.

Supported matchers are :
- `%f` : The file stem (`/tmp/dir/myfile.cbz` -> `myfile`)
- `%F` : The file stem with path (`/tmp/dir/myfile.cbz` -> `/tmp/dir/myfile`)
- `%e` : The file extension (`/tmp/dir/myfile.cbz` -> `cbz`)
- `%p` : The file parent only (`/tmp/dir/myfile.cbz` -> `dir`)
- `%P` : The file parent whole path (`/tmp/dir/myfile.cbz` -> `/tmp/dir`)
- `%Q` : The file parent's parent whole path (`/tmp/dir/myfile.cbz` -> `/tmp`)

Examples :
- `%F.pdf`
- `%Q/%p-converted/%f.cbz`""")
        self.le_format = QtWidgets.QLineEdit("")
        self.le_format.setPlaceholderText("jpg,png")
        self.le_format.setToolTip(
            """Comma-separated list of accepted image formats in the comic book archives (jpg, png, etc...).
If an image format that is not in the list is encountered, the image will be converted to the first format in this list."""
        )

        self.sb_quality = QtWidgets.QSpinBox()
        self.sb_quality.setRange(-1, 100)
        self.sb_quality.setSpecialValueText("Default")
        self.sb_quality.setValue(-1)
        self.sb_quality.setToolTip(
            "Integer between 0 (lowest) and 100 (highest) to downgrade the quality "
            "of images (jpg default is 75)."
        )

        self.sb_size = QtWidgets.QSpinBox()
        self.sb_size.setRange(-1, 99999)
        self.sb_size.setSpecialValueText("No limit")
        self.sb_size.setValue(-1)
        self.sb_size.setToolTip("Maximum width and height of images.")

        self.cb_ignore = QtWidgets.QCheckBox(
            "Skip copying files to destination when nothing to do"
        )

        # Table and Progress
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            ["Input file", "Output file", "Status", "File size change"]
        )
        self.table.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Stretch
        )

        self.btn_convert = QtWidgets.QPushButton("Start Conversion")
        self.btn_convert.setEnabled(False)
        self.progress_bar = QtWidgets.QProgressBar()
        self.reset_progress_bar()

        # --- Layout setup ---
        layout = QtWidgets.QVBoxLayout(self)

        input_layout = QtWidgets.QHBoxLayout()
        input_layout.addWidget(self.btn_select_file)
        input_layout.addWidget(self.btn_select_dir)
        input_layout.addWidget(self.lbl_input_path, 1)
        layout.addLayout(input_layout)

        form_layout = QtWidgets.QFormLayout()

        label = QtWidgets.QLabel("Output Pattern:")
        label.setToolTip(self.le_output.toolTip())
        form_layout.addRow(label, self.le_output)

        label = QtWidgets.QLabel("Image Formats:")
        label.setToolTip(self.le_format.toolTip())
        form_layout.addRow(label, self.le_format)

        label = QtWidgets.QLabel("Quality (0-100):")
        label.setToolTip(self.sb_quality.toolTip())
        form_layout.addRow(label, self.sb_quality)

        label = QtWidgets.QLabel("Max Size:")
        label.setToolTip(self.sb_size.toolTip())
        form_layout.addRow(label, self.sb_size)

        layout.addLayout(form_layout)

        layout.addWidget(self.cb_ignore)
        layout.addWidget(self.table)
        layout.addWidget(self.btn_convert)
        layout.addWidget(self.progress_bar)

        # --- Signal Connections ---
        self.btn_select_file.clicked.connect(self.select_file)
        self.btn_select_dir.clicked.connect(self.select_directory)
        self.le_output.textChanged.connect(self.update_table_preview)
        self.btn_convert.clicked.connect(self.start_conversion)

    def select_file(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select CBX File")
        if file_path:
            self.lbl_input_path.setText(file_path)
            self.files = [Path(file_path)]
            self.update_table_preview()
            self.reset_progress_bar()

    def select_directory(self):
        dir_path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory")
        if dir_path:
            self.lbl_input_path.setText(dir_path)
            # Find files matching the pattern as in cli.py
            self.files = natsorted(Path(dir_path).rglob("*.[cC][bB][zZrRaAtT7]"))
            self.update_table_preview()
            self.reset_progress_bar()

    def update_table_preview(self):
        self.table.setRowCount(len(self.files))
        pattern = self.le_output.text()

        for i, i_file in enumerate(self.files):
            o_file = compute_output_path(i_file, pattern)

            item = QtWidgets.QTableWidgetItem(str(i_file))
            item.setToolTip(str(i_file))
            self.table.setItem(i, 0, item)

            item = QtWidgets.QTableWidgetItem(str(o_file))
            item.setToolTip(str(o_file))
            self.table.setItem(i, 1, item)

            self.table.setItem(i, 2, QtWidgets.QTableWidgetItem("Pending"))
            self.table.setItem(i, 3, QtWidgets.QTableWidgetItem("-"))

        self.btn_convert.setEnabled(len(self.files) > 0)

    def start_conversion(self):
        self.btn_convert.setEnabled(False)
        self.reset_progress_bar()

        # Parse arguments mapped from CLI
        formats_text = self.le_format.text()
        formats = (
            [f.strip().lower() for f in formats_text.split(",")]
            if formats_text
            else None
        )
        quality = self.sb_quality.value() if self.sb_quality.value() != -1 else None
        size = self.sb_size.value() if self.sb_size.value() != -1 else None

        self.worker = ConversionWorker(
            files=self.files,
            output_pattern=self.le_output.text(),
            formats=formats,
            quality=quality,
            size=size,
            skip=self.cb_ignore.isChecked(),
        )

        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.row_updated.connect(self.update_table_row)
        self.worker.finished.connect(self.conversion_finished)
        self.worker.start()

    def reset_progress_bar(self):
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(len(self.files) if len(self.files) != 0 else 1)
        self.progress_bar.setValue(0)

    def update_table_row(self, row, status, size_change):
        self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(status))
        self.table.setItem(row, 3, QtWidgets.QTableWidgetItem(size_change))

    def conversion_finished(self):
        self.btn_convert.setEnabled(True)
        QtWidgets.QMessageBox.information(
            self, "Finished", "Conversion process completed."
        )


def main():
    app = QtWidgets.QApplication(sys.argv)
    widget = MainWindow()
    widget.resize(900, 600)
    widget.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
