import sys
import pandas as pd
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox
from VentanaCargaUI import Ui_MainWindow
import GestionDatos as gd
import ImportacionDatos as impDat
from UtilidadesInterfaz import Mensajes as msj

#Esta clase controla la interfaz de carga de datos

mensajeDefectoCmb = "--- Seleccione una columna ---"

class VentanaCargaCtrl(QMainWindow):
    
    def __init__(self, dataFrame):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Carga de columnas
        columnas =[mensajeDefectoCmb]
        columnas.extend(gd.cargaColumnas(dataFrame))
        self.ui.cmbEntrada.addItems(columnas)
        self.ui.cmbSalida.addItems(columnas)

        # Conectar botón de confirmación
        self.ui.btnConfirmar.clicked.connect(self.confirmarSeleccion)

    def confirmarSeleccion(self):
        entrada = self.ui.cmbEntrada.currentText()
        salida = self.ui.cmbSalida.currentText()
        if (entrada != mensajeDefectoCmb and salida != mensajeDefectoCmb):
            msj.crearInformacion(self,"Datos Seleccionados",
                f"Entrada: {entrada}\nSalida: {salida}")
        else:
             msj.crearAdvertencia(self,"Advertencia",
                "Debe seleccionar una columna para la entrada y la salida.")
    
    
#DESCOMENTAR PARA PROBAR
#app = QApplication(sys.argv)
#ventana = VentanaCargaCtrl(impDat.cargarDatos("InsertaRuta")) cambiar insertar ruta por ruta absoluta 
#ventana.show()
#sys.exit(app.exec())