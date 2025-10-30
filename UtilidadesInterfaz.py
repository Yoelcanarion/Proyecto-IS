from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import QAbstractTableModel, Qt
from PyQt6.QtGui import QBrush, QColor, QFont
from PyQt6 import QtWidgets, QtCore, QtGui
import pandas as pd

class Mensajes:
    """
    Clase de utilidad que agrupa la creación de diálogos emergentes comunes.
    Se usan métodos estáticos para no tener que crear una instancia de la clase.
    """
    
    @staticmethod
    def crearAdvertencia(parent, titulo, mensaje):
        """
        Muestra un diálogo de advertencia.

        Args:
            parent (QWidget): El widget padre sobre el cual se mostrará el diálogo.
            titulo (str): El título de la ventana de diálogo.
            mensaje (str): El texto principal que se mostrará en el diálogo.
        """
        dlg = QMessageBox(parent)
        dlg.setWindowTitle(titulo)
        dlg.setText(mensaje)
        dlg.setStandardButtons(QMessageBox.StandardButton.Ok)
        dlg.setIcon(QMessageBox.Icon.Warning)
        dlg.exec()
    
    def crearEncuestaAlUsuario(parent, titulo, mensaje, funcionContinuar):
        """
        Muestra un diálogo de advertencia.

        Args:
            parent (QWidget): El widget padre sobre el cual se mostrará el diálogo.
            titulo (str): El título de la ventana de diálogo.
            mensaje (str): El texto principal que se mostrará en el diálogo.
            funcionContinuar (function): Función a ejecutar si el usuario elige continuar.
        """
        dlg = QMessageBox(parent)
        dlg.setIcon(QMessageBox.Icon.Warning)
        dlg.setWindowTitle(titulo)
        dlg.setText(mensaje)
        dlg.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.No)
        respuesta = dlg.exec()
        if respuesta == QMessageBox.StandardButton.Ok:
            funcionContinuar()
        else: 
            return


    @staticmethod
    def crearInformacion(parent, titulo, mensaje):
        """
        Muestra un diálogo de información.

        Args:
            parent (QWidget): El widget padre sobre el cual se mostrará el diálogo.
            titulo (str): El título de la ventana de diálogo.
            mensaje (str): El texto principal que se mostrará en el diálogo.
        """
        dlg = QMessageBox(parent)
        dlg.setWindowTitle(titulo)
        dlg.setText(mensaje)
        dlg.setStandardButtons(QMessageBox.StandardButton.Ok)
        dlg.setIcon(QMessageBox.Icon.Information)
        dlg.exec()


class PandasModel(QAbstractTableModel):
    def __init__(self, df):
        super().__init__()
        self.df = df

    def rowCount(self, parent=None):
        return len(self.df)

    def columnCount(self, parent=None):
        return len(self.df.columns)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.ItemDataRole.DisplayRole:
            return str(self.df.iat[index.row(), index.column()])
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return str(self.df.columns[section])
            else:
                return str(self.df.index[section])
        return None


class PandasModelConColor(QAbstractTableModel):
    """
    Modelo extendido de PandasModel que permite colorear columnas específicas 
    y tachar valores NaN visualmente.
    """
    def __init__(self, df, columna_verde=None, columna_roja=None, tachar_nan=False):
        super().__init__()
        self.df = df
        # Convertir columna_verde a lista si es string
        if isinstance(columna_verde, str):
            self.columna_verde = [columna_verde]
        else:
            self.columna_verde = columna_verde if columna_verde is not None else []
        
        self.columna_roja = columna_roja
        self.tachar_nan = tachar_nan

    def rowCount(self, parent=None):
        return len(self.df)

    def columnCount(self, parent=None):
        return len(self.df.columns)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        
        valor = self.df.iat[index.row(), index.column()]
        
        if role == Qt.ItemDataRole.DisplayRole:
            # Mostrar el valor (incluso si es NaN)
            return str(valor)
        
        # Color de fondo para las columnas seleccionadas
        elif role == Qt.ItemDataRole.BackgroundRole:
            col_name = self.df.columns[index.column()]
            if col_name in self.columna_verde:
                return QBrush(QColor(144, 238, 144))  # Verde claro
            elif col_name == self.columna_roja:
                return QBrush(QColor(255, 182, 193))  # Rojo claro
        
        # Tachar los valores NaN si la opción está activada
        elif role == Qt.ItemDataRole.FontRole:
            if self.tachar_nan and pd.isna(valor):
                font = QFont()
                font.setStrikeOut(True)
                return font
        
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return str(self.df.columns[section])
            else:
                return str(self.df.index[section])
        return None
    

