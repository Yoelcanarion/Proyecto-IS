import sys
import os
import sqlite3
import pandas as pd
from PyQt6 import QtWidgets 
from PyQt6.QtWidgets import (QDialog, QApplication, QMainWindow, QFileDialog, QTableWidgetItem,QMessageBox, QHeaderView, QInputDialog, QStatusBar)
from PyQt6.QtCore import Qt 
from ExploradorUI import Ui_QMainWindow
import ImportacionDatos as impd
from UtilidadesInterfaz import PandasModel as mp
from UtilidadesInterfaz import Mensajes as msj

class ExploradorCtrl(QMainWindow):
    df = None #REVISAR Podria valer tambien con la ruta no se que es mas optimo/seguro
    def __init__(self):
        super().__init__()
        self.ui = Ui_QMainWindow()
        self.ui.setupUi(self)
        self.ui.openFileButton.clicked.connect(self.abrir_Explorador)
        self.df
        
    def abrir_Explorador(self):
        ruta,_ = QFileDialog.getOpenFileName(self,"Abrir dataset","","Archivos csv: (*.csv);;Archivos xlx: (*.xlx);;Archivos xlsx: (*.xlsx);; Archivos db: (*.db)")
        self.ui.filePathLineEdit.setPlaceholderText(ruta) 
        if ruta != "":
            
            try:
                df = impd.cargarDatos(ruta)
                self.cargarTabla(df)
            except ValueError as e:
                msj.crearAdvertencia(self,"Error inesperado", "Se ha producido un error inesperado al cargar el archivo")
            except FileNotFoundError as f:
                msj.crearAdvertencia(self,"Archivo no encontrado", "No se ha encontrado el archivo especificado")
                
        else: 
            msj.crearAdvertencia(self,"Ruta no encontrada","Se debe introducir una ruta válida")
            
    def cargarTabla (self,df):
        
        # hacer un try y hacer varios except, en funcion a los que devuelve el codigo de ventanacarga, mirando los except del mismo, poniendo el mensaje por advertencia
        modelo = self.ui.tblDatos.model()
        if modelo != None :
            self.ui.tblDatos.setModel(None)
            self.df=None
        
        try:
            model = mp(df)
            tabla = self.ui.tblDatos
            tabla.setModel(model)
            self.df = df
        except ValueError as e:
            self.df=None
            msj.crearAdvertencia(self,"Error inesperado", "Se ha producido un error inesperado al crear la tabla")
        
app = QApplication(sys.argv)
ventana = ExploradorCtrl() 
ventana.show()
sys.exit(app.exec()) 
        
    