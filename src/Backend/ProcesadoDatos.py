import pandas as pd
import numpy as np
from pandas.api.types import is_numeric_dtype, is_string_dtype, is_object_dtype
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline
from sklearn.svm import SVR
from sklearn.tree import DecisionTreeRegressor
from sklearn.neighbors import KNeighborsRegressor
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.tree import DecisionTreeRegressor, DecisionTreeClassifier
from sklearn.neighbors import KNeighborsRegressor, KNeighborsClassifier

###################################     MÉTODOS PRIVADOS DE VALIDACIÓN Y LÓGICA     ####################################

def _validarDatosNumericos(df, nombre="entrada"):
    """Verifica que las columnas sean numéricas. Lanza error si hay texto."""
    if isinstance(df, pd.Series):
        if not is_numeric_dtype(df):
            raise ValueError(f"Los datos de {nombre} deben ser numéricos. Se detectó texto o categorías.")
    else:
        for col in df.columns:
            if not is_numeric_dtype(df[col]):
                raise ValueError(f"La columna '{col}' de {nombre} contiene datos no numéricos.")

def _validarDatosRegresion(y):
    """Para modelos de regresión, la salida Y debe ser numérica."""
    if not is_numeric_dtype(y):
        raise ValueError("Incompatibilidad: Modelo de REGRESIÓN requiere salida numérica. Usa Regresión Logística para texto/categorías.")

def _validarDatosClasificacion(y):
    """Para modelos de clasificación, la salida Y debe ser categórica o discreta."""
    if is_string_dtype(y) or is_object_dtype(y):
        return
    n_unicos = y.nunique()
    if n_unicos > 20: 
        raise ValueError(f"Incompatibilidad: La columna objetivo tiene {n_unicos} valores numéricos distintos. Parece continua. Usa un modelo de Regresión.")

def _calcularMetricasRegresion(yTrue, yPred):
    """Calcula R2 y ECM."""
    r2 = r2_score(yTrue, yPred)
    ecm = mean_squared_error(yTrue, yPred)
    return r2, ecm

# --- FUNCIONES DE EJECUCIÓN DE MODELOS (Ahora devuelven el objeto modelo) ---

def ejecutarRegresionLineal(xTrain, yTrain, xTest, yTest):
    _validarDatosNumericos(xTrain, "Entrada (X)")
    _validarDatosRegresion(yTrain)
    
    modelo = LinearRegression()
    modelo.fit(xTrain, yTrain)
    
    yTrainPred = modelo.predict(xTrain)
    yTestPred = modelo.predict(xTest)
    r2Train, ecmTrain = _calcularMetricasRegresion(yTrain, yTrainPred)
    r2Test, ecmTest = _calcularMetricasRegresion(yTest, yTestPred)
    
    # Devolvemos modelo al principio
    return modelo, yTrainPred, yTestPred, r2Train, r2Test, ecmTrain, ecmTest

def ejecutarRegresionPolinomica(xTrain, yTrain, xTest, yTest):
    _validarDatosNumericos(xTrain, "Entrada (X)")
    _validarDatosRegresion(yTrain)

    modelo = make_pipeline(PolynomialFeatures(degree=2), LinearRegression())
    modelo.fit(xTrain, yTrain)
    
    yTrainPred = modelo.predict(xTrain)
    yTestPred = modelo.predict(xTest)
    r2Train, ecmTrain = _calcularMetricasRegresion(yTrain, yTrainPred)
    r2Test, ecmTest = _calcularMetricasRegresion(yTest, yTestPred)
    
    return modelo, yTrainPred, yTestPred, r2Train, r2Test, ecmTrain, ecmTest

def ejecutarSVR(xTrain, yTrain, xTest, yTest):
    _validarDatosNumericos(xTrain, "Entrada (X)")
    _validarDatosRegresion(yTrain)

    modelo = SVR(kernel='rbf')
    modelo.fit(xTrain, yTrain)
    
    yTrainPred = modelo.predict(xTrain)
    yTestPred = modelo.predict(xTest)
    r2Train, ecmTrain = _calcularMetricasRegresion(yTrain, yTrainPred)
    r2Test, ecmTest = _calcularMetricasRegresion(yTest, yTestPred)
    
    return modelo, yTrainPred, yTestPred, r2Train, r2Test, ecmTrain, ecmTest

