from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTextEdit,
    QPushButton,
)


class TextEditWindow(QWidget):
    """
    A simple text edit window that emits the entered text when closed.

    Inherits
    -------
    `QWidget`

    Parameters
    ----------
    initial_text : `str`
        The initial text to display in the text edit area.
        Default is an empty string.

    Attributes
    -------
    user_text_emitter : `pyqtSignal`
        Signal emitted when the window is closed, carrying the entered text.
    """

    user_text_emitter = pyqtSignal(str)

    def __init__(self, initial_text: str = ""):
        super().__init__()
        layout = QVBoxLayout()

        self.init_text = initial_text
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(self.init_text)

        self.current_text = initial_text
        self.save_button = QPushButton("Save (not to file)")
        self.save_button.clicked.connect(self.save)

        layout.addWidget(self.text_edit)
        layout.addWidget(self.save_button)
        self.setLayout(layout)

    def save(self):
        """Copy the current text from the text edit area to the `self.current_text` attribute."""

        entered_text = self.text_edit.toPlainText()
        self.current_text = entered_text

    def closeEvent(self, event):
        """Emit the entered text when the window is closed."""

        self.user_text_emitter.emit(self.current_text)
        event.accept()