class CheckableComboBox(QtWidgets.QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # --- Configuración Base ---
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        
        # Usamos un QListView para tener control total sobre el desplegable
        self.view = QtWidgets.QListView(self)
        self.setView(self.view)
        
        self.model = QtGui.QStandardItemModel(self)
        self.setModel(self.model)
        
        # --- Lógica de Eventos para Mejorar la UX ---
        
        # 1. ABRIR DESPLEGABLE AL CLICAR EN CUALQUIER PARTE
        # Instalamos un filtro de eventos sobre el QLineEdit interno.
        # Esto nos permitirá capturar los clics sobre él.
        self.lineEdit().installEventFilter(self)

        # 2. CERRAR EL DESPLEGABLE AL CLICAR FUERA
        # Instalamos un filtro sobre la vista desplegable (el QListView).
        self.view.installEventFilter(self)
        
        # --- Conexiones y Estado Inicial ---
        self.model.dataChanged.connect(self.updateText)
        self._keepPopupOpen = False # Flag para controlar el cierre del desplegable
        self.updateText() # Establecer texto inicial

    def eventFilter(self, objectWatched, event):
        """
        El corazón de la nueva funcionalidad. Este método intercepta
        eventos de los widgets en los que lo hemos instalado.
        (Nota: El nombre de este método no se cambia a camelCase 
        porque estamos sobreescribiendo un método existente de Qt).
        """
        # --- Lógica para abrir el desplegable al clicar en el texto ---
        if objectWatched == self.lineEdit():
            if event.type() == QtCore.QEvent.Type.MouseButtonPress:
                # Si se clica el LineEdit, mostramos el desplegable y
                # retornamos True para indicar que hemos manejado el evento.
                self.showPopup()
                return True

        # --- Lógica para mantener el desplegable abierto al clicar en un ítem ---
        if objectWatched == self.view:
            if event.type() == QtCore.QEvent.Type.MouseButtonPress:
                # Si se clica dentro de la vista, activamos nuestro flag
                # para que hidePopup() sepa que no debe cerrarse.
                index = self.view.indexAt(event.pos())
                if index.isValid():
                    self._keepPopupOpen = True
        
        # Devolvemos el control al comportamiento por defecto para otros eventos
        return super().eventFilter(objectWatched, event)

    def hidePopup(self):
        """
        Anulamos hidePopup para decidir cuándo debe cerrarse.
        (Nota: El nombre de este método no se cambia a camelCase 
        porque estamos sobreescribiendo un método existente de Qt).
        """
        if self._keepPopupOpen:
            # Si nuestro flag está activo (porque se clicó un ítem),
            # lo reseteamos y evitamos que el desplegable se cierre.
            self._keepPopupOpen = False
        else:
            # Si el flag no está activo (el cierre fue por clicar fuera,
            # perder el foco, etc.), procedemos con el cierre normal.
            super().hidePopup()

    def addItem(self, text, checked=False):
        """
        Añade un nuevo ítem chequeable a la lista.
        """
        item = QtGui.QStandardItem(text)
        item.setFlags(QtCore.Qt.ItemFlag.ItemIsUserCheckable | QtCore.Qt.ItemFlag.ItemIsEnabled)
        item.setData(QtCore.Qt.CheckState.Checked if checked else QtCore.Qt.CheckState.Unchecked, QtCore.Qt.ItemDataRole.CheckStateRole)
        self.model.appendRow(item)
        self.updateText()

    def updateText(self):
        """
        Actualiza el texto principal del combobox para reflejar los ítems seleccionados.
        """
        checkedTexts = self.getCheckedItems()
        if checkedTexts:
            self.lineEdit().setText(", ".join(checkedTexts))
        else:
            self.lineEdit().setText("--- Seleccione una o varias ---")

    def getCheckedItems(self):
        """
        Devuelve una lista con los textos de todos los ítems marcados.
        """
        checkedItems = []
        for i in range(self.model.rowCount()):
            item = self.model.item(i)
            if item.checkState() == QtCore.Qt.CheckState.Checked:
                checkedItems.append(item.text())
        return checkedItems