from UI.MainWindowCtrl import MainWindowCtrl
from PyQt6.QtWidgets import QApplication
import sys

if __name__ == "__main__":
    app = QApplication(sys.argv)
    controlador = MainWindowCtrl()
    controlador.show()
    sys.exit(app.exec())