def ejecutarArbolDecision(xTrain, yTrain, xTest, yTest):
    _validarDatosNumericos(xTrain, "Entrada (X)")
    _validarDatosRegresion(yTrain)

    modelo = DecisionTreeRegressor(max_depth=5)
    modelo.fit(xTrain, yTrain)
    
    yTrainPred = modelo.predict(xTrain)
    yTestPred = modelo.predict(xTest)
    r2Train, ecmTrain = _calcularMetricasRegresion(yTrain, yTrainPred)
    r2Test, ecmTest = _calcularMetricasRegresion(yTest, yTestPred)
    
    return modelo, yTrainPred, yTestPred, r2Train, r2Test, ecmTrain, ecmTest

def ejecutarKNN(xTrain, yTrain, xTest, yTest):
    _validarDatosNumericos(xTrain, "Entrada (X)")
    _validarDatosRegresion(yTrain)

    modelo = KNeighborsRegressor(n_neighbors=5)
    modelo.fit(xTrain, yTrain)
    
    yTrainPred = modelo.predict(xTrain)
    yTestPred = modelo.predict(xTest)
    r2Train, ecmTrain = _calcularMetricasRegresion(yTrain, yTrainPred)
    r2Test, ecmTest = _calcularMetricasRegresion(yTest, yTestPred)
    
    return modelo, yTrainPred, yTestPred, r2Train, r2Test, ecmTrain, ecmTest

def ejecutarRegresionLogistica(xTrain, yTrain, xTest, yTest):
    _validarDatosNumericos(xTrain, "Entrada (X)")
    _validarDatosClasificacion(yTrain)

    modelo = LogisticRegression(max_iter=1000)
    modelo.fit(xTrain, yTrain)
    
    yTrainPred = modelo.predict(xTrain)
    yTestPred = modelo.predict(xTest)
    
    msg = "No compatible (Clasificación)"
    
    return modelo, yTrainPred, yTestPred, msg, msg, msg, msg

def ejecutarArbolClasificacion(xTrain, yTrain, xTest, yTest):
    """Árbol de Decisión para Clasificación (Categorías)"""
    _validarDatosNumericos(xTrain, "Entrada (X)")
    _validarDatosClasificacion(yTrain)

    modelo = DecisionTreeClassifier(max_depth=5)
    modelo.fit(xTrain, yTrain)
    
    yTrainPred = modelo.predict(xTrain)
    yTestPred = modelo.predict(xTest)
    
    msg = "No compatible (Ver Matriz)"
    return modelo, yTrainPred, yTestPred, msg, msg, msg, msg

def ejecutarKNNClasificacion(xTrain, yTrain, xTest, yTest):
    """KNN para Clasificación (Categorías)"""
    _validarDatosNumericos(xTrain, "Entrada (X)")
    _validarDatosClasificacion(yTrain)

    modelo = KNeighborsClassifier(n_neighbors=5)
    modelo.fit(xTrain, yTrain)
    
    yTrainPred = modelo.predict(xTrain)
    yTestPred = modelo.predict(xTest)
    
    msg = "No compatible (Ver Matriz)"
    return modelo, yTrainPred, yTestPred, msg, msg, msg, msg

# --- DICCIONARIO CONFIGURACIÓN ---
configuracionModelos = {
    "Regresión Lineal":      {"funcion": ejecutarRegresionLineal,     "esGraficable": True},
    "Regresión Polinómica":  {"funcion": ejecutarRegresionPolinomica, "esGraficable": True},
    "SVR":                   {"funcion": ejecutarSVR,                 "esGraficable": True},
    "Árbol de Decisión":     {"funcion": ejecutarArbolDecision,       "esGraficable": True},
    "KNN":                   {"funcion": ejecutarKNN,                 "esGraficable": True},
    "Regresión Logística":   {"funcion": ejecutarRegresionLogistica,  "esGraficable": True},
    "Árbol de Decisión (Clasif)":{"funcion": ejecutarArbolClasificacion,   "esGraficable": True},
    "KNN (Clasificación)":       {"funcion": ejecutarKNNClasificacion,     "esGraficable": True}
}


