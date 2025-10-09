from PyQt6.QtWidgets import QMessageBox

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