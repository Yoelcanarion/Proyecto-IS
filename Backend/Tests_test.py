import pytest as pt
import pandas as pd
import numpy as np
import os
import pickle as pk
from ProcesadoDatos import crearAjustarModelo
from GestionDatos import crearDiccionarioModelo, crearModeloDisco


# Fixtures (Datos y configuraciones compartidas)


@pt.fixture
def dfTest():
    """Se crea un dataframe simple para las pruebas (conjunto de test)."""
    # col_A será entrada, col_B será salida
    return pd.DataFrame({'col_A': [1, 2], 'col_B': [10, 20]})

@pt.fixture
def dfTrain():
    """Se crea un dataframe simple para el entrenamiento de las pruebas."""
    # col_A será entrada, col_B será salida. Relación lineal simple y = 10x
    return pd.DataFrame({'col_A': [0.5, 1.5, 2.5], 'col_B': [5, 15, 25]})

@pt.fixture
def columnasEntrada():
    return ['col_A']

@pt.fixture
def columnaSalida():
    return 'col_B'

@pt.fixture
def rutaModelo(tmp_path):
    """Genera una ruta temporal segura para guardar el archivo del modelo."""
    return os.path.join(tmp_path, "modelo_prueba.pkl")

@pt.fixture
def modeloEntrenadoYMetricas(dfTrain, dfTest, columnasEntrada, columnaSalida):
    """
    Fixture auxiliar que devuelve el resultado de crearAjustarModelo
    para no repetir código en los tests.
    """
    return crearAjustarModelo(dfTrain, dfTest, columnasEntrada, columnaSalida)

# Pruebas de "creación de modelo"
def testCrearModeloYMetricas(modeloEntrenadoYMetricas):
    """
    Prueba unitaria para 'crearAjustarModelo'.
    Verifica que el modelo y las métricas (r2, ecm) se calculan correctamente
    tanto para entrenamiento como para test.
    """
    # Desempaquetamos todos los valores retornados
    _, _, _, _, modelo, r2Train, r2Test, ecmTrain, ecmTest = modeloEntrenadoYMetricas

    # Verificaciones básicas de tipos
    assert modelo is not None, "El modelo no debería ser None"
    
    # Verificaciones lógicas de las métricas
    # 1. Entrenamiento
    assert r2Train > 0.9, "El R2 de entrenamiento debería ser alto para datos lineales perfectos"
    assert ecmTrain < 1.0, "El error cuadrático medio de entrenamiento debería ser bajo"
    
    # Al ser datos sintéticos perfectos, el modelo debe generalizar bien
    assert r2Test > 0.9, "El R2 del test debería ser alto, indicando buena generalización"
    assert ecmTest < 5.0, "El error en test debería mantenerse bajo"


# Pruebas de "predicciones"
def testPredicciones(modeloEntrenadoYMetricas, columnasEntrada):
    """
    Prueba unitaria para las predicciones.
    Comprueba que el modelo puede predecir nuevos valores usando la estructura
    correcta de columnas definida en los fixtures.
    """
    # Solo necesitamos el modelo, ignoramos el resto con _
    _, _, _, _, modelo, _, _, _, _ = modeloEntrenadoYMetricas
    
    # Valor de entrada para la prueba (x = 3)
    valorEntrada = 3
    valorEsperado = 30.0 # Porque la relación es y = 10x
    
    
    nombreColumna = columnasEntrada[0] 
    nuevosDatos = pd.DataFrame({nombreColumna: [valorEntrada]})
    
    # Ejecutamos la predicción
    prediccion = modelo.predict(nuevosDatos)
    
    # Verificaciones
    assert len(prediccion) == 1
    # Usamos approx para comparar flotantes
    assert prediccion[0] == pt.approx(valorEsperado, abs=0.1)


# Pruebas de "guardado y carga del modelo"
def testGuardarModelo(modeloEntrenadoYMetricas, columnasEntrada, columnaSalida, rutaModelo):
    """
    Prueba unitaria para 'crearModeloDisco'.
    Verifica que se construye el diccionario del modelo y se guarda correctamente.
    """
    _, _, _, _, modelo, r2Train, r2Test, ecmTrain, ecmTest = modeloEntrenadoYMetricas
    
    # Construimos el diccionario como lo hace la aplicación real
    dictModelo = crearDiccionarioModelo(
        modelo=modelo,
        columnasEntrada=columnasEntrada,
        columnaSalida=columnaSalida,
        r2Train=r2Train,
        r2Test=r2Test,
        ecmTrain=ecmTrain,
        ecmTest=ecmTest,
        descripcion="Modelo de prueba unitaria"
    )
    
    # Probamos el guardado
    resultado = crearModeloDisco(dictModelo, rutaModelo)
    
    # crearModeloDisco devuelve None si todo va bien
    assert resultado is None
    assert os.path.exists(rutaModelo), "El archivo del modelo debería existir en disco"

def testCargarModelo(modeloEntrenadoYMetricas, columnasEntrada, columnaSalida, rutaModelo):
    """
    Prueba unitaria para la carga del modelo.
    Verifica que lo que se guarda se puede recuperar y es funcional.
    """
    # 1. Guardamos primero (Setup)
    _, _, _, _, modelo, r2Train, r2Test, ecmTrain, ecmTest = modeloEntrenadoYMetricas
    dictModeloOriginal = crearDiccionarioModelo(
        modelo, columnasEntrada, columnaSalida, r2Train, r2Test, ecmTrain, ecmTest, "Desc"
    )
    crearModeloDisco(dictModeloOriginal, rutaModelo)
    
    # 2. Cargamos el modelo
    with open(rutaModelo, 'rb') as f:
        modeloCargadoDict = pk.load(f)
        
    # 3. Verificaciones
    assert isinstance(modeloCargadoDict, dict)
    assert "modelo" in modeloCargadoDict
    assert modeloCargadoDict["columnasEntrada"] == columnasEntrada
    
    # Verificamos que el objeto modelo dentro del diccionario funciona
    modeloRecuperado = modeloCargadoDict["modelo"]
    prediccion = modeloRecuperado.predict(pd.DataFrame({'col_A': [3]}))
    assert prediccion[0] == pt.approx(30.0, abs=0.1)