###################################     MÉTODOS DE DATASPLIT     ####################################

#Entradas: pd.DatFrame, List[str], str, float -> Salidas: Tuple[pd.DataFrame, pd.DataFrame]
def _ejecutarDatasplit(dfProcesado, columnasEntrada, columnaSalida, tamañoTest):
    """Realiza el datasplit en dataFrameTrain y dataFrameTest"""
    try:
        # Verificar que no hay nulos en las columnas seleccionadas
        columnas_importantes = columnasEntrada + [columnaSalida]
        if dfProcesado[columnas_importantes].isnull().values.any() == True:
            raise TypeError("Para continuar al datasplit no puede tener nulos en las columnas de entrada o salida")
            
        dataFrameTrain, dataFrameTest = train_test_split(dfProcesado, test_size= tamañoTest)

    except Exception as e:
        raise Exception
    
    return dataFrameTrain, dataFrameTest


#Entradas: pd.DataFrame, pd.DataFrame, int -> Salidas: Tuple[str, str]
def _mostrarResultadosSplit(dataFrameTrain, dataFrameTest, tamDfProc):
    """Calcula las líneas de cada parte y su porcentaje real y lo muestra"""
    try:
        # Líneas y porcentaje de líneas del entrenamiento
        porcentajeTrain = (len(dataFrameTrain) / tamDfProc) * 100
        mensajeTrain = f"{len(dataFrameTrain)} Líneas de Entrenamiento --- {porcentajeTrain:.2f}% de los datos"

        # Líneas y porcentaje de líneas del test
        porcentajeTest = 100 - porcentajeTrain
        mensajeTest = f"{len(dataFrameTest)} Líneas de Test --- {porcentajeTest:.2f}% de los datos"

    except Exception as e:
        raise Exception
    
    return mensajeTrain, mensajeTest


##################################      MÉTODOS DE MODELADO     #####################################

#Entradas: pd.DataFrame, pd.DataFrame, List[str], str, str -> Salidas: Tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series, object, np.ndarray, np.ndarray, float, float, float, float, bool]
def crearAjustarModelo(dataFrameTrain, dataFrameTest, columnasEntradaGraficada, columnaSalidaGraficada, nombreModelo):
    """
    Método para ajustar modelo seleccionado, validar datos y obtener métricas.
    Devuelve datos, MODELO, predicciones, métricas y flag de graficación.
    """
    try:
        if dataFrameTrain is None or dataFrameTest is None:
            raise TypeError("No hay datos de entrenamiento o test disponibles")

        if columnasEntradaGraficada is None or columnaSalidaGraficada is None:
            raise TypeError("Las columnas de entrada o salida son nulas")
        
        # 1. Preparar Datos
        xTrain = dataFrameTrain[columnasEntradaGraficada]
        yTrain = dataFrameTrain[columnaSalidaGraficada]
        xTest = dataFrameTest[columnasEntradaGraficada]
        yTest = dataFrameTest[columnaSalidaGraficada]

        # 2. Buscar configuración del modelo
        config = configuracionModelos.get(nombreModelo)
        if not config:
            raise ValueError(f"El modelo '{nombreModelo}' no se encuentra en la configuración.")

        funcionModelo = config["funcion"]
        esGraficable = config["esGraficable"]

        # 3. Ejecutar Modelo 
        # IMPORTANTE: Ahora desempaquetamos el 'modelo' también
        modelo, yTrainPred, yTestPred, r2Train, r2Test, ecmTrain, ecmTest = funcionModelo(xTrain, yTrain, xTest, yTest)

    except ValueError as ve:
        # Capturamos errores de validación y los relanzamos
        raise ve
    except Exception as e:
        # Errores genéricos
        raise Exception(f"Error inesperado en el modelado: {e}")
    
    # Devolvemos 'modelo' después de los datos originales
    return xTrain, yTrain, xTest, yTest, modelo, yTrainPred, yTestPred, r2Train, r2Test, ecmTrain, ecmTest, esGraficable