import sys
import os
import pandas as pd
from pandas.api.types import is_numeric_dtype
import numpy as np
from scipy import stats
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error
import matplotlib.pyplot as plt
import seaborn as sns
from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog, QInputDialog, QStatusBar,QStackedWidget,QWidget, QVBoxLayout
from PyQt6 import QtWidgets
from PyQt6.QtCore import QCoreApplication, QPropertyAnimation, QEasingCurve
from PyQt6.QtWidgets import QGraphicsOpacityEffect
from UI.MainWindowUI import Ui_MainWindow
import Backend.ImportacionDatos as impd
import Backend.GestionDatos as gd
import pickle as pk
from UI.UtilidadesInterfaz import PandasModel as mp
from UI.UtilidadesInterfaz import Mensajes as msj
from UI.UtilidadesInterfaz import PandasModelConColor
from UI.UtilidadesInterfaz import CheckableComboBox
from PyQt6.QtCore import Qt
from UI.transiciones import TransicionPaginas
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from Backend import PreprocesamientoDatos as PrepDat
from Backend import ProcesadoDatos as ProcDat
import plotly.graph_objects as go
import plotly.express as px
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QVBoxLayout, QWidget
from PyQt6.QtCore import QCoreApplication
from sklearn.metrics import confusion_matrix

#Globales
mensajeDefectoCmb = "--- Seleccione una columna de Salida---"




