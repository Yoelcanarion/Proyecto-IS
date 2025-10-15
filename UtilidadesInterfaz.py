from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import QAbstractTableModel, Qt

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


#REVISAR
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
