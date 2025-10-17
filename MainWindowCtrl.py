import sys
import os
import pandas as pd
import numpy as np
from scipy import stats
from sklearn.model_selection import train_test_split

from PyQt6.QtWidgets import (QApplication, QMainWindow, QFileDialog, QInputDialog, QStatusBar)
from MainWindowUI import Ui_MainWindow
import ImportacionDatos as impd
from UtilidadesInterfaz import PandasModel as mp
from UtilidadesInterfaz import Mensajes as msj
from VentanaCargaCtrl import VentanaCargaCtrl
from UtilidadesInterfaz import PandasModelConColor


class MainWindowCtrl(QMainWindow):
    """
    Controlador principal de la ventana de la aplicación.
    Gestiona la interfaz gráfica, la carga de datos, selección de columnas,
    preprocesamiento y división de datos.
    """
    def __init__(self):
        """
        Inicializa la ventana principal y configura los elementos de la interfaz.
        Crea las variables necesarias para almacenar los distintos DataFrames 
        (original, procesado, entrenamiento y prueba) e inicializa la interfaz 
        llamando a los métodos de configuración y conexión de señales.
        """
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        # DataFrames
        self._df = None
        self.dfProcesado = None
        self.dataFrameTest = None
        self.dataFrameTrain = None
        
        # Columnas seleccionadas para entrada y salida
        self.columnaEntrada = None
        self.columnaSalida = None
        
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
        # Ocultar botones inicialmente
        self.ui.btnSeleccionarColumnas.hide()
        self.ui.cmbOpcionesPreprocesado.hide()
        self.ui.btnDividirDatos.hide()
        self.ui.btnPasarSiguientePestana.hide()
        
        # Añadir opciones al combo de preprocesamiento
        self.ui.cmbOpcionesPreprocesado.addItems([
            "Seleccione un método...",
            "Eliminar filas con NaN",
            "Rellenar con la media (Numpy)",
            "Rellenar con la mediana",
            "Rellenar con un valor constante"
        ])

    def conectarSenalesPreproceso(self):
        """Conectar señales de los botones y widgets"""
        self.ui.btnInsertarArchivo.clicked.connect(self.abrirExplorador)
        self.ui.btnSeleccionarColumnas.clicked.connect(self.abrirVentanaSeleccionColumnas)
        self.ui.cmbOpcionesPreprocesado.currentTextChanged.connect(self.aplicarPreprocesado)
        self.ui.btnDividirDatos.clicked.connect(self.procesoDataSplit)
        self.ui.btnPasarSiguientePestana.clicked.connect(self.pasarSiguientePestana)

    def abrirExplorador(self):
        """
        Abre un cuadro de diálogo para seleccionar un archivo y carga los datos en la tabla.
        Permite al usuario seleccionar un archivo con los formatos permitidos. 
        Si se selecciona una ruta válida, intenta cargar los datos utilizando la 
        función `impd.cargarDatos()` y mostrarlos en la tabla mediante `self.cargarTabla()`. 
        En caso de error, muestra mensajes de advertencia apropiados.

        Raises:
            ValueError: Si ocurre un error inesperado al cargar los datos.
            FileNotFoundError: Si el archivo seleccionado no se encuentra.
        """
        ruta, _ = QFileDialog.getOpenFileName(
            self,
            "Abrir dataset",
            "",
            "Archivos csv: (*.csv);;Archivos xlx: (*.xlx);;Archivos xlsx: (*.xlsx);; Archivos db: (*.db)"
        )
        
        if ruta != "":
            self.ui.lineEditRutaArchivo.setText(ruta)
            try:
                df = impd.cargarDatos(ruta)
                self.cargarTabla(df)
                # Mostrar botón de seleccionar columnas
                self.ui.btnSeleccionarColumnas.show()
                self.ui.btnSeleccionarColumnas.setText("Seleccionar Columnas")
            except ValueError as e:
                msj.crearAdvertencia(self, "Error inesperado", 
                    "Se ha producido un error inesperado al cargar el archivo")
            except FileNotFoundError as f:
                msj.crearAdvertencia(self, "Archivo no encontrado", 
                    "No se ha encontrado el archivo especificado")
        else:
            msj.crearAdvertencia(self, "Ruta no encontrada", 
                "Se debe seleccionar un archivo válido")

    def cargarTabla(self, df):
        """
        Carga un DataFrame en la tabla del interfaz gráfico.
        Si ya existe un modelo de datos cargado, lo elimina antes de establecer el nuevo.
        Crea un nuevo modelo a partir del DataFrame recibido y lo asigna a la tabla.
        Si ocurre un error durante la creación del modelo, muestra un mensaje de advertencia.

        Args:
            df (pandas.DataFrame): El conjunto de datos a mostrar en la tabla.

        Raises:
            ValueError: Si ocurre un error inesperado al crear el modelo de la tabla.
        """
        modelo = self.ui.tableViewDataFrame.model()
        if modelo is not None:
            self.ui.tableViewDataFrame.setModel(None)
            self.df = None
        

        try:
            model = mp(df)
            self.ui.tableViewDataFrame.setModel(model)
            self.ui.tableViewDataFrame.resizeColumnsToContents()
            self.df = df
        except ValueError as e:
            self.df = None
            msj.crearAdvertencia(self, "Error inesperado", 
                "Se ha producido un error inesperado al crear la tabla")

    def abrirVentanaSeleccionColumnas(self):
        """
        Abre la ventana de selección de columnas para entrada y salida.
        Al confirmar, marca las columnas seleccionadas en verde/rojo y muestra opciones de preprocesado.
        """
        if self.df is None:
            msj.crearAdvertencia(self, "Sin datos", "Primero debe cargar un archivo")
            return
        
        # Crear y mostrar ventana de selección de columnas
        ventanaColumnas = VentanaCargaCtrl(self.df)
        
        # Modificar el método confirmarSeleccion para que cierre y guarde las columnas
        def confirmarYCerrar():
            entrada = ventanaColumnas.ui.cmbEntrada.currentText()
            salida = ventanaColumnas.ui.cmbSalida.currentText()
            
            from VentanaCargaCtrl import mensajeDefectoCmb
            
            if (entrada != mensajeDefectoCmb and salida != mensajeDefectoCmb):
                self.columnaEntrada = entrada
                self.columnaSalida = salida
                
                msj.crearInformacion(self, "Columnas Seleccionadas",
                    f"Entrada: {entrada}\nSalida: {salida}")
                
                # Marcar columnas en el DataFrame (visualmente podríamos colorearlas)
                self.marcarColumnasSeleccionadas()
                
                # Mostrar combo de preprocesado
                self.ui.cmbOpcionesPreprocesado.show()
                
                ventanaColumnas.close()
            else:
                msj.crearAdvertencia(ventanaColumnas, "Advertencia",
                    "Debe seleccionar una columna para la entrada y la salida.")
        
        # Reemplazar la conexión del botón confirmar
        ventanaColumnas.ui.btnConfirmar.clicked.disconnect()
        ventanaColumnas.ui.btnConfirmar.clicked.connect(confirmarYCerrar)
        
        ventanaColumnas.show()
    
    def marcarColumnasSeleccionadas(self):
        if self.df is None or self.columnaEntrada is None or self.columnaSalida is None:
            return
        
        model = PandasModelConColor(self.df, columna_verde=self.columnaEntrada, 
                                    columna_roja=self.columnaSalida, tachar_nan=True)
        self.ui.tableViewDataFrame.setModel(model)
        self.ui.tableViewDataFrame.resizeColumnsToContents()
        
        self.statusBar().showMessage(f"Entrada: {self.columnaEntrada} | Salida: {self.columnaSalida}")

    # ==================== MÉTODOS DE PREPROCESAMIENTO ====================

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
    

    #ACTUALMENTE HAY ALGUN PROBLEMA CON LA NAN EN EL CASO EN EL QUE LA COJAMOS DE PRIMERA -> será x lo d current text
    #mañana lo arreglo
    def aplicarPreprocesado(self):
        """Aplica la operación de preprocesamiento seleccionada"""
        if self.df is None:
            msj.crearAdvertencia(self, "Sin datos", "No hay datos cargados")
            return
        
        df = self.df.copy()
        opcion = self.ui.cmbOpcionesPreprocesado.currentText()

        #MODIFICO CON MATCH CASE PARA HACERLO MAS LEGIBLE Y CORTO        
        try:
            match opcion:
                case "Eliminar filas con NaN":
                    nanAntes = df.isna().sum().sum()
                    df.dropna(inplace=True, ignore_index=True)
                    nanDespues = df.isna().sum().sum()
                    
                    msj.crearInformacion(self, "Preprocesado Aplicado",
                        f"Filas eliminadas: {len(self.df) - len(df)}\n"
                        f"NaN eliminados: {nanAntes}")
                
                case "Rellenar con la media (Numpy)":
                    df = self.rellenarNanColumnasNumericas(df, metodo='media')
                    msj.crearInformacion(self, "Preprocesado Aplicado",
                        "NaN rellenados con la media")
                
                case "Rellenar con la mediana":
                    df = self.rellenarNanColumnasNumericas(df, metodo='mediana')
                    msj.crearInformacion(self, "Preprocesado Aplicado",
                        "NaN rellenados con la mediana")
                
                case "Rellenar con un valor constante":
                    from PyQt6.QtWidgets import QInputDialog
                    valor, ok = QInputDialog.getText(self, "Valor constante",
                        "Introduce el valor constante para rellenar NaN:")
            
            self.dfProcesado = df
            self.cargarTabla(df)
            
            # Mostrar estadísticas del procesamiento
            mensaje = f"Procesamiento completado:\n"
            mensaje += f"Filas: {len(self.df)} → {len(df)}\n"
            mensaje += f"NaN: {self.df.isna().sum().sum()} → {df.isna().sum().sum()}"
            msj.crearInformacion(self, "Éxito", mensaje)
            
            # Verificar si hay NaN después del preprocesado
            if not df.isnull().values.any():
                # Mostrar botón de dividir datos
                self.ui.btnDividirDatos.show()
            
        except Exception as e:
            msj.crearAdvertencia(self, "Error", f"Error al procesar: {str(e)}")

    # ==================== MÉTODOS DEL DATASPLIT ====================

    def _actualizarPorcentajeTest(self):
        """Actualiza la proporción de test según el valor del input"""
        porcentaje, ok = QInputDialog.getInt(self, "División de datos",
            "Porcentaje de datos para TEST (%):", 20, 5, 50, 5)
        if ok:
            self.proporcionDeTest = float(porcentaje) / 100

    def _ejecutarDatasplit(self, tamañoTest):  
        """Realiza el datasplit en dataFrameTrain y dataFrameTest"""
        if self.dfProcesado is None:
            self.dataFrameTrain, self.dataFrameTest = train_test_split(self.df, test_size = tamañoTest)   
            return
        
        if self.dfProcesado.isnull().values.any() == True:
            msj.crearAdvertencia(self, "Presencia de Nulos", "Para continuar al datasplit no puede tener nulos en el dataframe")
            return

        self.dataFrameTrain, self.dataFrameTest = train_test_split(self.dfProcesado, test_size = tamañoTest)   

    def _mostrarTablaProporciones(self):
        """Calcula las lineas de cada parte y su porcentaje real y lo muestra en un bloque"""
        df_base = self.dfProcesado if self.dfProcesado is not None else self.df
        
        porcentajeTrain = (len(self.dataFrameTrain) / len(df_base)) * 100
        porcentajeTest = (len(self.dataFrameTest) / len(df_base)) * 100
        #si quereis sacarlo de manera diferente hay que modificar esto, esto es un crear informacion, mientras que beltran tenia un label que se cambiaba
        #por cuestion de espacio esto puede ser mejor, hay que decidirlo
        mensaje = f"División completada:\n"
        mensaje += f" Total: {len(df_base)} filas\n"
        mensaje += f" Train: {len(self.dataFrameTrain)} filas ({porcentajeTrain:.2f}%)\n"
        mensaje += f" Test: {len(self.dataFrameTest)} filas ({porcentajeTest:.2f}%)"
        
        msj.crearInformacion(self, "División Exitosa", mensaje)
        #saco el boton de lo de las graficas..
        self.ui.btnPasarSiguientePestana.show()

    def procesoDataSplit(self):
        """Realiza el proceso de datasplit y muestra los resultados"""
        self._actualizarPorcentajeTest()
        self._ejecutarDatasplit(self.proporcionDeTest)

        if (
        self.dataFrameTrain is None
        or self.dataFrameTest is None
        or self.dataFrameTrain.isnull().values.any()
        or self.dataFrameTest.isnull().values.any()):
            msj.crearAdvertencia(self, "Error inesperado", "Se ha producido un error inesperado al realizar el datasplit")
            return

        self._mostrarTablaProporciones()
        msj.crearInformacion(self, "Éxito", "El datasplit se ha realizado correctamente")

    def pasarSiguientePestana(self):
        """
        Pasa a la siguiente pestaña del QStackedWidget.
        Aquí se incluirían gráficas y análisis posteriores.
        """
        if self.dataFrameTrain is None or self.dataFrameTest is None:
            msj.crearAdvertencia(self, "Error",
                "Debe dividir los datos primero")
            return
        
        msj.crearInformacion(self, "Siguiente Fase",
            "Pasando a la fase de análisis y gráficas...\n"
            "(Esta funcionalidad se implementará posteriormente)")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = MainWindowCtrl()
    ventana.show()
    sys.exit(app.exec())