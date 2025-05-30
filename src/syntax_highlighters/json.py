from PyQt5.QtCore import QRegularExpression
from PyQt5.QtGui import QSyntaxHighlighter, QTextCharFormat, QFont, QColor


class JsonHighlighter(QSyntaxHighlighter):
    """
    A syntax highlighter for JSON text.

    Inherits
    -------
    `QSyntaxHighlighter`
    """

    def __init__(self, parent=None) -> None:
        super(JsonHighlighter, self).__init__(parent)

        yellow = QColor("#ffd866")
        purple = QColor("#ab9df2")
        blue = QColor("#78dce8")
        white = QColor("#f8f8f2")

        self.pattern = QRegularExpression(
            r'(?P<key>"(?:\\\\.|[^"\\])*"(?=\s*:))|'
            r'(?P<string>"(?:\\\\.|[^"\\])*")|'
            r"(?P<number>-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?)|"
            r"(?P<keyword>true|false|null)|"
            r"(?P<punct>[{}\[\],:])"
        )

        self.formats = {
            "key": self.create_format(white, QFont.Normal),
            "string": self.create_format(yellow, QFont.Normal),
            "number": self.create_format(purple, QFont.Normal),
            "keyword": self.create_format(blue, QFont.Normal),
            "punct": self.create_format(white, QFont.Normal),
        }

    def create_format(self, color: QColor, weight: QFont.Weight) -> QTextCharFormat:
        """
        Create a `QTextCharFormat` with the specified color and font weight.

        Parameters
        ----------
        color
            The color to set for the text format.
        weight
            The font weight to set for the text format.

        Returns
        -------
        `QTextCharFormat`
            A text format with the specified color and font weight.
        """

        fmt = QTextCharFormat()
        fmt.setForeground(color)
        fmt.setFontWeight(weight)
        return fmt

    def highlightBlock(self, text: str) -> None:
        """
        Highlight the text block using the defined patterns and formats.

        Parameters
        ----------
        text
            The text block to highlight.
        """

        iterator = self.pattern.globalMatch(text)
        while iterator.hasNext():
            match = iterator.next()

            for name, fmt in self.formats.items():
                start = match.capturedStart(name)
                if start >= 0:
                    length = match.capturedLength(name)
                    self.setFormat(start, length, fmt)
                    break
