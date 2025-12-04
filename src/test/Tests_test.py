import pytest as pt
import pandas as pd
import numpy as np
import os
import pickle as pk
import sys
# Añade la carpeta raíz del proyecto al sistema de rutas
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.Backend.ProcesadoDatos import crearAjustarModelo
from src.Backend.GestionDatos import crearDiccionarioModelo, crearModeloDisco

# FIXTURES (Datos de Prueba)


@pt.fixture
def dfRegresion():
    """
    Datos para modelos de REGRESIÓN (salida continua).
    Relación simple: y = 2*x + 1
    """
    x = np.linspace(0, 10, 20)
    y = 2 * x + 1
    return pd.DataFrame({'Entrada': x, 'Salida': y})

@pt.fixture
def dfClasificacion():
    """
    Datos para modelos de CLASIFICACIÓN (salida discreta/binaria).
    Clase 0 si x < 5, Clase 1 si x >= 5
    """
    x = np.linspace(0, 10, 20)
    y = [0 if val < 5 else 1 for val in x]
    return pd.DataFrame({'Entrada': x, 'Salida': y})

@pt.fixture
def rutaModelo(tmp_path):
    """Ruta temporal para pruebas de guardado."""
    return os.path.join(tmp_path, "modelo_test.pkl")


# TESTS DE MODELADO


# Lista de todos los modelos de Regresión disponibles
modelos_regresion = [
    "Regresión Lineal",
    "Regresión Polinómica",
    "SVR",
    "Árbol de Decisión",
    "KNN"
]

@pt.mark.parametrize("nombreModelo", modelos_regresion)
def test_ModelosRegresion(dfRegresion, nombreModelo):
    """
    Prueba que todos los modelos de regresión se entrenen,
    devuelvan métricas R2 numéricas y métricas de Accuracy como string (no compatible).
    """
    dfTrain = dfRegresion.iloc[:15]
    dfTest = dfRegresion.iloc[15:]
    
    colEntrada = ['Entrada']
    colSalida = 'Salida'

    # Ejecutamos la función principal
    (xTrain, yTrain, xTest, yTest, modelo, 
     yTrainPred, yTestPred, 
     r2Train, r2Test, ecmTrain, ecmTest, 
     accTrain, accTest, esGraficable) = crearAjustarModelo(dfTrain, dfTest, colEntrada, colSalida, nombreModelo)

    # 1. El modelo debe existir
    assert modelo is not None, f"El modelo {nombreModelo} devolvió None"

    # 2. Validar métricas de REGRESIÓN
    assert isinstance(r2Train, float), "R2 Train debería ser float en regresión"
    assert isinstance(ecmTrain, float), "ECM Train debería ser float en regresión"
    
    # 3. Validar métricas de CLASIFICACIÓN
    assert isinstance(accTrain, str), "Accuracy debería ser string (No compatible) en regresión"
    
    # 4. Comprobación lógica básica
    
    if nombreModelo == "Regresión Lineal":
        assert r2Test > 0.95

# Lista de modelos de Clasificación
modelos_clasificacion = [
    "Regresión Logística",
    "Regresión Logística Binaria", 
    "Árbol de Decisión (Clasif)",
    "KNN (Clasificación)"
]

@pt.mark.parametrize("nombreModelo", modelos_clasificacion)
def test_ModelosClasificacion(dfClasificacion, nombreModelo):
    """
    Prueba que los modelos de clasificación funcionen, devuelvan Accuracy numérico
    y R2 como string.
    """
    dfTrain = dfClasificacion.iloc[:16] # Asegurar que haya ambas clases en train
    dfTest = dfClasificacion.iloc[16:]
    
    colEntrada = ['Entrada']
    colSalida = 'Salida'

    (xTrain, yTrain, xTest, yTest, modelo, 
     yTrainPred, yTestPred, 
     r2Train, r2Test, ecmTrain, ecmTest, 
     accTrain, accTest, esGraficable) = crearAjustarModelo(dfTrain, dfTest, colEntrada, colSalida, nombreModelo)

    # 1. El modelo debe existir
    assert modelo is not None

    # 2. Validar métricas de CLASIFICACIÓN 
    assert isinstance(accTrain, float), f"Accuracy Train debería ser float en {nombreModelo}"
    assert 0.0 <= accTrain <= 1.0
    
    # 3. Validar métricas de REGRESIÓN 
    assert isinstance(r2Train, str), "R2 debería ser string (No compatible) en clasificación"


# TESTS DE PREDICCIÓN (Lógica específica)


