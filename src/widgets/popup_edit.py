from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QSyntaxHighlighter, QFontMetrics, QFontDatabase
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTextEdit,
    QPushButton,
)
from typing import Optional


class TextEditWindow(QWidget):
    """
    A simple text edit window that emits the entered text when closed.

    Inherits
    -------
    `QWidget`

    Parameters
    ----------
    highlighter : `Optional[QSyntaxHighlighter]`
        An optional syntax highlighter to apply to the text edit area.
        If not provided, no syntax highlighting will be applied.

    initial_text : `str`
        The initial text to display in the text edit area.
        Default is an empty string.

    tab_width : `int`
        The width of a tab character in spaces. Default is 4.

    font_size : `int`
        The font size for the text edit area. Default is 14.

    Attributes
    -------
    user_text_emitter : `pyqtSignal`
        Signal emitted when the window is closed, carrying the entered text.
    """

    user_text_emitter = pyqtSignal(str)

    def __init__(
        self,
        highlighter: Optional[QSyntaxHighlighter],
        initial_text: str = "",
        tab_width: int = 4,
        font_size: int = 14,
    ) -> None:
        super().__init__()
        layout = QVBoxLayout()

        self.init_text = initial_text
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(self.init_text)

        # have to use monospace font so that tab width is consistent
        self.font = QFontDatabase.systemFont(QFontDatabase.FixedFont)

        self.font_size = font_size
        self.update_font()

        self.tab_width = tab_width
        self.update_tab_stop()

        if highlighter is not None:
            if issubclass(highlighter, QSyntaxHighlighter):
                self.highlighter = highlighter(self.text_edit.document())
            else:
                raise TypeError("Highlighter must be a subclass of QSyntaxHighlighter")

        self.current_text = initial_text
        self.save_button = QPushButton("Save (not to file)")
        self.save_button.clicked.connect(self.save)

        layout.addWidget(self.text_edit)
        layout.addWidget(self.save_button)
        self.setLayout(layout)

    def update_font(self) -> None:
        """Set a larger font size while preserving other font properties"""
        self.font.setPointSize(self.font_size)
        self.text_edit.setFont(self.font)

    def update_tab_stop(self) -> None:
        """Update tab stop distance based on current font and tab width"""
        font_metrics = QFontMetrics(self.text_edit.font())
        space_width = font_metrics.horizontalAdvance(" ")
        tab_stop = self.tab_width * space_width
        self.text_edit.setTabStopDistance(tab_stop)

    def save(self) -> None:
        entered_text = self.text_edit.toPlainText()
        self.current_text = entered_text

    def closeEvent(self, event) -> None:
        self.user_text_emitter.emit(self.current_text)
        event.accept()
