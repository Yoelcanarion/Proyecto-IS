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
from PyQt6.QtCore import QCoreApplication, QPropertyAnimation, QEasingCurve
from PyQt6.QtWidgets import QGraphicsOpacityEffect
from MainWindowUI import Ui_MainWindow
import ImportacionDatos as impd
import GestionDatos as gd
import pickle as pk
from UtilidadesInterfaz import PandasModel as mp
from UtilidadesInterfaz import Mensajes as msj
from VentanaCargaCtrl import VentanaCargaCtrl
from UtilidadesInterfaz import PandasModelConColor
from UtilidadesInterfaz import CheckableComboBox
from PyQt6.QtCore import Qt
from transiciones import TransicionPaginas
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

#Globales
mensajeDefectoCmb = "--- Seleccione una columna---"


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
        # Inicializar sistema de transiciones
        self.transicion = TransicionPaginas(self)
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

    def resetearPaginaPreprocesado(self):
        """Resetea los elementos de la página 1"""
        self.ui.tableViewDataFrame.setModel(None)
        self.ui.btnConfirmar.hide()
        self.ui.cmbEntrada.hide()
        self.ui.cmbSalida.hide()
        self.ui.cmbOpcionesPreprocesado.hide()
        self.ui.botonAplicarPreprocesado.hide()


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


    def conectarSenalesPreproceso(self):
        """Conectar señales de los botones y widgets"""
  
        self.ui.btnInsertarArchivo.clicked.connect(self.abrirExplorador)
        self.ui.botonDividirTest.clicked.connect(self.pipelineModelo)
        self.ui.botonAplicarPreprocesado.clicked.connect(self.aplicarPreprocesado)
        self.ui.sliderProporcionTest.valueChanged.connect(self.actualizarLblValSlider)
        self.ui.numeroSliderTest.valueChanged.connect(self.actualizarPorcentajeSpin)
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
        if (len(entrada) >0 and salida != mensajeDefectoCmb):
            msj.crearInformacion(self,"Datos Seleccionados",
                f"Entrada: {', '.join(str(x) for x in entrada)}\nSalida: {salida}")

            # Marcar columnas en el DataFrame (visualmente podríamos colorearlas)
            # CAMBIO IMPORTANTE: Se guarda la columna de entrada como una lista para futura compatibilidad con selección múltiple.
            self.columnasEntrada =  entrada
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


    #MODIFICADO PARA METER MULTIVARIABLES
    def marcarColumnasSeleccionadas(self, dfEntr):
        if self.df is None or self.columnasEntrada is None or self.columnaSalida is None:
            return

        # CAMBIO IMPORTANTE: El código original ya manejaba correctamente una lista aquí, por lo que no se necesitan cambios.
        # Se mantiene la lógica para asegurar que 'columnas_entrada' sea siempre una lista.
        if isinstance(self.columnasEntrada, str):
            columnas_entrada = [self.columnasEntrada]
        else:
            columnas_entrada = self.columnasEntrada

        model = PandasModelConColor(dfEntr, columna_verde=columnas_entrada,
                                    columna_roja=self.columnaSalida, tachar_nan=True)
        self.ui.tableViewDataFrame.setModel(model)
        self.ui.tableViewDataFrame.resizeColumnsToContents()

        # Mostrar todas las columnas de entrada
        # CAMBIO IMPORTANTE: El código original ya formateaba la lista correctamente. No se necesitan cambios.
        if isinstance(columnas_entrada, list):
            entradas_str = ", ".join(columnas_entrada)
        else:
            entradas_str = columnas_entrada
        self.statusBar().showMessage(f"Entrada: {entradas_str} | Salida: {self.columnaSalida}")


    def actualizarColumnasSeleccionadas(self):
        if self.ui.conjuntoTabs.currentIndex() == 1 and self.columnasEntrada is not None and self.columnaSalida is not None:
            # CAMBIO IMPORTANTE: Se formatea la lista de columnas de entrada para mostrarla correctamente en la barra de estado.
            entradas_str = ", ".join(self.columnasEntrada)
            self.statusBar().showMessage(f"Entrada: {entradas_str} | Salida: {self.columnaSalida}")
        if self.ui.conjuntoTabs.currentIndex() == 2 and self.columnasEntradaGraficada is not None and self.columnaSalidaGraficada is not None:
            # CAMBIO IMPORTANTE: Se formatea la lista de columnas de entrada (para la gráfica) para mostrarla en la barra de estado.
            entradas_str = ", ".join(self.columnasEntradaGraficada)
            self.statusBar().showMessage(f"Entrada: {entradas_str} | Salida: {self.columnaSalidaGraficada}")


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
        # CAMBIO IMPORTANTE: La lógica original ya era compatible con 'columnasEntrada' como lista. No se requieren cambios.
        if isinstance(self.columnasEntrada, str):
            columnas_entrada = [self.columnasEntrada]
        else:
            columnas_entrada = self.columnasEntrada

        # Combinar columnas de entrada y salida
        columnas_a_procesar = columnas_entrada + [self.columnaSalida]

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

        # CAMBIO IMPORTANTE: La lógica original ya era compatible con 'columnasEntrada' como lista. No se requieren cambios.
        if isinstance(self.columnasEntrada, str):
            columnas_entrada = [self.columnasEntrada]
        else:
            columnas_entrada = self.columnasEntrada
        columnas_seleccionadas = columnas_entrada + [self.columnaSalida]

        self.dfProcesado = self.df.copy(deep=True)
        opcion = self.ui.cmbOpcionesPreprocesado.currentText()

        try:
            match opcion:
                case "Eliminar filas con NaN":
                    nanAntes = self.dfProcesado[columnas_seleccionadas].isna().sum().sum()
                    # Eliminar filas que tengan NaN en las columnas seleccionadas
                    self.dfProcesado.dropna(subset=columnas_seleccionadas,
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
            mensaje += f"NaN en columnas seleccionadas: {self.df[columnas_seleccionadas].isna().sum().sum()} → {self.dfProcesado[columnas_seleccionadas].isna().sum().sum()}"
            msj.crearInformacion(self, "Éxito", mensaje)

            # Verificar si hay NaN en las columnas de entrada y salida
            if not self.dfProcesado[columnas_seleccionadas].isnull().values.any():
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
        # CAMBIO IMPORTANTE: Se concatena la lista de columnas de entrada con la de salida para formar la lista de columnas a verificar.
        columnas_importantes = self.columnasEntrada + [self.columnaSalida]
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


    def crearAjustarModelo(self):
        """Método usado para crear, ajustar, testear y obtener estadísticas como R**2 y ECM a partir de los datos procesados anteriormente"""
        if self.dataFrameTrain is None or self.dataFrameTest is None:
            msj.crearAdvertencia(self, "Error de datos", "No hay datos de entrenamiento o test disponibles")
            return

        if self.columnasEntradaGraficada is None or self.columnaSalidaGraficada is None:
            msj.crearAdvertencia(self, "Error de columnas", "No se han seleccionado las columnas de entrada y salida")
            return
        # CAMBIO IMPORTANTE: Se selecciona el subconjunto de columnas de entrada directamente usando la lista.
        # El uso de corchetes simples `[]` es suficiente porque `columnasEntradaGraficada` ya es una lista.
        #La salida de xTrain y xTest tiene la forma [[col1, col2,...],[col1, col2,...],...], sean las listas internas 
        # filas de datos ordenadas por su respectiva columna en ese orden (osea que cada lista interna son las coordenadas independientes de un punto del modelo)
        self.xTrain = self.dataFrameTrain[self.columnasEntradaGraficada]        
        self.yTrain = self.dataFrameTrain[self.columnaSalidaGraficada]
        self.xTest = self.dataFrameTest[self.columnasEntradaGraficada]
        self.yTest = self.dataFrameTest[self.columnaSalidaGraficada]

        self.modelo = LinearRegression().fit(self.xTrain, self.yTrain)

        yTrainPred = self.modelo.predict(self.xTrain)  #Tiene la forma [pred1, pred2, ...], siendo pred la predicción de cada muestra de xTrain (con muestras me refiero a las listas internas)
        yTestPred = self.modelo.predict(self.xTest)

        self.r2Train = r2_score(self.yTrain, yTrainPred)
        self.r2Test = r2_score(self.yTest, yTestPred)

        self.ecmTrain = mean_squared_error(self.yTrain, yTrainPred)
        self.ecmTest = mean_squared_error(self.yTest, yTestPred)


    def plotGrafica(self):   #CAMBIOS NECESARIOS
        """Método que se encarga de graficar la regresión lineal con los datos del modelo"""
        # Verificar que el modelo y los datos existen
        if len(self.columnasEntradaGraficada) > 2:
            return
        
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


        # CAMBIO IMPORTANTE: Se extrae el nombre de la primera (y única) columna para graficar en 2D.
        # Esto mantiene la funcionalidad actual pero es consciente de que la variable es una lista.
        if len(self.columnasEntradaGraficada) == 1:
            eje = fig.add_subplot(111)
            self.ui.barraProgreso.setValue(40)

            # Datos
            nombre_columna_x = self.columnasEntradaGraficada[0]
            puntosXTrain = self.xTrain[nombre_columna_x]
            puntosYTrain = self.yTrain
            puntosXTest = self.xTest[nombre_columna_x]
            puntosYTest = self.yTest

            sns.scatterplot(x=puntosXTrain, y=puntosYTrain, color='blue', label='Train', ax=eje)
            sns.scatterplot(x=puntosXTest, y=puntosYTest, color='orange', label='Test', ax=eje)

            # Recta de regresión (línea roja)
            sns.regplot(x=puntosXTrain, y=puntosYTrain, ax=eje, scatter=False, color='red',
                        line_kws={'linewidth': 2, 'label': 'Recta de regresión'})

            #Indicaciones
            eje.set_title("Regresión Lineal", fontsize=14)
            # CAMBIO IMPORTANTE: Se usa el nombre de la columna extraído para la etiqueta del eje X.
            eje.set_xlabel(nombre_columna_x)
            eje.set_ylabel(self.columnaSalidaGraficada)
            eje.legend(  handlelength=1.0,  handletextpad=0.5,  borderpad=0.3,  labelspacing=0.3)
            sns.despine(fig)

        elif len(self.columnasEntradaGraficada) == 2:
                eje = fig.add_subplot(111, projection="3d")
                self.ui.barraProgreso.setValue(40)

                # Extraer las columnas correctamente
                nombre_columna_x = self.columnasEntradaGraficada[0]
                nombre_columna_y = self.columnasEntradaGraficada[1]
                
                # Obtener los datos
                puntosXTrain = self.xTrain[nombre_columna_x]
                puntosYTrain = self.xTrain[nombre_columna_y]
                puntosZTrain = self.yTrain
                
                puntosXTest = self.xTest[nombre_columna_x]
                puntosYTest = self.xTest[nombre_columna_y]
                puntosZTest = self.yTest

                # Graficar en 3D
                eje.scatter(puntosXTrain, puntosYTrain, puntosZTrain, color='blue', label='Train', s=50)
                eje.scatter(puntosXTest, puntosYTest, puntosZTest, color='orange', label='Test', s=50)

                # Graficar el plano de regresión
                x_min, x_max = puntosXTrain.min(), puntosXTrain.max()
                y_min, y_max = puntosYTrain.min(), puntosYTrain.max()
                x_range = np.linspace(x_min - 0.5, x_max + 0.5, 20)
                y_range = np.linspace(y_min - 0.5, y_max + 0.5, 20)
                X_mesh, Y_mesh = np.meshgrid(x_range, y_range)
                XY_mesh = np.c_[X_mesh.ravel(), Y_mesh.ravel()]
                Z_mesh = self.modelo.predict(XY_mesh).reshape(X_mesh.shape)
                eje.plot_surface(X_mesh, Y_mesh, Z_mesh, color='red', alpha=0.5, label='Plano de regresión')

                # Configurar etiquetas
                eje.set_title("Regresión Lineal 3D", fontsize=14)
                eje.set_xlabel(nombre_columna_x)
                eje.set_ylabel(nombre_columna_y)
                eje.set_zlabel(self.columnaSalidaGraficada)
                eje.legend(  handlelength=1.0,  handletextpad=0.5,  borderpad=0.3,  labelspacing=0.3)

        # Añadir al layout
        layout.addWidget(canvas)
        self.ui.placeholderGrafica.setLayout(layout)
        self.ui.barraProgreso.setValue(80)

        # Refrescar
        canvas.draw()
        self.ui.barraProgreso.setValue(100)
        QCoreApplication.processEvents()
        self.ui.barraProgreso.setVisible(False)


    def plotCorrelacion(self):
        """Método que se encarga de graficar la regresión lineal con los datos del modelo"""
        # Verificar que el modelo y los datos existen
        if len(self.columnasEntradaGraficada) > 2:
            return
        
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
        layout = QVBoxLayout(self.ui.placeholderCorrelacion)

        # Crear figura con estilo Seaborn
        sns.set(style="whitegrid", context="talk")
        fig = Figure(figsize=(6, 4))
        canvas = FigureCanvasQTAgg(fig)

        if len(self.columnasEntradaGraficada) == 1:
            eje = fig.add_subplot(111)
            self.ui.barraProgreso.setValue(40)

            # Datos
            puntosXTest = self.xTest
            puntosYTest = self.yTest
            predicciones = self.modelo.predict(puntosXTest)

            #predicciones
            sns.scatterplot(x=puntosYTest, y=predicciones, color='blue', label='Predicciones individuales', ax=eje)

            #Recta de correlación
            sns.regplot(x=puntosYTest, y=predicciones, ax=eje, scatter=False, color='red',
                        line_kws={'linewidth': 2, 'label': 'Recta de regresión'})

            #Indicaciones
            eje.set_title("Gráfica de correlación", fontsize=14)
            eje.set_xlabel("Valores Reales")
            eje.set_ylabel("Valores Predichos")
            eje.legend(  handlelength=1.0,  handletextpad=0.5,  borderpad=0.3,  labelspacing=0.3)
            sns.despine(fig)

        elif len(self.columnasEntradaGraficada) == 2:
                eje = fig.add_subplot(111)
                self.ui.barraProgreso.setValue(40)

                puntosXYTest = self.xTest
                puntosZTest = self.yTest
                predicciones = self.modelo.predict(puntosXYTest)

                #predicciones
                sns.scatterplot(x=puntosZTest, y=predicciones, color='blue', label='Predicciones individuales', ax=eje)

                #Recta de correlación
                sns.regplot(x=puntosZTest, y=predicciones, ax=eje, scatter=False, color='red',
                            line_kws={'linewidth': 2, 'label': 'Recta de regresión'})

                #Indicaciones
                eje.set_title("Gráfica de correlación", fontsize=14)
                eje.set_xlabel("Valores Reales")
                eje.set_ylabel("Valores Predichos")
                eje.legend(  handlelength=1.0,  handletextpad=0.5,  borderpad=0.3,  labelspacing=0.3)
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
        for i in [self.ui.placeholderGrafica, self.ui.placeholderCorrelacion]:
            layout = i.layout()

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
        self.procesoDataSplit()
        self.ui.conjuntoTabs.setCurrentIndex(1)
        self.columnasEntradaGraficada = self.columnasEntrada
        self.columnaSalidaGraficada = self.columnaSalida
        # CAMBIO IMPORTANTE: Se formatea la lista de columnas para la barra de estado.
        entradas_str = ", ".join(self.columnasEntradaGraficada)
        self.statusBar().showMessage(f"Entrada: {entradas_str} | Salida: {self.columnaSalidaGraficada}")
        if self.ui.placeholderGrafica.layout() is not None or self.ui.placeholderCorrelacion.layout() is not None:
            self.limpiarGrafica()
        self.crearAjustarModelo()       
        self.plotGrafica()
        self.plotCorrelacion()
        self.ui.placeholderCorrelacion.show()
        # Solo actualizar UI si todo salió bien
        if self.r2Train is not None and self.r2Test is not None:
            self.ui.labelR2Test.setText(f"R**2 Entrenamiento: {self.r2Train:.4f}\nR**2 Test: {self.r2Test:.4f}\n\nECM Entrenamiento: {self.ecmTrain:.4f}\nECM Test: {self.ecmTest:.4f}")
            self.ui.labelFormula.setText(f"Fórmula Modelo: y = {self.modelo.intercept_:.4f} + {self.modelo.coef_[0]:.4f}*x")
            self.ui.propiedadesModelo.show()
            self.ui.btnGuardarModelo.show()
            self.ui.textDescribirModelo.clear()
            self.ui.textDescribirModelo.show()
            self.ui.btnAplicarPrediccion.show()
            # CAMBIO IMPORTANTE: Se formatea la lista de columnas para mostrarla en la etiqueta.
            self.ui.labelEntradaActual.setText(f"Ingrese valor para {self.columnasEntradaGraficada[0]}")
            self.ui.labelEntradaActual.show()
            self.ui.spinBoxEntrada.show()
            self.ui.labelPrediccion.hide()




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
            self.columnasEntradaGraficada = datos.get("columnasEntrada")
            self.columnaSalidaGraficada = datos.get("columnaSalida")
            metricas = datos.get("metricas", {})
            self.r2Train = metricas.get("r2Train")
            self.r2Test = metricas.get("r2Test")
            self.ecmTrain = metricas.get("ecmTrain")
            self.ecmTest = metricas.get("ecmTest")
            self.formula = datos.get("formula", "")

            # CAMBIO IMPORTANTE: Se prepara la cadena de texto de las columnas de entrada,
            # sea una lista (nuevo formato) o un string (formato antiguo).
            if isinstance(self.columnasEntradaGraficada, list):
                entradas_str = ", ".join(self.columnasEntradaGraficada)
            else:
                entradas_str = self.columnasEntradaGraficada

            # Actualizar tab2
            self.ui.textDescribirModelo.setPlainText(datos.get("descripcion", ""))
            self.ui.labelR2Test.setText(f"R**2 Entrenamiento: {self.r2Train:.4f}\nR**2 Test: {self.r2Test:.4f}\n\nECM Entrenamiento: {self.ecmTrain:.4f}\nECM Test: {self.ecmTest:.4f}")
            self.ui.labelFormula.setText(f"{self.formula}")
            self.ui.propiedadesModelo.show()
            self.ui.btnGuardarModelo.show()
            self.ui.textDescribirModelo.show()
            self.ui.labelEntradaActual.setText(f"Ingrese valor para {self.columnasEntradaGraficada[0]}")# Usar la cadena formateada
            self.ui.btnAplicarPrediccion.show()
            self.ui.labelEntradaActual.show()
            self.ui.spinBoxEntrada.show()
            self.ui.labelPrediccion.hide()
            self.limpiarGrafica()
            self.statusBar().showMessage(f"Entrada: {entradas_str} | Salida: {self.columnaSalidaGraficada}")

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
            self.ui.tableViewDataFrame.setModel(None)
            self.resetearPaginaPreprocesado()

        except (pk.PickleError, EOFError):
            msj.crearAdvertencia(self, "Error de lectura", "El archivo no es un modelo válido o está dañado.")
        except FileNotFoundError:
            msj.crearAdvertencia(self, "Error", "No se encontró el archivo especificado.")
        except Exception as e:
            msj.crearAdvertencia(self, "Error inesperado", f"Ocurrió un error: {e}")

        

#=====================MÉTODOS DE PREDICCIÓN========================#


#El usuario mete los datos en el orden original de las columnas de entrada
#Le da al botón de predecir y se llama a pipelinePrediccion()
#Entran unos datosEntrada en orden con este formato [[120, 3, 5]] (por ejemplo), se crea la predicción de Y y se pone en un label
#Con los datosEntrada se crea una gráfica mediante plotPrediccion
#Según si es creado o cargado, añade la predicción a lo ya graficado o crea la gráfica de 0
#Ya se añadirá una versión para rlm
    def actualizarDatosPrediccion(self):
        nuevaEntrada = self.ui.spinBoxEntrada.value()
        self.datosEntrada.append(nuevaEntrada)
        self.ui.spinBoxEntrada.setValue(0)

    def pipelinePrediccion(self):
        if self.modelo is None:
            msj.crearAdvertencia(self, "Error de datos", "No hay modelo disponible para predicción")
            return

        self.actualizarDatosPrediccion()
        
        #Verifica si aún faltan datos por ingresar
        if len(self.datosEntrada) < len(self.columnasEntradaGraficada):
            siguienteIndice = len(self.datosEntrada)
            self.ui.labelEntradaActual.setText(f"Ingrese valor para {self.columnasEntradaGraficada[siguienteIndice]}")
            return

        # predict espera [lista_de_valores], ya sea [[valor]] para simple o [[valor1, valor2, ...]] para múltiple
        self.prediccion = self.modelo.predict([self.datosEntrada])
        self.ui.labelPrediccion.setText(f"Valor de {self.columnaSalidaGraficada} predicho: {self.prediccion[0]:.4f}")
        self.ui.labelPrediccion.show()
        self.plotPrediccion()
        
        # Limpiar datos de entrada para la próxima predicción
        self.datosEntrada.clear()
        # Resetear el label para la primera columna
        self.ui.labelEntradaActual.setText(f"Ingrese valor para {self.columnasEntradaGraficada[0]}")

    #Hasta aquí todo bien

    def plotPrediccion(self):
        if self.ui.placeholderGrafica.layout() is None: #Crear la gráfica de 0
            if len(self.columnasEntradaGraficada) > 2:
                return
            
            elif len(self.columnasEntradaGraficada) == 1:
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

                # Graficar solo el punto de predicción inicialmente
                sns.scatterplot(x=[self.datosEntrada[0]], y=self.prediccion, color='green', s=200, marker='*',
                            label='Predicción', edgecolor='black', linewidth=1.5,
                            ax=eje, zorder=5, legend=True)

                #Crear la recta de regresión
                xMin, xMax = eje.get_xlim()
                xLine = np.linspace(xMin, xMax, 100).reshape(-1, 1)
                yLine = self.modelo.intercept_ + self.modelo.coef_[0] * xLine
                eje.plot(xLine, yLine, color="red", linewidth=2, label="Recta de regresión")

                # Indicaciones
                eje.set_title("Regresión Lineal", fontsize=14)
                # CAMBIO IMPORTANTE: Se accede al primer elemento de la lista para la etiqueta del eje X.
                eje.set_xlabel(self.columnasEntradaGraficada[0])
                eje.set_ylabel(self.columnaSalidaGraficada)
                eje.legend(  handlelength=1.0,  handletextpad=0.5,  borderpad=0.3,  labelspacing=0.3)
                sns.despine(fig)

            elif len(self.columnasEntradaGraficada) == 2:
                self.ui.barraProgreso.setVisible(True)
                self.ui.barraProgreso.setValue(0)
                QCoreApplication.processEvents()

                layout = QVBoxLayout(self.ui.placeholderGrafica)

                # Crear figura con estilo Seaborn
                sns.set(style="whitegrid", context="talk")
                fig = Figure(figsize=(6, 4))
                canvas = FigureCanvasQTAgg(fig)
                eje = fig.add_subplot(111, projection = "3d")
                self.ui.barraProgreso.setValue(40)
            #predicciones
                eje.scatter(self.datosEntrada[0], self.datosEntrada[1], self.prediccion, color = "green", label = "Predicción", marker = "*", s = 200, edgecolor = "black", linewidth = 1.5)

                xMin, xMax = eje.get_xlim()
                yMin, yMax = eje.get_ylim()
                X, Y = np.meshgrid(np.linspace(xMin, xMax, 100), np.linspace(yMin, yMax, 100))
                Z = self.modelo.coef_[0] * X + self.modelo.coef_[1] * Y + self.modelo.intercept_
                eje.plot_surface(X, Y, Z, color='red', alpha=0.5, label='Plano de regresión')

                eje.set_title("Regresión Lineal 3D", fontsize=14)
                eje.set_xlabel(self.columnasEntradaGraficada[0])
                eje.set_ylabel(self.columnasEntradaGraficada[1])
                eje.set_zlabel(self.columnaSalidaGraficada)
                eje.legend(  handlelength=1.0,  handletextpad=0.5,  borderpad=0.3,  labelspacing=0.3)

                # Añadir al layout
            layout.addWidget(canvas)
            self.ui.placeholderGrafica.setLayout(layout)
            self.ui.barraProgreso.setValue(80)

            # Refrescar
            canvas.draw()
            self.ui.barraProgreso.setValue(100)
            QCoreApplication.processEvents()
            self.ui.barraProgreso.setVisible(False)


        else: #Añadir el punto de predicción a lo ya existente
            if len(self.columnasEntradaGraficada) > 2:
                return    


            elif len(self.columnasEntradaGraficada) == 1:
                layout = self.ui.placeholderGrafica.layout()
                canvas = layout.itemAt(0).widget() #Con esto obtenemos el canvas
                fig = canvas.figure
                eje = fig.axes[0]

                #NOTA PARA CASA: x e y deben tener el formato [valores], y ese ya es el formato base de self.datosEntrada y self.prediccion
                # Graficar el punto de predicción con seaborn
                # Verificar si ya existe 'Predicción' en la leyenda
                handles, labels = eje.get_legend_handles_labels()
                labelAUsar = 'Predicción' if 'Predicción' not in labels else None

                sns.scatterplot(x=[self.datosEntrada[0]], y=self.prediccion, color='green', s=200, marker='*',
                            label=labelAUsar, edgecolor='black', linewidth=1.5,
                            ax=eje, zorder=5, legend=False)

                # Actualizar la leyenda solo si hay labels
                if labelAUsar or handles:
                    eje.legend(handlelength=1.0,  handletextpad=0.5,  borderpad=0.3,  labelspacing=0.3)

                canvas.draw()
            

            elif len(self.columnasEntradaGraficada) == 2:
                layout = self.ui.placeholderGrafica.layout()
                canvas = layout.itemAt(0).widget() #Con esto obtenemos el canvas
                fig = canvas.figure
                eje = fig.axes[0]

                #NOTA PARA CASA: x e y deben tener el formato [valores], y ese ya es el formato base de self.datosEntrada y self.prediccion
                # Graficar el punto de predicción con seaborn
                # Verificar si ya existe 'Predicción' en la leyenda
                handles, labels = eje.get_legend_handles_labels()
                labelAUsar = 'Predicción' if 'Predicción' not in labels else None

                eje.scatter(self.datosEntrada[0], self.datosEntrada[1], self.prediccion, color = "green", label = labelAUsar, marker = "*", s = 200, edgecolor = "black", linewidth = 1.5)

                if labelAUsar or handles:
                    eje.legend(handlelength=1.0,  handletextpad=0.5,  borderpad=0.3,  labelspacing=0.3)

                canvas.draw()



if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = MainWindowCtrl()
    ventana.show()
    sys.exit(app.exec())