def test_Prediccion_Logistica_Valores(dfClasificacion):
    """
    Verifica específicamente que la regresión logística prediga clases (0 o 1)
    y no probabilidades continuas en la salida directa.
    """
    dfTrain = dfClasificacion
    dfTest = dfClasificacion 
    
    # Entrenamos
    (_, _, _, _, modelo, _, yTestPred, _, _, _, _, _, _, _) = crearAjustarModelo(
        dfTrain, dfTest, ['Entrada'], 'Salida', "Regresión Logística"
    )
    
    # Verificamos que las predicciones sean del tipo correcto (enteros o float discretos, no continuos)
    valores_unicos = np.unique(yTestPred)
    # Debería haber solo 0 y 1 (o subconjunto)
    assert np.all(np.isin(valores_unicos, [0, 1])), f"La logística predijo valores fuera de clases: {valores_unicos}"

# ==========================================
# TESTS DE PERSISTENCIA (Guardar/Cargar)
# ==========================================

def test_GuardarCargarModelo(dfRegresion, rutaModelo):
    """
    Prueba completa del ciclo de vida: Entrenar -> Guardar -> Cargar -> Predecir.
    Actualizado para los nuevos parámetros de GestionDatos.
    """
    # 1. Entrenar un modelo simple
    dfTrain = dfRegresion
    dfTest = dfRegresion
    colEntrada = ['Entrada']
    colSalida = 'Salida'
    
    (xTr, yTr, xTe, yTe, modelo, 
     yPredTr, yPredTe, 
     r2Tr, r2Te, ecmTr, ecmTe, 
     accTr, accTe, esGraf) = crearAjustarModelo(dfTrain, dfTest, colEntrada, colSalida, "Regresión Lineal")

    # 2. Crear diccionario (Asegurando pasar todos los argumentos nuevos)
    
    diccionario_mapeo = None 
    
    dictModelo = crearDiccionarioModelo(
        modelo=modelo,
        columnasEntrada=colEntrada,
        columnaSalida=colSalida,
        r2Train=r2Tr,
        r2Test=r2Te,
        ecmTrain=ecmTr,
        ecmTest=ecmTe,
        descripcion="Test Unitario Automatizado",
        dicColumnaSalida=diccionario_mapeo # <--- Argumento añadido
    )
    
    # 3. Guardar en disco
    error = crearModeloDisco(dictModelo, rutaModelo)
    assert error is None, f"Hubo un error al guardar: {error}"
    assert os.path.exists(rutaModelo)

    # 4. Cargar y verificar integridad
    with open(rutaModelo, 'rb') as f:
        modeloCargado = pk.load(f)
    
    assert modeloCargado['columnasEntrada'] == colEntrada
    assert modeloCargado['formula'] is not None
    
    # 5. Verificar que el objeto modelo dentro del diccionario predice igual
    modeloRecuperado = modeloCargado['modelo']
    # Predecir valor 5 (y = 2*5 + 1 = 11)
    prediccion = modeloRecuperado.predict(pd.DataFrame({'Entrada': [5]}))
    assert prediccion[0] == pt.approx(11.0, abs=0.1)


def test_Escenario_Binario_Hibrido(dfClasificacion):
    """
    Si el usuario convierte una columna categórica
    a binaria (0 y 1), el sistema debe permitir ejecutar TANTO modelos de
    Clasificación (Logística) COMO de Regresión (Lineal), ya que 0 y 1 son números.
    """
    # Usamos dfClasificacion que tiene salidas 0 y 1
    dfTrain = dfClasificacion
    dfTest = dfClasificacion
    colEntrada = ['Entrada']
    colSalida = 'Salida' # Esta columna tiene 0s y 1s

    
    # CASO A: El usuario elige CLASIFICACIÓN (Ej: Regresión Logística)
    
    _, _, _, _, modeloLog, _, _, _, _, _, _, accTrain, _, _ = crearAjustarModelo(
        dfTrain, dfTest, colEntrada, colSalida, "Regresión Logística"
    )
    
    # Verificamos que funcionó como Clasificación
    assert modeloLog is not None
    assert isinstance(accTrain, float), "La Logística debe devolver Accuracy (float) con datos binarios"
    assert accTrain >= 0.0

    
    # CASO B: El usuario elige REGRESIÓN (Ej: Regresión Lineal)
    
    _, _, _, _, modeloLin, _, _, r2Train, _, ecmTrain, _, accTrainLin, _, _ = crearAjustarModelo(
        dfTrain, dfTest, colEntrada, colSalida, "Regresión Lineal"
    )

    # Verificamos que funcionó como Regresión
    assert modeloLin is not None
    assert isinstance(r2Train, float), "La Lineal debe devolver R2 (float) incluso con datos 0 y 1"
    assert isinstance(accTrainLin, str), "La Lineal debe decir 'No compatible' al accuracy"
    
    print("\n¡ÉXITO! El backend soporta tratar datos binarios (0/1) como Clasificación Y como Regresión.")