import sys
import os
import sqlite3
import pandas as pd
import numpy as np
import pandas as pd
from scipy import stats

from PyQt6.QtWidgets import (QApplication, QMainWindow, QFileDialog, QTableWidgetItem,QMessageBox, QHeaderView, QInputDialog, QStatusBar)
from MainWindowUI import Ui_QMainWindow
import ImportacionDatos as impd
from UtilidadesInterfaz import PandasModel as mp
from UtilidadesInterfaz import Mensajes as msj

class MainWindowCtrl(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_QMainWindow()
        self.ui.setupUi(self)
        #El que cargamos
        self._df = None
        #el procesado
        self.dfProcesado = None
        # Configuración inicial
        self.configurarInterfaz()
        self.conectarSenalesPreproceso()
        
    

    @property
    def df(self):
        return self._df

    @df.setter
    def df(self, df):
        self._df = df

    def configurarInterfaz(self):
        """Configuración inicial de la interfaz"""
        # Ocultar input de constante inicialmente
        self.ui.input_constante.hide()
                
        # Añadir opciones al combo de preprocesamiento
        self.ui.combo_opciones.addItems([
            "Eliminar filas con NaN",
            "Rellenar con la media (Numpy)",
            "Rellenar con la mediana",
            "Rellenar con un valor constante"
        ])
        
        # Asegurar que empezamos en la página del explorador
        self.ui.stackedWidget.setCurrentIndex(0)

    def conectarSenalesPreproceso(self):
        """Conectar señales adicionales para preprocesamiento"""
        # El botón openFileButton ya está conectado en la clase padre
        # Solo conectamos las señales nuevas
        self.ui.btnContinuarPreproceso.clicked.connect(self.irAPreprocesamiento)
        self.ui.combo_opciones.currentTextChanged.connect(self.mostrarConstante)
        self.ui.btn_aplicar.clicked.connect(self.aplicarPreprocesado)
        self.ui.btnVolverExplorador.clicked.connect(self.volverAExplorador)
        self.ui.openFileButton.clicked.connect(self.abrirExplorador)


       
    
    
    
    def abrirExplorador(self):
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
            msj.crearAdvertencia(self,"Ruta no encontrada","Se debe introducir una ruta valida")
            
    def cargarTabla(self,df):
        
        # hacer un try y hacer varios except, en funcion a los que devuelve el codigo de ventanacarga, mirando los except del mismo, poniendo el mensaje por advertencia
        modelo = self.ui.tblDatos.model()
        if modelo != None :
            self.ui.tblDatos.setModel(None)
            self.df = None 
        
        try:
            model = mp(df)
            tabla = self.ui.tblDatos
            tabla.setModel(model)
            self.df = df
        except ValueError as e:
            self.df = None
            msj.crearAdvertencia(self,"Error inesperado", "Se ha producido un error inesperado al crear la tabla")

    def irAPreprocesamiento(self):
        """Cambia a la página de preprocesamiento"""
        if self.df is None:
            msj.crearAdvertencia(self, "Sin datos", "Primero debe cargar un archivo")
            return
        
        # Cambiar a la página de preprocesamiento
        self.ui.stackedWidget.setCurrentIndex(1)
        
        # Mostrar información de valores NaN
        self.mostrarInfoNan()
        
        # Cargar tabla original en vista de preprocesamiento
        self.mostrarTablaOriginal()
        
        # Limpiar tabla procesada
        self.ui.table_view_after.setModel(None)
        self.ui.label_after.setText("DataFrame PROCESADO")
    
    def volverAExplorador(self):
        """Vuelve a la página del explorador"""
        self.ui.stackedWidget.setCurrentIndex(0)
    
    # ==================== MÉTODOS DE PREPROCESAMIENTO ====================
    
    def mostrarInfoNan(self):
        """Muestra información sobre valores NaN en el DataFrame"""
        if self.df is None:
            return
        
        nanTotal = self.df.isna().sum().sum()
        if nanTotal > 0:
            mensaje = f"Se encontraron {nanTotal} valores NaN\n"
            for col in self.df.columns:
                nanCol = self.df[col].isna().sum()
                if nanCol > 0:
                    mensaje += f"  • {col}: {nanCol} NaN\n"
            self.ui.label_info.setText(mensaje)
        else:
            self.ui.label_info.setText("✓ No hay valores NaN en el dataset")
    
    def mostrarConstante(self):
        """Muestra u oculta el input de valor constante según la opción seleccionada"""
        if "constante" in self.ui.combo_opciones.currentText():
            self.ui.input_constante.show()
        else:
            self.ui.input_constante.hide()
    #HAY QU EMEJORAR ALGUNAS COISAS, NO SE SI FUNCIONA BIEN LA MEDIA Y LA M EDIA 
    def rellenarNanColumnasNumericas(self, df, metodo, valorConstante=None):
        """
        Rellena valores NaN en columnas numéricas del DataFrame.
        
        Args:
            df: DataFrame a procesar
            metodo: 'media', 'mediana' o 'constante'
            valorConstante: valor a usar si metodo='constante'
            
        Returns:
            DataFrame con valores NaN rellenados
        """        
        for col in df.select_dtypes(include=[np.number]).columns:
            if df[col].isna().any():
                if metodo == 'media':
                    valor = np.nanmean(df[col])
                    df[col] = df[col].fillna(valor)
                elif metodo == 'mediana':
                    valor = np.nanmedian(df[col].to_numpy())
                    df[col] = df[col].fillna(valor)
                elif metodo == 'constante' and valorConstante is not None:
                    df[col] = df[col].fillna(valorConstante)
        return df
    
    def aplicarPreprocesado(self):
        """Aplica la operación de preprocesamiento seleccionada"""
        if self.df is None:
            msj.crearAdvertencia(self, "Sin datos", "No hay datos cargados")
            return
        
        df = self.df.copy()
        opcion = self.ui.combo_opciones.currentText()
        
        try:
            if opcion == "Eliminar filas con NaN":
                #inplace -> no vuelves a almacenar el dataframe, lo hace en el sitio
                #ignore_index -> reescribe el indic ej borro la 12, la 14 pasa a la 13
                df.dropna(inplace=True,ignore_index=True)
            
            elif "Rellenar con la media (Numpy)" == opcion:
                df = self.rellenarNanColumnasNumericas(df, metodo='media')
            
            elif "Rellenar con la mediana" == opcion:
                df = self.rellenarNanColumnasNumericas(df, metodo='mediana')
            
            elif "Rellenar con un valor constante" == opcion:
                valor = self.ui.input_constante.text()
                if valor == "":
                    msj.crearAdvertencia(self, "Valor requerido", "Introduce un valor constante")
                    return
                try:
                    valor = float(valor)
                except:
                    pass
                df = df.fillna(valor)
            
            self.dfProcesado = df
            self.mostrarTablaProcesada()
            
            # Mostrar estadísticas del procesamiento
            mensaje = f"Procesamiento completado:\n"
            mensaje += f"Filas: {len(self.df)} → {len(df)}\n"
            mensaje += f"NaN: {self.df.isna().sum().sum()} → {df.isna().sum().sum()}"
            msj.crearInformacion(self, "Éxito", mensaje)
            
        except Exception as e:
            msj.crearAdvertencia(self, "Error", f"Error al procesar: {str(e)}")
    
    
    def mostrarTablaOriginal(self):
        """Muestra el DataFrame original en la vista de preprocesamiento"""
        if self.df is None:
            return
        model = mp(self.df)
        self.ui.table_view.setModel(model)
        self.ui.table_view.resizeColumnsToContents()
        self.ui.label_preview.setText(f"DataFrame ORIGINAL ({len(self.df)} filas)")
    
    def mostrarTablaProcesada(self):
        """Muestra el DataFrame procesado"""
        if self.dfProcesado is None:
            return
        model = mp(self.dfProcesado)
        self.ui.table_view_after.setModel(model)
        self.ui.table_view_after.resizeColumnsToContents()
        self.ui.label_after.setText(f"DataFrame PROCESADO ({len(self.dfProcesado)} filas)")






app = QApplication(sys.argv)
ventana = MainWindowCtrl() 
ventana.show()
sys.exit(app.exec())