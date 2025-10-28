from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import QAbstractTableModel, Qt
from PyQt6.QtGui import QBrush, QColor, QFont
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