import sys
import os
import sqlite3
import pandas as pd
from PyQt5 import QtWidgets 
from PyQt5.QtWidgets import (QDialog, QApplication, QMainWindow, QFileDialog, QTableWidgetItem,QMessageBox, QHeaderView, QInputDialog, QStatusBar)
from PyQt5.QtCore import Qt 
from ExploradorUI import Ui_QMainWindow 

class LoaderApp(QMainWindow):
    
    def __init__(self):
        super().__init__()
        #Cargar la UI 
        self.ui = Ui_QMainWindow()
        self.ui.setupUi(self)
        
        self.setWindowTitle ("Ventana de prueba")
        
        #Conectar señales y slots
        
        self.ui.openFileButton.clicked.connect(self.buscarArchivo) 
        
        #Configuarción de QTableWidget
        
        self.ui.dataTableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers) # O simplemente Qt.NoEditTriggers
        
        #Enumeración para setSectionResizeMode
        
        self.ui.dataTableWidget.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Interactive) 
        self.ui.dataTableWidget.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Interactive) 

        #Configurar la barra de estado (QStatusBar es parte de QMainWindow)
        self.statusBar().showMessage ("Listo para cargar un archivo.")
        
    def buscarArchivo(self):
        file_filter = "Todos los Archivos Soportados (*.csv *.xlsx *.xls *.sqlite *.db);;" \
                      "Archivos CSV (*.csv);;" \
                      "Archivos Excel (*.xlsx *.xls);;" \
                      "Bases de Datos SQLite (*.sqlite *.db);;" \
                      "Todos los Archivos (*.*)"
        
       
        initial_dir = os.path.expanduser('~') 
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar Dataset", initial_dir, file_filter) 
        
        if file_path :
            self.ui.filePathLineEdit.setText(file_path)
           
            self.cargarArchivo(file_path) 
        
        else:
           
            self.statusBar().showMessage("Selección de archivo cancelada.") 
    
    def cargarArchivo (self,file_path):
        
        self.limpiarTabla() 
        self.statusBar().showMessage(f"Cargando datos de: {os.path.basename(file_path)}...")
        file_extension = os.path.splitext(file_path)[1].lower()
        df = None
        
        try:
            if file_extension == ".csv":
                df = pd.read_csv(file_path)
            elif file_extension in (".xlsx",".xls"):
                df = pd.read_excel(file_path)
            
            elif file_extension in (".sqlite",".db"):
                
                df = self.cargarSqliteData (file_path) 
            
            else: 
                
                self.mostrarMensajeError("Tipo de archivo no compatible",
                                        f"El archivo '{os.path.basename(file_path)}' tiene una extensión no soportada: {file_extension}")

                self.ui.filePathLineEdit.setPlaceholderText("Archivo no compatible o dañado.")
                self.statusBar().showMessage("Error: Tipo de archivo no compatible.")
                return
            
            if df is not None:
                
                self.mostrarDatosTabla(df) 
                self.statusBar().showMessage (f"Datos de '{os.path.basename(file_path)}' cargados correctamente. Filas: {df.shape[0]}, Columnas: {df.shape[1]}.")
            else:
                self.statusBar().showMessage("No se pudo cargar el dataset o está vacío.")
            
        except pd.errors.EmptyDataError:
           
            self.mostrarMensajeError("Archivo Vacío",
                                    f"El archivo '{os.path.basename(file_path)}' está vacío o no contiene datos.")
            self.ui.filePathLineEdit.setPlaceholderText("Archivo vacío o sin datos.")
            self.statusBar().showMessage("Error: Archivo vacío.")
        
        except pd.errors.ParserError as e:
            
            self.mostrarMensajeError("Error de Formato",
                                    f"El archivo '{os.path.basename(file_path)}' tiene un formato incorrecto o está corrupto. Detalles: {e}")
            
            self.ui.filePathLineEdit.setPlaceholderText("Error: Archivo con formato incorrecto.")
            self.statusBar().showMessage(f"Error: {e}") # Asegurarse de mostrar el error en la barra
            
        except FileNotFoundError:
            
            self.mostrarMensajeError("Archivo no encontrado",
                                    f"El archivo '{os.path.basename(file_path)}' no se encontró en la ruta especificada. Probablemente fue movido o borrado.")
            
            self.ui.filePathLineEdit.setPlaceholderText ("Archivo no encontrado.")
            self.statusBar().showMessage("Error: Archivo no encontrado.")
        
        except Exception as e:
            
            self.mostrarMensajeError ("Error al Cargar Archivo", 
                                     f"Ocurrió un error inesperado al intentar cargar el archivo '{os.path.basename(file_path)}'. Detalles: {e}")
            self.ui.filePathLineEdit.setPlaceholderText("Error al cargar archivo.")
            self.statusBar().showMessage(f"Error: {e}")
    
    def cargarSqliteData (self, file_path):
        conn = None
        try:
            conn = sqlite3.connect(file_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [table[0] for table in cursor.fetchall()]
            
            if not tables:
                
                self.mostrarMensajeError("Base de datos vacía",
                                        f"La base de datos '{os.path.basename(file_path)}' no contiene ninguna tabla.")
                
                return None
            
            if len(tables) == 1:
                selected_table = tables[0]
            
            else:
                selected_table,correcto = QInputDialog.getItem(self, "Seleccionar Tabla",f"La base de datos '{os.path.basename(file_path)}' contiene múltiples tablas.\nPor favor, selecciona una:", tables,0,False)
                if not correcto or not selected_table:
                    self.statusBar().showMessage("Carga de base de datos cancelada por el usuario.")
                    
                    return None
            
            query = f"SELECT * FROM {selected_table}"
            df = pd.read_sql_query(query,conn)
            return df
        except sqlite3.Error as e:
           
            self.mostrarMensajeError("Error de Base de Datos SQLite", f"No se pudo leer la base de datos '{os.path.basename(file_path)}' o la tabla seleccionada. Detalles: {e}")
            
            return None
        
        finally:
            if conn:
                conn.close()
    
    def mostrarDatosTabla(self,df):
        if df.empty:
            self.statusBar().showMessage("El dataset cargado está vacío")
            
            return
        self.ui.dataTableWidget.setRowCount(df.shape[0])
        self.ui.dataTableWidget.setColumnCount(df.shape[1])
        
        self.ui.dataTableWidget.setHorizontalHeaderLabels(df.columns.astype(str))
        
        for i, fila in enumerate(df.values):
            for j, valorCelda in enumerate(fila):
                item = QTableWidgetItem(str(valorCelda))
                self.ui.dataTableWidget.setItem(i,j,item)
        
        #Reajustar el tamaño de las columnas al contenido:
        
        self.ui.dataTableWidget.resizeColumnsToContents() # Opcional, puede ser lento
    
    def limpiarTabla(self):
        self.ui.dataTableWidget.clearContents()
        self.ui.dataTableWidget.setRowCount(0)
        self.ui.dataTableWidget.setColumnCount(0)
        self.ui.dataTableWidget.setHorizontalHeaderLabels([])
    
    def mostrarMensajeError(self,titulo,mensaje):
        QMessageBox.critical(self,titulo,mensaje)
        self.ui.filePathLineEdit.setPlaceholderText("Error al cargar archivo.")
        
        self.limpiarTabla() 
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LoaderApp()
    window.show()
    sys.exit(app.exec_()) 