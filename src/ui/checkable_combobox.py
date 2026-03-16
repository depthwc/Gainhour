from PySide6.QtWidgets import QComboBox, QStyledItemDelegate
from PySide6.QtCore import Qt, Signal, QEvent
from PySide6.QtGui import QStandardItemModel, QStandardItem, QFontMetrics
from PySide6.QtGui import QStandardItemModel, QStandardItem, QFontMetrics

class CheckableComboBox(QComboBox):
    selectionChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(False)
        self.model_ = QStandardItemModel(self)
        self.setModel(self.model_)
        
        self.view().viewport().installEventFilter(self)
        self.view().pressed.connect(self.handleItemPressed)
        self._updating = False
        self._is_popup_open = False

    def eventFilter(self, obj, event):
        if obj == self.view().viewport():
            if event.type() == QEvent.MouseButtonRelease:
                return True
            if event.type() == QEvent.MouseButtonPress:
                return False
        return super().eventFilter(obj, event)

    def handleItemPressed(self, index):
        item = self.model_.itemFromIndex(index)
        if item.checkState() == Qt.Checked:
            item.setCheckState(Qt.Unchecked)
        else:
            item.setCheckState(Qt.Checked)
        self.updateText()
        self.selectionChanged.emit()

    def updateText(self):
        checked_items = self.get_checked_items()
        if self._is_popup_open:
            return

        if not checked_items:
            self.setEditable(True)
            self.lineEdit().setReadOnly(True)
            self.lineEdit().setText("Select Apps...")
            self.setToolTip("None selected")
            return
            
        text = ", ".join(checked_items)
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        self.lineEdit().setText(text)
        self.setToolTip(text)

    def add_item(self, text, checked=False):
        item = QStandardItem(text)
        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
        item.setData(Qt.Checked if checked else Qt.Unchecked, Qt.CheckStateRole)
        self.model_.appendRow(item)
        if not self._updating:
            self.updateText()

    def clear(self):
        self.model_.clear()
        if not self._updating:
            self.updateText()

    def get_checked_items(self):
        checked = []
        for i in range(self.model_.rowCount()):
            item = self.model_.item(i)
            if item.checkState() == Qt.Checked:
                checked.append(item.text())
        return checked

    def set_items(self, items, initial_checked=None):
        if self._is_popup_open:
            return
            
        if initial_checked is not None:
            current_checked = initial_checked
        else:
            current_checked = self.get_checked_items()
        
        self._updating = True
        self.clear()
        for item_text in sorted(items):
            self.add_item(item_text, checked=(item_text in current_checked))
        self._updating = False
        
        self.updateText()

    def showPopup(self):
        self._is_popup_open = True
        super().showPopup()
        
    def hidePopup(self):
        self._is_popup_open = False
        super().hidePopup()
        self.updateText()
