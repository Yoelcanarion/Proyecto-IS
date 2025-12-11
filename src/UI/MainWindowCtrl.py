import pandas as pd
from pandas.api.types import is_numeric_dtype
from PyQt6.QtWidgets import QMainWindow, QFileDialog, QInputDialog
from PyQt6 import QtWidgets
from UI.MainWindowUI import Ui_MainWindow
import Backend.ImportacionDatos as impd
import Backend.GestionDatos as gd
import pickle as pk
from UI.UtilidadesInterfaz import PandasModel as mp
from UI.UtilidadesInterfaz import Mensajes as msj
from UI.UtilidadesInterfaz import PandasModelConColor
from UI.UtilidadesInterfaz import CheckableComboBox
from Backend import PreprocesamientoDatos as PrepDat
from Backend import ProcesadoDatos as ProcDat
from Backend.PlotGraficas import plotCorrelacion, plotGrafica, limpiarGrafica

#Globales
mensajeDefectoCmb = "--- Selecciona las columnas de Salida ---"




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
        self.dicColumnaSalida = None
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
        limpiarGrafica(self.ui.placeholderGrafica, self.ui.placeholderCorrelacion)

    def cargarComboModelos(self, esCategorico):
        """
        Carga el ComboBox de modelos disponibles basándose en la naturaleza de los datos.
        Lógica simplificada mediante composición de listas.
        """
        self.ui.cmbModelos.clear()
        self.ui.lblTipoModelo.show()
        self.ui.lblTipoModelo.setText("")
        self.dicColumnaSalida= None
        self.ui.cmbModelos.addItem("---Seleccione un Entrenamiento---")

        # 1. Definición de Grupos de Modelos
        MODELOS_REGRESION = [
            "Regresión Lineal", "Regresión Polinómica", 
            "SVR", "Árbol de Decisión", "KNN"
        ]
        MODELOS_CLASIFICACION = [
            "Regresión Logística", "Árbol de Decisión (Clasif)", 
            "KNN (Clasificación)"
        ]
        MODELOS_BINARIOS = ["Regresión Logística Binaria"]

        # 2. Detección de estado
        esBinario = self.dfProcesado[self.columnaSalida].nunique() == 2
        listaModelos = []

        # 3. Lógica de Decisión
        if esCategorico:
            self.ui.lblTipoModelo.setText("Tipo de Modelo: Clasificacion")
            listaModelos = MODELOS_CLASIFICACION
            
            if esBinario:
                self.ui.lblTipoModelo.setText("Tipo de Modelo: Clasificacion")
                listaModelos += MODELOS_BINARIOS
                aceptarTransformacion = self.msj.crearEncuestaSimple(
                    self,
                    "Datos Binarios Detectados",
                    "Su salida es binaria pero de texto (ej: 'Sí'/'No').\n"
                    "¿Desea transformarla internamente a numérica (0/1) para poder usar también modelos de Regresión?"
                )
                
                if aceptarTransformacion:
                    self.ui.lblTipoModelo.setText("Tipo de Modelo: Regresion y Clasificacion")
                    self.dicColumnaSalida = gd.transformarColumnaBinariaAuto(self.dfProcesado,self.columnaSalida) 
                    listaModelos += MODELOS_REGRESION

        else:
            # Caso Numérico
            if esBinario:
                self.ui.lblTipoModelo.setText("Tipo de Modelo: Regresion y Clasificacion")
                listaModelos = MODELOS_CLASIFICACION + MODELOS_BINARIOS + MODELOS_REGRESION
            else:
                self.ui.lblTipoModelo.setText("Tipo de Modelo: Regresion")
                listaModelos = MODELOS_REGRESION

        # 4. Carga final
        self.ui.cmbModelos.addItems(listaModelos)

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
        self.ui.lblTipoModelo.hide()
    

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
        self.ui.lblTipoModelo.hide()


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
            self.ui.lblTipoModelo.hide()
            #Comprueba si existe algun nulo entre las columnas seleccionadas
            if((lambda df, conjuntoAnalisis: any(df[c].isna().any() for c in conjuntoAnalisis))(self.df, conjuntoAnalisis)):
                #Ponemos que se vean despues de seleccionar
                self.ui.botonDividirTest.hide()
                self.ui.numeroSliderTest.hide()
                self.ui.sliderProporcionTest.hide()
                self.ui.lblDivision.hide()
                self.ui.cmbModelos.hide()
                self.ui.lblDatosDivision.hide()
                self.ui.cmbOpcionesPreprocesado.show()
                self.ui.botonAplicarPreprocesado.show()
            else:
                self.ui.botonDividirTest.show()
                self.ui.numeroSliderTest.show()
                self.ui.sliderProporcionTest.show()
                self.ui.lblDivision.show()
                self.ui.cmbModelos.show()
                self.ui.lblDatosDivision.show()
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

            parametros["dicColumnaSalida"] = self.dicColumnaSalida
            
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
        if(self.ui.cmbModelos.currentText() == "---Seleccione un Entrenamiento---"): return
        
        self.procesoDataSplit()
        # CAMBIO REALIZADO AQUÍ: Se eliminó la transición y se usa setCurrentIndex
        self.ui.conjuntoTabs.setCurrentIndex(1)
        
        self.columnasEntradaGraficada = self.columnasEntrada
        self.columnaSalidaGraficada = self.columnaSalida

        if hasattr(self, 'datosEntrada'): self.datosEntrada.clear()

        entradas_str = ", ".join(self.columnasEntradaGraficada)
        self.statusBar().showMessage(f"Entrada: {entradas_str} | Salida: {self.columnaSalidaGraficada}")
        limpiarGrafica(self.ui.placeholderGrafica, self.ui.placeholderCorrelacion)

        try: 
            nombre_modelo = self.ui.cmbModelos.currentText() 

            self.xTrain, self.yTrain, self.xTest, self.yTest, \
            self.modelo, self.yTrainPred, self.yTestPred, \
            self.r2Train, self.r2Test, self.ecmTrain, self.ecmTest, \
            self.accTrain, self.accTest, esGraficable = ProcDat.crearAjustarModelo(
                self.dataFrameTrain, self.dataFrameTest, self.columnasEntradaGraficada, self.columnaSalidaGraficada, nombre_modelo
            )       
            
            if esGraficable:
                plotGrafica(self.xTrain, self.yTrain, self.xTest, self.yTest, self.columnasEntradaGraficada, self.columnaSalidaGraficada, self.dicColumnaSalida, self.modelo, self.ui.placeholderGrafica)
                plotCorrelacion(self, self.modelo, self.xTest, self.yTest, self.columnaSalidaGraficada, self.dicColumnaSalida, self.ui.placeholderCorrelacion)

            self.ui.placeholderCorrelacion.show()

            def fmt(v): return f"{v:.4f}" if isinstance(v, (int, float)) else "N/A"

            textoMetricas = ""
            if self.r2Train is not None:
                textoMetricas += f"R² Train: {fmt(self.r2Train)}\nR² Test: {fmt(self.r2Test)}\n"
                textoMetricas += f"ECM Train: {fmt(self.ecmTrain)}\nECM Test: {fmt(self.ecmTest)}"
            
            if self.accTrain is not None:
                if textoMetricas: textoMetricas += "\n\n"
                textoMetricas += f"Accuracy Train: {fmt(self.accTrain)}\nAccuracy Test: {fmt(self.accTest)}"

            self.ui.labelR2Test.setText(textoMetricas)

            textoFormula = gd.generarTextoFormula(self.modelo, self.columnasEntradaGraficada)
            self.ui.labelFormula.setText(textoFormula)

            self.ui.propiedadesModelo.show()
            self.ui.btnGuardarModelo.show()
            self.ui.textDescribirModelo.clear()
            self.ui.textDescribirModelo.show()
            self.ui.btnAplicarPrediccion.show()
            self.ui.labelEntradaActual.setText(f"Ingrese valor para {self.columnasEntradaGraficada[0]}")
            self.ui.labelEntradaActual.show()
            self.ui.spinBoxEntrada.show()
            self.ui.labelPrediccion.hide()

        except TypeError as m: msj.crearAdvertencia(self, "Error Datos", str(m))
        except Exception as e: msj.crearAdvertencia(self, "Error", f"Proceso fallido: {e}")


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
            self.dicColumnaSalida = None
            
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
            
            #Carga el auxiliar
            try:
                self.dicColumnaSalida = datos.get("dicColumnaSalida")
            except:
                print("Estas cargando un modelo deprecado")

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
            limpiarGrafica(self.ui.placeholderGrafica, self.ui.placeholderCorrelacion) # Borra la gráfica vieja
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
            
            columnaSalida = self.columnaSalidaGraficada
            textoPredicho = ""
            
            # === LÓGICA DE TRADUCCIÓN CATEGÓRICA ===
            if self.dicColumnaSalida is not None:
                # Si hay diccionario, hacemos búsqueda inversa: Valor (0/1) -> Clave (Texto)
                # 'next' busca la primera clave 'k' cuyo valor 'v' coincida con la predicción.
                textoPredicho = next((k for k, v in self.dicColumnaSalida.items() if v == valorPredicho), str(valorPredicho))
            else:
                # Si NO hay diccionario, intentamos formatear como número flotante
                try:
                    valFloat = float(valorPredicho)
                    textoPredicho = f"{valFloat:.4f}"
                except (ValueError, TypeError):
                    textoPredicho = str(valorPredicho)

            # Actualizar UI
            self.ui.labelPrediccion.setText(f"Valor de {columnaSalida} predicho: {textoPredicho}")
            self.ui.labelPrediccion.show()

            # Graficar (Pasamos 'valorPredicho' numérico para que se pinte bien en los ejes)
            plotGrafica(self.xTrain, self.yTrain, self.xTest, self.yTest, self.columnasEntradaGraficada, self.columnaSalidaGraficada, self.dicColumnaSalida, self.modelo, self.ui.placeholderGrafica, puntoPrediccion=(self.datosEntrada, valorPredicho))
            
            # Resetear label para la próxima vez
            primeraColumna = self.columnasEntradaGraficada[0]
            self.ui.labelEntradaActual.setText(f"Ingrese valor para {primeraColumna}")

        except Exception as e:
            msj.crearAdvertencia(self, "Error al predecir", str(e))
            self.datosEntrada.clear()
        
if __name__ == "main":
    pass