class MainWindowCtrl(QMainWindow):
    """
    Controlador principal de la ventana de la aplicación.
    Gestiona la interfaz gráfica, la carga de datos, selección de columnas,
    preprocesamiento y división de datos.
    
    OPTIMIZACIONES IMPLEMENTADAS:
    - Uso de PandasModelConColor optimizado con caché precalculado
    - Acceso directo a arrays NumPy para mejor rendimiento
    - Reducción de operaciones repetitivas en renderizado de tablas
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
        # Inicializar sistema de transiciones
        self.transicion = TransicionPaginas(self)
        #sino se lo quito como veais, se puede llamar al  msj normal, sin poner controlador.msj
        self.msj = msj
        # Configuración inicial
        self.resetearTodo()
        self.configurarInterfaz()


        # Conectar botón de confirmación
        self.ui.btnConfirmar.clicked.connect(self.confirmarSeleccion)
        # Añadir opciones al combo de preprocesamiento
        self.ui.cmbOpcionesPreprocesado.addItems([
            "Seleccione un método para preprocesado",
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
        self.columnasEntrada = None
        self.columnaSalida = None

        self.columnasEntradaGraficada = None
        self.columnaSalidaGraficada = None

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

        #Datos de predicción
        self.datosEntrada = []
        # Limpiar gráfica
        self.limpiarGrafica()

    def cargarComboModelos(self, logistico):
        self.ui.cmbModelos.clear()
        if logistico:
            self.ui.cmbModelos.addItems([
            "--- Seleccione un Entrenamiento---",
            "Regresión Logística" ,
            "Árbol de Decisión (Clasif)",
            "KNN (Clasificación)"
        ])
        else:
            self.ui.cmbModelos.addItems([
            "--- Seleccione un Entrenamiento---",
            "Regresión Lineal",   
            "Regresión Polinómica",
            "SVR",  
            "Árbol de Decisión", 
            "KNN",
        ])
            

    def resetearPaginaPreprocesado(self):
        """Resetea los elementos de la página 1"""
        self.ui.tableViewDataFrame.setModel(None)
        self.ui.btnConfirmar.hide()
        self.ui.cmbEntrada.hide()
        self.ui.cmbSalida.hide()
        self.ui.cmbOpcionesPreprocesado.hide()
        self.ui.botonAplicarPreprocesado.hide()
        self.ui.sliderProporcionTest.hide()
        self.ui.botonDividirTest.hide()
        self.ui.lblDatosDivision.hide()
        self.ui.lblDivision.hide()
        self.ui.numeroSliderTest.hide()
        self.ui.cmbModelos.hide()
    

    def configurarInterfaz(self):
        """Configuración inicial de la interfaz"""
        #Configuracion ComboboxSeleccion
        original_combo = self.ui.cmbEntrada
        parent = original_combo.parent()
        layout = parent.layout()
        self.checkable_combo_entrada = CheckableComboBox(parent)
        # Copiar propiedades importantes
        self.checkable_combo_entrada.setGeometry(original_combo.geometry())
        # Reemplazar el widget en el layout
        if layout:
            layout.replaceWidget(original_combo, self.checkable_combo_entrada)
        original_combo.deleteLater() # Eliminar el original
        self.ui.cmbEntrada = self.checkable_combo_entrada # Asignar el nuevo a la UI
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
        self.ui.lblDatosDivision.hide()
        self.ui.placeholderCorrelacion.hide()
        #Widgets de predicción
        self.ui.btnAplicarPrediccion.hide()
        self.ui.labelEntradaActual.hide()
        self.ui.labelEntradaActual.hide()
        self.ui.labelPrediccion.hide()
        self.ui.spinBoxEntrada.hide()
        self.ui.cmbModelos.hide()


    def conectarSenalesPreproceso(self):
        """Conectar señales de los botones y widgets"""
  
        self.ui.btnInsertarArchivo.clicked.connect(self.abrirExplorador)
        self.ui.botonDividirTest.clicked.connect(self.pipelineModelo)
        self.ui.botonAplicarPreprocesado.clicked.connect(self.aplicarPreprocesado)
        self.ui.sliderProporcionTest.valueChanged.connect(self.actualizarLblValSlider)
        self.ui.numeroSliderTest.valueChanged.connect(self._actualizarPorcentajeSpin)
        #cargar modelo
        self.ui.btnCargarModelo.clicked.connect(self.cargarModelo)
        self.ui.btnGuardarModelo.clicked.connect(self.seleccionarRutaModelo)

       #actualizar status bar
        self.ui.conjuntoTabs.currentChanged.connect(self.actualizarColumnasSeleccionadas)

        #Poner valores de predicción
        self.ui.btnAplicarPrediccion.clicked.connect(self.pipelinePrediccion)


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
                self.resetearPaginaPreprocesado()
                df = impd.cargarDatos(ruta)
                self.df = df
                self.cargarTabla(df)
                self.tamDf = len(df)
                # Mostrar botón de seleccionar columnas
                self.ui.btnConfirmar.show()
                self.ui.cmbEntrada.show()
                self.ui.cmbSalida.show()
            except ValueError as e:
                msj.crearAdvertencia(self, "Error inesperado",
                    "Se ha producido un error inesperado al cargar el archivo")
            except FileNotFoundError as f:
                msj.crearAdvertencia(self, "Archivo no encontrado",
                    "No se ha encontrado el archivo especificado")
        else:
            msj.crearAdvertencia(self, "Ruta no encontrada",
                "Se debe seleccionar un archivo válido")


    def cargarTablaGenerico(self, df):
        model = mp(df)
        self.ui.tableViewDataFrame.setModel(model)
        self.ui.tableViewDataFrame.resizeColumnsToContents()
        

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
            self.columnas.extend(gd.cargaColumnas(df,False))
            self.ui.cmbEntrada.clear()
            for col in self.columnas[1:]:
                self.ui.cmbEntrada.addItem(col)
            self.ui.cmbSalida.clear()
            self.ui.cmbSalida.addItems(self.columnas)

        except ValueError as e:
            msj.crearAdvertencia(self, "Error inesperado",
                "Se ha producido un error inesperado al crear la tabla")


    def confirmarSeleccion(self):
        if self.df is None:
            msj.crearAdvertencia(self, "Sin datos", "Primero debe cargar un archivo")
            return

        entrada = self.ui.cmbEntrada.getCheckedItems()
        salida = self.ui.cmbSalida.currentText()
        if (salida in entrada):
            msj.crearAdvertencia(self, "Advertencia", "La salida seleccionada ya se encuentra en una de las entradas")
            return
        
        if (len(entrada) >0 and salida != mensajeDefectoCmb):
            msj.crearInformacion(self,"Datos Seleccionados",
                f"Entrada: {', '.join(str(x) for x in entrada)}\nSalida: {salida}")
            conjuntoAnalisis = entrada+[salida]
            # Marcar columnas en el DataFrame (visualmente podríamos colorearlas)
            # CAMBIO IMPORTANTE: Se guarda la columna de entrada como una lista para futura compatibilidad con selección múltiple.
            self.columnasEntrada =  entrada
            self.columnaSalida = salida
            self.marcarColumnasSeleccionadas(self.df)
            #Comprueba si existe algun nulo entre las columnas seleccionadas
            if((lambda df, conjuntoAnalisis: any(df[c].isna().any() for c in conjuntoAnalisis))(self.df, conjuntoAnalisis)):
                #Ponemos que se vean despues de seleccionar
                self.ui.botonDividirTest.hide()
                self.ui.numeroSliderTest.hide()
                self.ui.sliderProporcionTest.hide()
                self.ui.lblDivision.hide()
                self.ui.cmbModelos.hide()
                self.ui.cmbOpcionesPreprocesado.show()
                self.ui.botonAplicarPreprocesado.show()
            else:
                self.ui.botonDividirTest.show()
                self.ui.numeroSliderTest.show()
                self.ui.sliderProporcionTest.show()
                self.ui.lblDivision.show()
                self.ui.cmbModelos.show()
                self.ui.cmbOpcionesPreprocesado.hide()
                self.ui.botonAplicarPreprocesado.hide()
                msj.crearInformacion(self,"Informacion", "No se han encontrado nulos en tus columnas seleccionadas, puedes proceder con el data split")
                
                self.dfProcesado = self.df[conjuntoAnalisis]
                self.cargarTablaGenerico(self.dfProcesado)
                self.marcarColumnasSeleccionadas(self.dfProcesado)
                self.tamDf = len(self.df)
                self.tamDfProc = len(self.dfProcesado)
                if is_numeric_dtype(self.dfProcesado[self.columnaSalida]):
                    self.cargarComboModelos(False)
                else:
                    self.cargarComboModelos(True)

        else:
             msj.crearAdvertencia(self,"Advertencia",
                "Debe seleccionar una columna para la entrada y la salida.")


    def marcarColumnasSeleccionadas(self, dfEntr):
        """
        Marca visualmente las columnas seleccionadas en la tabla.
        OPTIMIZADO: Usa PandasModelConColor con caché precalculado para mejor rendimiento.
        
        Args:
            dfEntr: DataFrame a mostrar con las columnas marcadas
        """
        if self.df is None or self.columnasEntrada is None or self.columnaSalida is None:
            return

        # Asegurar que columnasEntrada sea una lista
        if isinstance(self.columnasEntrada, str):
            columnas_entrada = [self.columnasEntrada]
        else:
            columnas_entrada = self.columnasEntrada

        # OPTIMIZACIÓN: Usar el modelo optimizado con caché precalculado
        # Esto mejora significativamente el rendimiento en DataFrames grandes
        model = PandasModelConColor(
            dfEntr, 
            columna_verde=columnas_entrada,
            columna_roja=self.columnaSalida, 
            tachar_nan=True
        )
        
        self.ui.tableViewDataFrame.setModel(model)
        self.ui.tableViewDataFrame.resizeColumnsToContents()

        # Mostrar todas las columnas de entrada
        if isinstance(columnas_entrada, list):
            entradas_str = ", ".join(columnas_entrada)
        else:
            entradas_str = columnas_entrada
        self.statusBar().showMessage(f"Entrada: {entradas_str} | Salida: {self.columnaSalida}")


    def actualizarColumnasSeleccionadas(self):
        if self.ui.conjuntoTabs.currentIndex() == 1 and self.columnasEntrada is not None and self.columnaSalida is not None:
            entradas_str = ", ".join(self.columnasEntrada)
            self.statusBar().showMessage(f"Entrada: {entradas_str} | Salida: {self.columnaSalida}")
        if self.ui.conjuntoTabs.currentIndex() == 2 and self.columnasEntradaGraficada is not None and self.columnaSalidaGraficada is not None:
            entradas_str = ", ".join(self.columnasEntradaGraficada)
            self.statusBar().showMessage(f"Entrada: {entradas_str} | Salida: {self.columnaSalidaGraficada}")

    # ==================== MÉTODOS DE PREPROCESAMIENTO ====================

    def aplicarPreprocesado(self):
        """
        Aplica la operación de preprocesamiento seleccionada.
        OPTIMIZADO: Usa el modelo optimizado para mostrar los resultados.
        """
        if self.ui.cmbOpcionesPreprocesado.currentText() == "Seleccione un método para preprocesado":
            return

        if self.df is None:
            msj.crearAdvertencia(self, "Sin datos", "No hay datos cargados")
            return

        # Verificar que se hayan seleccionado columnas
        if self.columnasEntrada is None or self.columnaSalida is None:
            msj.crearAdvertencia(self, "Sin columnas seleccionadas",
                "Debe seleccionar las columnas de entrada y salida primero")
            return
        
        opcion = self.ui.cmbOpcionesPreprocesado.currentText()
        cte = 0
        if opcion == "Rellenar con un valor constante":
            cte ,_= QInputDialog.getText(self, "Valor constante", "Introduce el valor constante para rellenar NaN:")
        
        try:  
            self.dfProcesado, mensaje, columnasSeleccionadas = PrepDat.aplicarPreprocesadoCalcular(
                                                                            columnasEntrada = self.columnasEntrada,
                                                                            columnaSalida=self.columnaSalida,
                                                                            df=self.df,
                                                                            opcion=opcion,
                                                                            constante= cte)

            msj.crearInformacion(self, "Preprocesado Aplicado", mensaje)
            self.cargarTablaGenerico(self.dfProcesado)
            self.marcarColumnasSeleccionadas(self.dfProcesado)
            self.tamDfProc = len(self.dfProcesado)
        
            # Mostrar estadísticas del procesamiento
            mensaje = f"Procesamiento completado:\n"
            mensaje += f"Filas: {self.tamDf} → {self.tamDfProc}\n"
            mensaje += f"NaN en columnas seleccionadas: {self.df[columnasSeleccionadas].isna().sum().sum()} → {self.dfProcesado[columnasSeleccionadas].isna().sum().sum()}"
            msj.crearInformacion(self, "Éxito", mensaje)

            # Verificar si hay NaN en las columnas de entrada y salida
            if not self.dfProcesado[columnasSeleccionadas].isnull().values.any():
                # Mostrar botón de dividir datos
                self.ui.botonDividirTest.show()
                self.ui.lblDivision.show()
                self.ui.numeroSliderTest.show()
                self.ui.sliderProporcionTest.show()
                self.ui.lblDatosDivision.show()
                self.ui.cmbModelos.show()
                if is_numeric_dtype(self.dfProcesado[self.columnaSalida]):
                    self.cargarComboModelos(False)
                else:
                    self.cargarComboModelos(True)
            else:
                msj.crearAdvertencia(self, "NaN restantes",
                    "Aún quedan valores NaN en las columnas seleccionadas.\n"
                    "Debe aplicar otro método de preprocesado.")

        except Exception as e:
            msj.crearAdvertencia(self, "Error", f"Error al procesar: {str(e)}")


    # ==================== MÉTODOS DEL DATASPLIT ====================
    def actualizarLblValSlider(self):   #TESTINFO: NO TESTEAR ESTE
        value = self.ui.sliderProporcionTest.value()
        self.ui.numeroSliderTest.setValue(value)
        longitud = self.tamDfProc
        test = float(value)
        train = 100 - test
        self.ui.lblDatosDivision.setText(f"Test: {test}% --- Filas: {round(longitud*test/100)}\nTrain: {train}% --- Filas: {round(longitud*train/100)}")


    def _actualizarPorcentajeTest(self):        #TESTINFO: NO TESTEAR ESTE
        """Actualiza la proporción de test según el valor del slider"""
        value = self.ui.sliderProporcionTest.value()
        self.proporcionDeTest = float(value) / 100


    def _actualizarPorcentajeSpin(self):        #TESTINFO: NO TESTEAR ESTE
        """Actualiza la proporción de test del slider el valor del spin"""
        value = self.ui.numeroSliderTest.value()
        self.ui.sliderProporcionTest.setValue(value)
        self.proporcionDeTest = float(value) / 100


    def procesoDataSplit(self): #TESTINFO: NO TESTEAR ESTE
        """Realiza el proceso de datasplit y muestra los resultados"""
        try:
            # Actualizar la proporción según el slider
            self._actualizarPorcentajeTest()

            # Ejecutar el datasplit
            self.dataFrameTrain, self.dataFrameTest = ProcDat._ejecutarDatasplit(self.dfProcesado, self.columnasEntrada, self.columnaSalida, self.proporcionDeTest)

            # Mostrar los resultados si el split fue exitoso
            if self.dataFrameTrain is not None and self.dataFrameTest is not None:
                mensajeTrain, mensajeTest = ProcDat._mostrarResultadosSplit(self.dataFrameTrain, self.dataFrameTest, self.tamDfProc)
                msj.crearInformacion(self, "División Completada",
                            f"{mensajeTrain}\n{mensajeTest}")

        except TypeError as mensaje:
            msj.crearAdvertencia(self, "Presencia de Nulos", str(mensaje))
            return
        
        except Exception as e:
            msj.crearAdvertencia(self, "Error", f"Error al procesar: {str(e)}")

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
                "columnasEntrada": self.columnasEntradaGraficada,
                "columnaSalida": self.columnaSalidaGraficada,
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


    def pipelineModelo(self):
        """
        Genera el modelo y grafica.
        FIX: Limpia el buffer de inputs anteriores para evitar predicciones fantasma.
        """
        if(self.ui.cmbModelos.currentText() == "--- Seleccione un Entrenamiento---"):
            return
        
        self.procesoDataSplit()
        
        # Transición
        self.transicion.cambiarPagina(1)
        
        self.columnasEntradaGraficada = self.columnasEntrada
        self.columnaSalidaGraficada = self.columnaSalida

        if hasattr(self, 'datosEntrada'):
            self.datosEntrada.clear()

        # Info Barra Estado
        entradas_str = ", ".join(self.columnasEntradaGraficada)
        self.statusBar().showMessage(f"Entrada: {entradas_str} | Salida: {self.columnaSalidaGraficada}")

        if self.ui.placeholderGrafica.layout() is not None or self.ui.placeholderCorrelacion.layout() is not None:
            self.limpiarGrafica()

        try: 
            nombre_modelo = self.ui.cmbModelos.currentText() 

            # Ajustar Modelo (Llamada al Backend)
            # Asegúrate de usar 'ProcDat' o como hayas importado tu módulo de procesamiento
            self.xTrain, self.yTrain, self.xTest, self.yTest, self.modelo, self.yTrainPred, self.yTestPred, self.r2Train, self.r2Test, self.ecmTrain, self.ecmTest, esGraficable = ProcDat.crearAjustarModelo(
                self.dataFrameTrain, 
                self.dataFrameTest,
                self.columnasEntradaGraficada, 
                self.columnaSalidaGraficada, 
                nombre_modelo
            )       
            
            if esGraficable:
                self.plotGrafica()
                self.plotCorrelacion()

            self.ui.placeholderCorrelacion.show()

            # Formateo de métricas
            def fmt(valor):
                return f"{valor:.4f}" if isinstance(valor, (int, float)) else str(valor)

            self.ui.labelR2Test.setText(
                f"R**2 Entrenamiento: {fmt(self.r2Train)}\n"
                f"R**2 Test: {fmt(self.r2Test)}\n\n"
                f"ECM Entrenamiento: {fmt(self.ecmTrain)}\n"
                f"ECM Test: {fmt(self.ecmTest)}"
            )

            # Fórmula
            if hasattr(self.modelo, 'coef_') and hasattr(self.modelo, 'intercept_'):
                try:
                    b = self.modelo.intercept_
                    m = self.modelo.coef_
                    if hasattr(b, '__len__'): b = b[0]
                    if hasattr(m, '__len__'): m = m[0]
                    self.ui.labelFormula.setText(f"Fórmula Modelo: y = {b:.4f} + {m:.4f}*x")
                except:
                    self.ui.labelFormula.setText("Fórmula: Estructura compleja")
            else:
                self.ui.labelFormula.setText("Fórmula: No aplicable")

            # Mostrar controles
            self.ui.propiedadesModelo.show()
            self.ui.btnGuardarModelo.show()
            self.ui.textDescribirModelo.clear()
            self.ui.textDescribirModelo.show()
            self.ui.btnAplicarPrediccion.show()
            
            if len(self.columnasEntradaGraficada) > 0:
                self.ui.labelEntradaActual.setText(f"Ingrese valor para {self.columnasEntradaGraficada[0]}")
            else:
                self.ui.labelEntradaActual.setText("Ingrese valor")
                
            self.ui.labelEntradaActual.show()
            self.ui.spinBoxEntrada.show()
            self.ui.labelPrediccion.hide()

        except TypeError as mensaje:
            msj.crearAdvertencia(self, "Error de datos", str(mensaje))
            return
        
        except Exception as e:
            msj.crearAdvertencia(self, "Error", f"Error al procesar: {str(e)}")


    def cargarModelo(self):
        """
        Carga un modelo .pkl y LIMPIA todos los datos residuales del modelo anterior.
        """
        ruta, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Seleccionar modelo", "", "Modelos (*.pkl)"
        )

        if not ruta:
            return

        try:
            with open(ruta, 'rb') as f:
                datos = pk.load(f)
            # Si no ponemos esto a None, plotGrafica creerá que tiene datos válidos
            # e intentará cruzar las columnas de B con los datos de A -> ERROR.
            self.xTrain = None
            self.yTrain = None
            self.xTest = None
            self.yTest = None
            
            # También limpiamos el buffer de entrada para predicciones
            self.datosEntrada.clear() 
            # =================================================================

            # Carga del nuevo modelo (B)
            self.modelo = datos.get("modelo")
            self.columnasEntradaGraficada = datos.get("columnasEntrada")
            self.columnaSalidaGraficada = datos.get("columnaSalida")
            
            # Carga de métricas
            metricas = datos.get("metricas", {})
            self.r2Train = metricas.get("r2Train")
            self.r2Test = metricas.get("r2Test")
            self.ecmTrain = metricas.get("ecmTrain")
            self.ecmTest = metricas.get("ecmTest")
            self.formula = datos.get("formula", "")

            # Formateador seguro para textos/números
            def fmt(val):
                return f"{val:.4f}" if isinstance(val, (int, float)) else str(val)

            # Preparar strings para UI
            if isinstance(self.columnasEntradaGraficada, list):
                entradas_str = ", ".join(self.columnasEntradaGraficada)
                columna_input = self.columnasEntradaGraficada[0]
            else:
                entradas_str = self.columnasEntradaGraficada
                columna_input = self.columnasEntradaGraficada

            # --- Actualizar Interfaz (Tab Visualización) ---
            self.ui.textDescribirModelo.setPlainText(datos.get("descripcion", ""))
            
            self.ui.labelR2Test.setText(
                f"R**2 Entrenamiento: {fmt(self.r2Train)}\n"
                f"R**2 Test: {fmt(self.r2Test)}\n\n"
                f"ECM Entrenamiento: {fmt(self.ecmTrain)}\n"
                f"ECM Test: {fmt(self.ecmTest)}"
            )
            
            self.ui.labelFormula.setText(f"{self.formula}")
            self.ui.propiedadesModelo.show()
            self.ui.btnGuardarModelo.show()
            self.ui.textDescribirModelo.show()
            
            # Configurar inputs de predicción para el nuevo modelo
            self.ui.labelEntradaActual.setText(f"Ingrese valor para {columna_input}")
            self.ui.btnAplicarPrediccion.show()
            self.ui.labelEntradaActual.show()
            self.ui.spinBoxEntrada.show()
            self.ui.labelPrediccion.hide()
            
            self.statusBar().showMessage(f"Entrada: {entradas_str} | Salida: {self.columnaSalidaGraficada}")

            # --- Limpiar UI del modelo anterior ---
            self.limpiarGrafica() # Borra la gráfica vieja
            self.resetearPaginaPreprocesado()

            msj.crearInformacion(self, "Éxito", f"Modelo cargado correctamente:\n{ruta}")

        except (pk.PickleError, EOFError):
            msj.crearAdvertencia(self, "Error de lectura", "El archivo no es un modelo válido o está dañado.")
        except FileNotFoundError:
            msj.crearAdvertencia(self, "Error", "No se encontró el archivo especificado.")
        except Exception as e:
            msj.crearAdvertencia(self, "Error inesperado", f"Ocurrió un error al cargar: {e}")


    def actualizarDatosPrediccion(self):
        nuevaEntrada = self.ui.spinBoxEntrada.value()
        self.datosEntrada.append(nuevaEntrada)
        self.ui.spinBoxEntrada.setValue(0)
                

    def pipelinePrediccion(self):
        """
        Gestor de predicción secuencial.
        """
        if self.modelo is None:
            msj.crearAdvertencia(self, "Error", "No hay modelo disponible.")
            return
        
        # Limpieza de seguridad
        if len(self.datosEntrada) >= len(self.columnasEntradaGraficada):
            self.datosEntrada.clear()

        self.actualizarDatosPrediccion() 
        
        # Si faltan datos, pedir el siguiente y salir
        if len(self.datosEntrada) < len(self.columnasEntradaGraficada):
            siguienteIndice = len(self.datosEntrada)
            nombreColumna = self.columnasEntradaGraficada[siguienteIndice]
            self.ui.labelEntradaActual.setText(f"Ingrese valor para {nombreColumna}")
            return

        # --- PREDICCIÓN ---
        try:
            # Crear DataFrame con nombres (camelCase)
            entradaDf = pd.DataFrame([self.datosEntrada], columns=self.columnasEntradaGraficada)
            
            self.prediccion = self.modelo.predict(entradaDf)
            valorPredicho = self.prediccion[0]
            
            # Formateo texto/número
            columnaSalida = self.columnaSalidaGraficada
            textoPredicho = ""
            
            try:
                valFloat = float(valorPredicho)
                textoPredicho = f"{valFloat:.4f}"
            except (ValueError, TypeError):
                textoPredicho = str(valorPredicho)

            self.ui.labelPrediccion.setText(f"Valor de {columnaSalida} predicho: {textoPredicho}")
            self.ui.labelPrediccion.show()

            self.plotGrafica(puntoPrediccion=(self.datosEntrada, valorPredicho))
            
            # Resetear label para la próxima vez
            primeraColumna = self.columnasEntradaGraficada[0]
            self.ui.labelEntradaActual.setText(f"Ingrese valor para {primeraColumna}")

        except Exception as e:
            msj.crearAdvertencia(self, "Error al predecir", str(e))
            self.datosEntrada.clear() 
            
    # ----------------------------------------------------------------------
    #                       MÉTODOS GRÁFICOS (PLOTLY)
    # ----------------------------------------------------------------------
    def _mostrarPlotlyEnQt(self, fig, placeholder):
        """Helper para incrustar gráficas Plotly en el layout de Qt"""
        self.limpiarLayout(placeholder)
        vistaWeb = QWebEngineView()
        html = fig.to_html(include_plotlyjs='cdn') 
        vistaWeb.setHtml(html)
        layout = QVBoxLayout(placeholder)
        layout.addWidget(vistaWeb)
        placeholder.setLayout(layout)

    def plotGrafica(self, puntoPrediccion=None):
        """
        Orquestador principal para la generación de gráficas 2D/3D.
        """
        nCols = len(self.columnasEntradaGraficada)
        if nCols == 0 or nCols > 2:
            return 
        
        if self.modelo is None:
             return

        fig = go.Figure()

        if nCols == 1:
            self._configurarGrafica2D(fig, puntoPrediccion)
        elif nCols == 2:
            self._configurarGrafica3D(fig, puntoPrediccion)

        self._mostrarPlotlyEnQt(fig, self.ui.placeholderGrafica)


    def _configurarGrafica2D(self, fig, puntoPrediccion):
        """Configura trazas y layout para gráficas 2D (1 variable entrada)."""
        nombreX = self.columnasEntradaGraficada[0]
        
        # 1. Obtener límites y dibujar datos reales si existen
        xMin, xMax = self._dibujarDatosReales2D(fig, nombreX)
        
        # 2. Ajustar límites si solo tenemos un punto de predicción (Modelo cargado)
        #    Si xMin es 0 y xMax es 10, asumimos que es el valor por defecto.
        if puntoPrediccion and xMin == 0 and xMax == 10:
            valX = puntoPrediccion[0][0]
            xMin, xMax = valX - 5, valX + 5

        # 3. Dibujar la línea de tendencia del modelo
        self._dibujarLineaModelo(fig, nombreX, xMin, xMax)

        # 4. Dibujar el punto de predicción actual
        if puntoPrediccion:
            entrada, salida = puntoPrediccion
            self._dibujarPuntoDestacado(fig, x=[entrada[0]], y=[salida], nombre="Predicción Actual")

        # Layout
        fig.update_layout(title="Modelo Regresión 2D", xaxis_title=nombreX, yaxis_title=self.columnaSalidaGraficada)


    def _configurarGrafica3D(self, fig, puntoPrediccion):
        """Configura trazas y layout para gráficas 3D (2 variables entrada)."""
        nombreX, nombreY = self.columnasEntradaGraficada
        
        # 1. Obtener límites y dibujar datos reales si existen
        limites = self._dibujarDatosReales3D(fig, nombreX, nombreY) # (xmin, xmax, ymin, ymax)
        
        # 2. Ajustar límites si es necesario (Modelo cargado con predicción puntual)
        if puntoPrediccion and limites == (0, 10, 0, 10):
            vx, vy = puntoPrediccion[0]
            limites = (vx-5, vx+5, vy-5, vy+5)

        # 3. Dibujar superficie del modelo
        self._dibujarSuperficieModelo(fig, nombreX, nombreY, limites)

        # 4. Dibujar punto de predicción
        if puntoPrediccion:
            entrada, salida = puntoPrediccion
            self._dibujarPuntoDestacado3D(fig, x=[entrada[0]], y=[entrada[1]], z=[salida], nombre="Predicción Actual")

        # Layout
        fig.update_layout(
            title="Modelo Regresión 3D", 
            scene=dict(xaxis_title=nombreX, yaxis_title=nombreY, zaxis_title=self.columnaSalidaGraficada),
            margin=dict(l=0, r=0, b=0, t=40)
        )


    def _configurarGraficaCorrelacion(self, fig):
        """Genera la gráfica clásica de Real vs Predicho para regresión."""
        yPred = self.modelo.predict(self.xTest)
        
        # Puntos
        fig.add_trace(go.Scatter(
            x=self.yTest, y=yPred, 
            mode='markers', name='Datos Test',
            marker=dict(
                color=self.yTest, # Opcional: mantener escala visual
                colorscale='Viridis',
                showscale=True,
                opacity=0.7,
                line=dict(width=0.5, color='DarkSlateGrey')
            )
        ))

        # Línea Ideal
        minVal = min(self.yTest.min(), yPred.min())
        maxVal = max(self.yTest.max(), yPred.max())
        
        fig.add_trace(go.Scatter(
            x=[minVal, maxVal], y=[minVal, maxVal],
            mode='lines', name='Ideal (Perfecto)',
            line=dict(color='black', dash='dash', width=2)
        ))

        fig.update_layout(
            title="Correlación: Real vs Predicho",
            xaxis_title=f"Valor Real ({self.columnaSalidaGraficada})",
            yaxis_title="Valor Predicho",
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
        )


    # --- MÉTODOS HELPER 2D (Privados) ---

    def _dibujarDatosReales2D(self, fig, colX):
        """Dibuja scatter de entrenamiento y test si existen. Retorna (min, max) de X."""
        xMin, xMax = 0, 10 # Valores por defecto

        # Verificamos si existen los datos en memoria (no es un modelo cargado)
        if self.xTrain is not None and self.yTrain is not None:
            xTr = self._extraerColumna(self.xTrain, colX)
            xTe = self._extraerColumna(self.xTest, colX)

            fig.add_trace(go.Scatter(x=xTr, y=self.yTrain, mode='markers', name='Entrenamiento', marker=dict(color='blue', opacity=0.5)))
            fig.add_trace(go.Scatter(x=xTe, y=self.yTest, mode='markers', name='Test', marker=dict(color='orange', opacity=0.5)))
            
            if len(xTr) > 0:
                xMin, xMax = min(xTr.min(), xTe.min()), max(xTr.max(), xTe.max())
        
        return xMin, xMax

    def _dibujarLineaModelo(self, fig, colX, xMin, xMax):
        """Genera la línea de regresión evaluando el modelo."""
        # Calcular margen visual
        padding = (xMax - xMin) * 0.1 if xMax != xMin else 1
        xRange = np.linspace(xMin - padding, xMax + padding, 100)
        
        # Crear DataFrame explícito para respetar nombres de columnas del modelo
        dfRange = pd.DataFrame({colX: xRange})
        
        try:
            yRange = self.modelo.predict(dfRange)
            fig.add_trace(go.Scatter(x=xRange, y=yRange, mode='lines', name='Modelo', line=dict(color='red', width=3)))
        except Exception:
            # Silenciosamente ignoramos si falla la predicción de rango (ej: tipo de dato incompatible)
            pass


    # --- MÉTODOS HELPER 3D (Privados) ---

    def _dibujarDatosReales3D(self, fig, colX, colY):
        """Dibuja scatter 3D de entrenamiento y test si existen. Retorna límites."""
        bounds = (0, 10, 0, 10)

        if self.xTrain is not None and self.yTrain is not None:
            xTr = self._extraerColumna(self.xTrain, colX)
            yTr = self._extraerColumna(self.xTrain, colY)
            zTr = self.yTrain

            xTe = self._extraerColumna(self.xTest, colX)
            yTe = self._extraerColumna(self.xTest, colY)
            zTe = self.yTest

            fig.add_trace(go.Scatter3d(x=xTr, y=yTr, z=zTr, mode='markers', name='Train', marker=dict(size=4, color='blue', opacity=0.5)))
            fig.add_trace(go.Scatter3d(x=xTe, y=yTe, z=zTe, mode='markers', name='Test', marker=dict(size=4, color='orange', opacity=0.5)))
            
            if len(xTr) > 0:
                bounds = (xTr.min(), xTr.max(), yTr.min(), yTr.max())
        
        return bounds

    def _dibujarSuperficieModelo(self, fig, colX, colY, limites):
        """Genera la malla 3D del modelo."""
        xMin, xMax, yMin, yMax = limites
        
        # Crear malla
        xLin = np.linspace(xMin, xMax, 20)
        yLin = np.linspace(yMin, yMax, 20)
        xMesh, yMesh = np.meshgrid(xLin, yLin)
        
        # Aplanar para predecir
        xyFlat = np.c_[xMesh.ravel(), yMesh.ravel()]
        dfMesh = pd.DataFrame(xyFlat, columns=[colX, colY])
        
        try:
            zFlat = self.modelo.predict(dfMesh)
            
            # Solo graficamos superficie si la salida es numérica (para evitar error en clasificación de texto)
            if np.issubdtype(zFlat.dtype, np.number):
                zMesh = zFlat.reshape(xMesh.shape)
                fig.add_trace(go.Surface(z=zMesh, x=xLin, y=yLin, colorscale='Reds', opacity=0.5, name='Modelo', showscale=False))
        except Exception:
            pass

    # --- UTILIDADES ---

    def _extraerColumna(self, data, nombre_col):
        """Extrae una columna de DataFrame o Series de forma segura."""
        if hasattr(data, 'columns'):
            return data[nombre_col]
        # Si es un array de numpy o una serie sin nombre
        return data.iloc[:, 0] if hasattr(data, 'iloc') and data.ndim > 1 else data

    def _dibujarPuntoDestacado(self, fig, x, y, nombre):
        """Dibuja un punto 2D destacado (estrella verde)."""
        fig.add_trace(go.Scatter(
            x=x, y=y, mode='markers', name=nombre,
            marker=dict(color='green', size=15, symbol='star', line=dict(color='black', width=2))
        ))

    def _dibujarPuntoDestacado3D(self, fig, x, y, z, nombre):
        """Dibuja un punto 3D destacado (diamante verde)."""
        fig.add_trace(go.Scatter3d(
            x=x, y=y, z=z, mode='markers', name=nombre,
            marker=dict(color='green', size=12, symbol='diamond', line=dict(color='black', width=2))
        ))

    def plotCorrelacion(self):
        """
        Decide qué gráfica mostrar según el tipo de datos:
        - Datos Numéricos -> Gráfica de Correlación (Real vs Predicho).
        - Datos Categóricos -> Matriz de Confusión.
        """
        # Validación de seguridad
        if self.yTest is None or self.xTest is None:
            msj.crearAdvertencia(self, "Aviso", "Faltan datos de test para generar estadísticas.")
            self.limpiarLayout(self.ui.placeholderCorrelacion)
            return

        fig = go.Figure()

        try:
            # Determinamos si es Clasificación (Texto/Categoría) o Regresión (Números)
            esNumerico = is_numeric_dtype(self.yTest)

            if esNumerico:
                self._configurarGraficaCorrelacion(fig)
            else:
                self._configurarMatrizConfusion(fig)

            self._mostrarPlotlyEnQt(fig, self.ui.placeholderCorrelacion)
            
        except Exception as e:
            msj.crearAdvertencia(self, "Error", f"Error al graficar estadísticas: {e}")

    def _configurarMatrizConfusion(self, fig):
        """Genera una Matriz de Confusión (Heatmap) para modelos de clasificación."""
        yPred = self.modelo.predict(self.xTest)
        
        # Calcular matriz de confusión
        # labels=unique_labels asegura que el orden sea consistente
        labels = sorted(list(set(self.yTest) | set(yPred)))
        cm = confusion_matrix(self.yTest, yPred, labels=labels)
        
        # Invertimos el eje Y para que coincida con la visualización estándar (Origen arriba-izq vs abajo-izq)
        # En plotly heatmaps, a veces es mejor invertirlo para leerlo como matriz clásica.
        # Pero standard plotly: x=Predicted, y=Actual
        
        # Crear Heatmap
        fig.add_trace(go.Heatmap(
            z=cm,
            x=labels,
            y=labels,
            colorscale='Blues',
            showscale=True
        ))

        # Añadir anotaciones de texto (los números dentro de los cuadros)
        annotations = []
        for i, row in enumerate(cm):
            for j, value in enumerate(row):
                annotations.append(dict(
                    x=labels[j],
                    y=labels[i],
                    text=str(value),
                    font=dict(color="white" if value > cm.max()/2 else "black"), # Contraste
                    showarrow=False
                ))
        
        fig.update_layout(
            title="Matriz de Confusión",
            xaxis_title="Valor Predicho",
            yaxis_title="Valor Real",
            annotations=annotations
        )
 
    def limpiarGrafica(self):
        """Limpia los widgets de gráficas"""
        self.limpiarLayout(self.ui.placeholderGrafica)
        self.limpiarLayout(self.ui.placeholderCorrelacion)

    def limpiarLayout(self, widgetPlaceholder):
        """Función auxiliar segura para borrar layouts con WebEngines"""
        if widgetPlaceholder.layout() is not None:
            oldLayout = widgetPlaceholder.layout()
            while oldLayout.count():
                item = oldLayout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
            QWidget().setLayout(oldLayout)
            
if __name__ == "main":
    pass
