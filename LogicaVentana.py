import sys
import os
import pandas as pd
from PyQt6 import QtWidgets
from PyQt6.QtWidgets import (QDialog, QApplication, QMainWindow, QFileDialog, QTableWidgetItem,
    QMessageBox, QHeaderView, QInputDialog, QStatusBar, QAbstractItemView)
from PyQt6.uic import load_ui
from PyQt6.QtCore import Qt
from VentanaMainUI import Ui_QMainWindow

class LoaderApp(QMainWindow):
    def __init__(self):
        
        #Cargar la UI 
        self.ui = Ui_QMainWindow()
        self.ui.setupUi(self)
        
        self.setWindowTitle ("Ventana de prueba")
        
        #Conectar señales y slots
        self.ui.openFileButton.clicked.connect(self.open_file_dialog)
        
        #Configuarción de QTableWidget
        #Enumeración para setEditTriggers
        self.ui.dataTableWidget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        #Enumeración para setSectionResizeMode
        self.ui.dataTableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.ui.dataTableWidget.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)

        #Configurar la barra de estado (QStatusBar es parte de QMainWindow)
        self.statusBar().showMessage ("Listo para cargar un archivo.")
        
    def buscarArchivo(self):
        file_filter = "(*.csv *.xlsx *.xls *.sqlite *.db)"
        
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar Dataset","",file_filter)
        
        if file_path :
            self.ui.filePathLineEdit.setText(file_path)
            self.load_data(file_path)
        
        else:
            self.statusBar().showMessages("Selección de archivo cancelada.")
    
    def CargarArchivo (self,file_path):
        self.clear_table()
        self.statusBar().showMessage(f"Cargando datos de: {os.path.basename(file_path)}...")
        file_extension = os.path.splitext(file_path)[1].lower()
        df = None
        
        try:
            if file_extension == ".csv":
                df = pd.read_csv(file_path)
            elif file_extension in (".xlsx",".xls"):
                df = pd.read_excel(file_path)
            
            elif file_extension in (".sqlite",".db"):
                df = self._load_sqlite_data (file_path)
            
            else: 
                self.show_error_message("Tipo de archivo no compatible",
                                        f"El archivo '{os.path.basename(file_path)}'tiene una extensión no soportada: {file_extension}")

    
        
        