import sys
import os
import pandas as pd
import numpy as np
from scipy import stats
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error
import matplotlib.pyplot as plt
import seaborn as sns
from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog, QInputDialog, QStatusBar,QStackedWidget,QWidget, QVBoxLayout
from PyQt6 import QtWidgets
from PyQt6.QtCore import QCoreApplication
from MainWindowUI import Ui_MainWindow
import ImportacionDatos as impd
import GestionDatos as gd
import pickle as pk
from UtilidadesInterfaz import PandasModel as mp
from UtilidadesInterfaz import Mensajes as msj
from VentanaCargaCtrl import VentanaCargaCtrl
from UtilidadesInterfaz import PandasModelConColor
from PyQt6.QtCore import Qt

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg 
from matplotlib.figure import Figure

#Globales
mensajeDefectoCmb = "--- Seleccione una columna ---"


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
        self.ui.stackedWidget.setCurrentIndex(0)        

        # Configuración inicial
        self.resetearTodo()
        self.configurarInterfaz()

        # Conectar botón de confirmación
        self.ui.btnConfirmar.clicked.connect(self.confirmarSeleccion)
        # Añadir opciones al combo de preprocesamiento
        self.ui.cmbOpcionesPreprocesado.addItems([
            "Seleccione un método...",
            "Eliminar filas con NaN",
            "Rellenar con la media (Numpy)",
            "Rellenar con la mediana",
            "Rellenar con un valor constante"
        ])
        self.conectarSenalesPreproceso()

    @property
    def df(self):
        return self._df

    @df.setter
    def df(self, df):
        self._df = df


    def resetearTodo(self):
        """Convierte a todas las variables en None"""
                # DataFrames
        self._df = None
        self.dfProcesado = None
        self.dataFrameTest = None
        self.dataFrameTrain = None
        self.tamDfProc = None
        self.tamDf = None
        # Columnas seleccionadas para entrada y salida
        self.columnaEntrada = None
        self.columnaSalida = None
        
        #Modelo
        self.modelo=None
        self.descripcionModelo=None
        
        #Metricas
        self.r2Train=None
        self.r2Test=None
        self.ecmTrain=None
        self.ecmTest=None

        #Datos del dataframe
        self.xTrain=None
        self.yTrain=None
        self.xTest=None
        self.yTest=None

            # Limpiar gráfica
        self.limpiarGrafica()


    def configurarInterfaz(self):
        """Configuración inicial de la interfaz"""
        # Ocultar botones inicialmente
        #el de las columnas
        self.ui.conjuntoTabs.setCurrentIndex(0)
        self.ui.lineEditRutaArchivo.clear()
        self.ui.tableViewDataFrame.setModel(None)
        self.ui.textDescribirModelo.clear()
        self.ui.cmbOpcionesPreprocesado.setCurrentIndex(0)
        self.ui.btnConfirmar.hide()
        self.ui.cmbEntrada.hide()
        self.ui.cmbSalida.hide()
        #el combo del preprocesado
        self.ui.cmbOpcionesPreprocesado.hide()
        #el del preprocesado
        self.ui.botonAplicarPreprocesado.hide()
        #el texto de al lado del slider
        self.ui.lblDivision.hide()
        #El slider
        self.ui.sliderProporcionTest.hide()
        #los numeros relacionados al slider
        self.ui.numeroSliderTest.hide()
        #El que aplica la division
        self.ui.botonDividirTest.hide()
        #El de pasar a la siguiente pestaña
        self.ui.textDescribirModelo.hide()
        self.ui.propiedadesModelo.hide()
        self.ui.barraProgreso.hide()
        self.ui.btnGuardarModelo.hide()
        self.ui.btnCrearGrafica.hide()
        self.ui.lblDatosDivision.hide()

       

    def conectarSenalesPreproceso(self):
        """Conectar señales de los botones y widgets"""
        #PAGINA INICIAL
        self.ui.btnInicialCrearModelo.clicked.connect((lambda: self.cambiarPagina(1)))#PARA PASAR A LA DE PREPROCESADO
        self.ui.btnInicialCargarModelo.clicked.connect(self.cargarModeloInicio)#PARA PASAR A LA DE REGRESIÓN LINEAL

        self.ui.btnInsertarArchivo.clicked.connect(self.abrirExplorador)
        self.ui.botonDividirTest.clicked.connect(self.procesoDataSplit)
        self.ui.botonAplicarPreprocesado.clicked.connect(self.aplicarPreprocesado)
        self.ui.sliderProporcionTest.valueChanged.connect(self.actualizarLblValSlider)
        self.ui.numeroSliderTest.valueChanged.connect(self.actualizarPorcentajeSpin)
        #cargar modelo
        self.ui.btnCargarModelo.clicked.connect(self.cargarModelo)
        self.ui.btnGuardarModelo.clicked.connect(self.seleccionarRutaModelo)
        self.ui.btnCrearGrafica.clicked.connect(self.pipelineModelo)


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
                self.df = df
                self.cargarTabla(df)
                self.tamDf = len(df)
                # Mostrar botón de seleccionar columnas
                self.ui.btnConfirmar.show()
                self.ui.cmbEntrada.show()
                self.ui.cmbSalida.show()
                #Para que en el caso de volver a meter un archivo no podamos preprocesarlo sin antes eleccionar las columnas
                self.ui.cmbOpcionesPreprocesado.hide()
                self.ui.botonAplicarPreprocesado.hide()
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

        try:
            model = mp(df)
            self.ui.tableViewDataFrame.setModel(model)
            self.ui.tableViewDataFrame.resizeColumnsToContents()
            self.columnas =[mensajeDefectoCmb]
            self.columnas.extend(gd.cargaColumnas(df))
            self.ui.cmbEntrada.clear()
            self.ui.cmbSalida.clear()
            self.ui.cmbEntrada.addItems(self.columnas)
            self.ui.cmbSalida.addItems(self.columnas)

        except ValueError as e:
            msj.crearAdvertencia(self, "Error inesperado", 
                "Se ha producido un error inesperado al crear la tabla")
    
    def confirmarSeleccion(self):
        if self.df is None:
            msj.crearAdvertencia(self, "Sin datos", "Primero debe cargar un archivo")
            return
        
        entrada = self.ui.cmbEntrada.currentText()
        salida = self.ui.cmbSalida.currentText()
        if (entrada != mensajeDefectoCmb and salida != mensajeDefectoCmb):
            msj.crearInformacion(self,"Datos Seleccionados",
                f"Entrada: {entrada}\nSalida: {salida}")
            
            # Marcar columnas en el DataFrame (visualmente podríamos colorearlas)
            self.columnaEntrada =  entrada
            self.columnaSalida = salida
            self.marcarColumnasSeleccionadas(self.df)
            #Ponemos que se vean despues de seleccionar
            self.ui.botonDividirTest.hide()
            self.ui.numeroSliderTest.hide()
            self.ui.sliderProporcionTest.hide()
            self.ui.lblDivision.hide()
            self.ui.cmbOpcionesPreprocesado.show()
            self.ui.botonAplicarPreprocesado.show()
        else:
             msj.crearAdvertencia(self,"Advertencia",
                "Debe seleccionar una columna para la entrada y la salida.")
    

    def marcarColumnasSeleccionadas(self,dfEntr):
        if self.df is None or self.columnaEntrada is None or self.columnaSalida is None:
            return
        
        model = PandasModelConColor(dfEntr, columna_verde=self.columnaEntrada, 
                                    columna_roja=self.columnaSalida, tachar_nan=True)
        self.ui.tableViewDataFrame.setModel(model)
        self.ui.tableViewDataFrame.resizeColumnsToContents()
        #para que se muestre abajo las seleccionadas
        self.statusBar().showMessage(f"Entrada: {self.columnaEntrada} | Salida: {self.columnaSalida}")


    # ==================== MÉTODOS DE PREPROCESAMIENTO ====================

    def rellenarNanColumnasNumericas(self, df, metodo, valorConstante=None):
        """
        Rellena valores NaN en las columnas de entrada y salida seleccionadas.
        
        Args:
            df: DataFrame a procesar
            metodo: 'media', 'mediana' o 'constante'
            valorConstante: valor a usar si metodo='constante'
            
        Returns:
            DataFrame con valores NaN rellenados en las columnas seleccionadas
        """
        # Solo procesar las columnas de entrada y salida
        columnas_a_procesar = [self.columnaEntrada, self.columnaSalida]
        
        for col in columnas_a_procesar:
            # Verificar que la columna existe y es numérica
            if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
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
        if self.ui.cmbOpcionesPreprocesado.currentText() == "Seleccione un método...":
            return
        
        if self.df is None:
            msj.crearAdvertencia(self, "Sin datos", "No hay datos cargados")
            return
        
        # Verificar que se hayan seleccionado columnas
        if self.columnaEntrada is None or self.columnaSalida is None:
            msj.crearAdvertencia(self, "Sin columnas seleccionadas", 
                "Debe seleccionar las columnas de entrada y salida primero")
            return
        
        self.dfProcesado = self.df.copy(deep=True)
        opcion = self.ui.cmbOpcionesPreprocesado.currentText()

        try:
            match opcion:
                case "Eliminar filas con NaN":
                    nanAntes = self.dfProcesado[[self.columnaEntrada, self.columnaSalida]].isna().sum().sum()
                    # Eliminar filas que tengan NaN en las columnas seleccionadas
                    self.dfProcesado.dropna(subset=[self.columnaEntrada, self.columnaSalida], 
                                        inplace=True, ignore_index=True)
                    
                    msj.crearInformacion(self, "Preprocesado Aplicado",
                        f"Filas eliminadas: {self.tamDf - len(self.dfProcesado)}\n"
                        f"NaN eliminados: {nanAntes}")
                
                case "Rellenar con la media (Numpy)":
                    self.dfProcesado = self.rellenarNanColumnasNumericas(self.dfProcesado, metodo='media')
                    msj.crearInformacion(self, "Preprocesado Aplicado",
                        "NaN rellenados con la media en columnas seleccionadas")
                
                case "Rellenar con la mediana":
                    self.dfProcesado = self.rellenarNanColumnasNumericas(self.dfProcesado, metodo='mediana')
                    msj.crearInformacion(self, "Preprocesado Aplicado",
                        "NaN rellenados con la mediana en columnas seleccionadas")
                
                case "Rellenar con un valor constante":
                    from PyQt6.QtWidgets import QInputDialog
                    valorConstante, ok = QInputDialog.getText(self, "Valor constante",
                        "Introduce el valor constante para rellenar NaN:")
                    
                    if ok and valorConstante:
                        valorNumerico = float(valorConstante)
                        self.dfProcesado = self.rellenarNanColumnasNumericas(
                            self.dfProcesado, 
                            metodo='constante', 
                            valorConstante=valorNumerico
                        )
                        msj.crearInformacion(self, "Preprocesado Aplicado",
                            f"NaN rellenados con {valorNumerico} en columnas seleccionadas")
                    else:
                        return
            
            self.cargarTabla(self.dfProcesado)
            self.marcarColumnasSeleccionadas(self.dfProcesado)
            self.tamDfProc = len(self.dfProcesado)
            # Mostrar estadísticas del procesamiento
            mensaje = f"Procesamiento completado:\n"
            mensaje += f"Filas: {self.tamDf} → {self.tamDfProc}\n"
            mensaje += f"NaN en columnas seleccionadas: {self.df[[self.columnaEntrada, self.columnaSalida]].isna().sum().sum()} → {self.dfProcesado[[self.columnaEntrada, self.columnaSalida]].isna().sum().sum()}"
            msj.crearInformacion(self, "Éxito", mensaje)
            
            # Verificar si hay NaN en las columnas de entrada y salida
            if not self.dfProcesado[[self.columnaEntrada, self.columnaSalida]].isnull().values.any():
                # Mostrar botón de dividir datos
                self.ui.botonDividirTest.show()
                self.ui.lblDivision.show()
                self.ui.numeroSliderTest.show()
                self.ui.sliderProporcionTest.show()
                self.ui.lblDatosDivision.show()

            else:
                msj.crearAdvertencia(self, "NaN restantes", 
                    "Aún quedan valores NaN en las columnas seleccionadas.\n"
                    "Debe aplicar otro método de preprocesado.")
            
        except Exception as e:
            msj.crearAdvertencia(self, "Error", f"Error al procesar: {str(e)}")


    # ==================== MÉTODOS DEL DATASPLIT ====================
    def actualizarLblValSlider(self):
        value = self.ui.sliderProporcionTest.value()
        self.ui.numeroSliderTest.setValue(value)
        longitud = self.tamDfProc
        test = float(value)
        train = 100 - test
        self.ui.lblDatosDivision.setText(f"Test: {test}% --- Filas: {round(longitud*test/100)}\nTrain: {train}% --- Filas: {round(longitud*train/100)}")
        
    def _actualizarPorcentajeTest(self):
        """Actualiza la proporción de test según el valor del slider"""
        value = self.ui.sliderProporcionTest.value()
        self.proporcionDeTest = float(value) / 100
    
    def actualizarPorcentajeSpin(self):
        """Actualiza la proporción de test del slider el valor del spin"""
        value = self.ui.numeroSliderTest.value()
        self.ui.sliderProporcionTest.setValue(value)
        self.proporcionDeTest = float(value) / 100
        

    def _ejecutarDatasplit(self, tamañoTest):  
        """Realiza el datasplit en dataFrameTrain y dataFrameTest"""
        if self.dfProcesado is None:
            self.dataFrameTrain, self.dataFrameTest = train_test_split(self.df, test_size=tamañoTest)   
            return
        
        # Verificar que no hay nulos en las columnas seleccionadas
        columnas_importantes = [self.columnaEntrada, self.columnaSalida]
        if self.dfProcesado[columnas_importantes].isnull().values.any() == True:
            msj.crearAdvertencia(self, "Presencia de Nulos", 
                "Para continuar al datasplit no puede tener nulos en las columnas de entrada o salida")
            return
        
        self.dataFrameTrain, self.dataFrameTest = train_test_split(self.dfProcesado, test_size=tamañoTest)


    def _mostrarResultadosSplit(self):
        """Calcula las líneas de cada parte y su porcentaje real y lo muestra"""
        if self.dataFrameTrain is None or self.dataFrameTest is None:
            return
        
        # Líneas y porcentaje de líneas del entrenamiento
        porcentajeTrain = (len(self.dataFrameTrain) / self.tamDfProc) * 100
        mensajeTrain = f"{len(self.dataFrameTrain)} Líneas de Entrenamiento --- {porcentajeTrain:.2f}% de los datos"
        
        # Líneas y porcentaje de líneas del test
        porcentajeTest = 100 - porcentajeTrain
        mensajeTest = f"{len(self.dataFrameTest)} Líneas de Test --- {porcentajeTest:.2f}% de los datos"
        
        # Mostrar en un mensaje informativo
        msj.crearInformacion(self, "División Completada", 
            f"{mensajeTrain}\n{mensajeTest}")


    def procesoDataSplit(self):
        """Realiza el proceso de datasplit y muestra los resultados"""
        # Actualizar la proporción según el slider
        self._actualizarPorcentajeTest()
        
        # Ejecutar el datasplit
        self._ejecutarDatasplit(self.proporcionDeTest)
        
        # Mostrar los resultados si el split fue exitoso
        if self.dataFrameTrain is not None and self.dataFrameTest is not None:
            self._mostrarResultadosSplit()
            self.ui.btnCrearGrafica.show()


    def cambiarPagina(self, nPaginasAMover):
        """Cambia de página en el QStackedWidget según el número de páginas a mover""" #puede ser negativo o positivo
        indiceActual = self.ui.stackedWidget.currentIndex()
        nuevoIndice = indiceActual + nPaginasAMover
        if 0 <= nuevoIndice < self.ui.stackedWidget.count():
            self.ui.stackedWidget.setCurrentIndex(nuevoIndice)


    #========================MÉTODOS DE REGRESIÓN LINEAL=======================#

    def seleccionarRutaModelo(self):
        """Método que verifica si se añadió una descripción al modelo y también pone una interfaz para guardar el modelo donde el usuario desee"""
    # Abre un diálogo para elegir la ruta y el nombre del archivo .pkl
        descr  = self.ui.textDescribirModelo.toPlainText()
        if descr =="":
                msj.crearInformacion(self,"Descripcion sin detalles", "No se ha escrito ninguna descripcion")

        ruta, _ = QtWidgets.QFileDialog.getSaveFileName(
        self,
        "Guardar modelo como",
        "",
        "Modelos (*.pkl)"
    )
        if ruta:
        # Asegurar que la extensión sea .pkl aunque el usuario no la escriba
            if not ruta.lower().endswith(".pkl"):
                ruta += ".pkl"
            self.guardarModelo(ruta,descr)


    def guardarModelo(self, ruta,descr):
        """Método usado para guardar el modelo, sus características y una descripción, en un archivo de formato .plk"""
        if ruta:
            parametros = {
                "modelo": self.modelo,
                "columnaEntrada": self.columnaEntrada,
                "columnaSalida": self.columnaSalida,
                "r2Train": self.r2Train,
                "r2Test": self.r2Test,
                "ecmTrain": self.ecmTrain,
                "ecmTest": self.ecmTest,
            }

            # Agregar descripción desde el panel de texto
            parametros["descripcion"] = descr

            # Detectar parámetros faltantes
            faltantes = [nombre for nombre, valor in parametros.items() if valor is None]
            if faltantes:
                msj.crearAdvertencia(self, "Error: faltan los siguientes parámetros de descripción:", f"{faltantes}")
                return

            # Crear diccionario del modelo
            dict_modelo = gd.crearDiccionarioModelo(**parametros)

            try:
                # Guardar en disco usando tu función
                error = gd.crearModeloDisco(dict_modelo, ruta)
                if error:
                    msj.crearAdvertencia(self, "Error al guardar el modelo", error)
                else:
                    msj.crearInformacion(self, "Éxito", "El modelo se ha guardado correctamente.")
            except Exception as e:
                msj.crearAdvertencia(self, "Error no previsto al guardar el modelo", str(e))
        else:
            msj.crearAdvertencia(self, "Error", "No se seleccionó ninguna ruta para guardar el modelo.")

        
    def crearAjustarModelo(self):
        """Método usado para crear, ajustar, testear y obtener estadísticas como R**2 y ECM a partir de los datos procesados anteriormente"""
        if self.dataFrameTrain is None or self.dataFrameTest is None:
            msj.crearAdvertencia(self, "Error de datos", "No hay datos de entrenamiento o test disponibles")
            return
        
        if self.columnaEntrada is None or self.columnaSalida is None:
            msj.crearAdvertencia(self, "Error de columnas", "No se han seleccionado las columnas de entrada y salida")
            return
        self.xTrain = self.dataFrameTrain[[self.columnaEntrada]]
        self.yTrain = self.dataFrameTrain[self.columnaSalida]
        self.xTest = self.dataFrameTest[[self.columnaEntrada]]
        self.yTest = self.dataFrameTest[self.columnaSalida]

        self.modelo = LinearRegression().fit(self.xTrain, self.yTrain)

        yTrainPred = self.modelo.predict(self.xTrain)
        yTestPred = self.modelo.predict(self.xTest)

        self.r2Train = r2_score(self.yTrain, yTrainPred)
        self.r2Test = r2_score(self.yTest, yTestPred)

        self.ecmTrain = mean_squared_error(self.yTrain, yTrainPred)
        self.ecmTest = mean_squared_error(self.yTest, yTestPred) 


    def plotGrafica(self):
        """Método que se encarga de graficar la regresión lineal con los datos del modelo"""
        # Verificar que el modelo y los datos existen
        if self.modelo is None:
            msj.crearAdvertencia(self, "Error de datos", "No hay modelo disponible para graficar")
            return
        
        if self.xTrain is None or self.yTrain is None or self.xTest is None or self.yTest is None:
            msj.crearAdvertencia(self, "Error de datos", "No hay datos de entrenamiento o test para graficar")
            return

        # Mostrar y actualizar barra de progreso
        self.ui.barraProgreso.setVisible(True)
        self.ui.barraProgreso.setValue(0)
        QCoreApplication.processEvents()

        layout = QVBoxLayout(self.ui.placeholderGrafica)

        # Crear figura con estilo Seaborn
        sns.set(style="whitegrid", context="talk")
        fig = Figure(figsize=(6, 4))
        canvas = FigureCanvasQTAgg(fig)
        eje = fig.add_subplot(111)
        self.ui.barraProgreso.setValue(40)

        # Datos
        puntosXTrain = self.xTrain[self.columnaEntrada]
        puntosYTrain = self.yTrain
        puntosXTest = self.xTest[self.columnaEntrada]
        puntosYTest = self.yTest

        sns.scatterplot(x=puntosXTrain, y=puntosYTrain, color='blue', label='Train', ax=eje)
        sns.scatterplot(x=puntosXTest, y=puntosYTest, color='orange', label='Test', ax=eje)

        # Recta de regresión (línea roja)
        xLine = np.linspace(min(puntosXTrain.min(), puntosXTest.min()), max(puntosXTrain.max(), puntosXTest.max()), 100)
        yLine = self.modelo.predict(xLine.reshape(-1, 1))
        eje.plot(xLine, yLine, color="red", linewidth=2, label="Recta de regresión")

        #Indicaciones
        eje.set_title("Regresión Lineal", fontsize=14)
        eje.set_xlabel(self.columnaEntrada)
        eje.set_ylabel(self.columnaSalida)
        eje.legend()
        sns.despine(fig)

        # Añadir al layout
        layout.addWidget(canvas)
        self.ui.placeholderGrafica.setLayout(layout)
        self.ui.barraProgreso.setValue(80)

        # Refrescar
        canvas.draw()
        self.ui.barraProgreso.setValue(100)
        QCoreApplication.processEvents()
        self.ui.barraProgreso.setVisible(False)


    def limpiarGrafica(self):
        """Limpia completamente el widget de la gráfica"""
        # Obtener el layout actual
        layout = self.ui.placeholderGrafica.layout()
        
        if layout is not None:
            # Eliminar todos los widgets del layout
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
            
            # Eliminar el layout
            QWidget().setLayout(layout)


    def pipelineModelo(self):
        """Pipeline que sirve para el proceso completo de representar la gráfica tras su procesado"""
        self.crearAjustarModelo() 
        self.plotGrafica()
        # Solo actualizar UI si todo salió bien
        if self.r2Train is not None and self.r2Test is not None:
            self.ui.labelR2Test.setText(f"R**2 Entrenamiento: {self.r2Train:.4f}\nR**2 Test: {self.r2Test:.4f}\n\nECM Entrenamiento: {self.ecmTrain:.4f}\nECM Test: {self.ecmTest:.4f}")
            self.ui.labelFormula.setText(f"Fórmula Modelo: y = {self.modelo.intercept_} + {self.modelo.coef_}*x")
            self.ui.propiedadesModelo.show()
            self.ui.btnGuardarModelo.show()
            self.ui.textDescribirModelo.show()



    def cargarModeloInicio(self):
        """Opción si quieres ir desde el principio a cargar una gráfica"""
        self.cambiarPagina(1)
        self.ui.conjuntoTabs.setCurrentIndex(1)
        self.ui.btnCrearGrafica.hide()
        self.cargarModelo()
        
    def cargarModelo(self):
        """Método usado para cargar modelos previamente guardados en formato .plk"""
        ruta, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Seleccionar modelo",
            "",
            "Modelos (*.pkl)"
        )

        if not ruta:
            return 

        try:
            with open(ruta, 'rb') as f:
                datos = pk.load(f)

            self.modelo = datos.get("modelo")
            self.columnaEntrada = datos.get("columnaEntrada")
            self.columnaSalida = datos.get("columnaSalida")

            metricas = datos.get("metricas", {})
            self.r2Train = metricas.get("r2Train")
            self.r2Test = metricas.get("r2Test")
            self.ecmTrain = metricas.get("ecmTrain")
            self.ecmTest = metricas.get("ecmTest")
            self.formula = datos.get("formula", "")

            # Actualizar tab2
            self.ui.textDescribirModelo.setPlainText(datos.get("descripcion", ""))
            self.ui.labelR2Test.setText(f"R**2 Entrenamiento: {self.r2Train:.4f}\nR**2 Test: {self.r2Test:.4f}\n\nECM Entrenamiento: {self.ecmTrain:.4f}\nECM Test: {self.ecmTest:.4f}")
            self.ui.labelFormula.setText(f"{self.formula}")
            self.ui.propiedadesModelo.show()
            self.ui.btnGuardarModelo.show()
            self.ui.textDescribirModelo.show()
            self.ui.btnCrearGrafica.hide()
            self.limpiarGrafica()
            
            #Actualizar tab1
            self.ui.botonDividirTest.hide()
            self.ui.sliderProporcionTest.hide()
            self.ui.lblDivision.hide()
            self.ui.lblDatosDivision.hide()
            self.ui.numeroSliderTest.hide()
            self.ui.cmbOpcionesPreprocesado.hide()
            self.ui.botonAplicarPreprocesado.hide()

            self.ui.lineRutaCargar.setText(ruta)
            # Mensaje de éxito
            msj.crearInformacion(self, "Éxito", f"Modelo cargado correctamente:\n{ruta}")

        except (pk.PickleError, EOFError):
            msj.crearAdvertencia(self, "Error de lectura", "El archivo no es un modelo válido o está dañado.")
        except FileNotFoundError:
            msj.crearAdvertencia(self, "Error", "No se encontró el archivo especificado.")
        except Exception as e:
            msj.crearAdvertencia(self, "Error inesperado", f"Ocurrió un error: {e}")



if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = MainWindowCtrl()
    ventana.show()
    sys.exit(app.exec())