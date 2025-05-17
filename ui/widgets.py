from PyQt6.QtWidgets import QWidget, QLabel, QComboBox, QLineEdit, QHBoxLayout

class LabeledComboBox(QWidget):
    def __init__(self, label_text, items, parent=None):
        super().__init__(parent)
        self.label = QLabel(label_text)
        self.combo = QComboBox()
        self.combo.addItems(items)
        layout = QHBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.combo)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def current_text(self):
        return self.combo.currentText()

class LabeledLineEdit(QWidget):
    def __init__(self, label_text, default_text="", parent=None):
        super().__init__(parent)
        self.label = QLabel(label_text)
        self.line_edit = QLineEdit()
        self.line_edit.setText(default_text)
        layout = QHBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.line_edit)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def text(self):
        return self.line_edit.text()
