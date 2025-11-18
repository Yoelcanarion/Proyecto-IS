import pytest as pt
from UI.MainWindowCtrl import *
from PyQt6.QtGui import QStandardItemModel
import pandas as pd
from unittest.mock import MagicMock
from pytestqt import qtbot

@pt.fixture
def dfTest():
    "Se crea un dataframe simple para las pruebas"
    return pd.DataFrame({'col_A': [1,2], 'col_B': [10,20]})

@pt.fixture
def ventanaReal(qtbot,mocker,dfTest):
    """Esta fixture crea una instancia real de MainWindowCtrl
    pero con sus dependencias simuladas (mocker)"""
    
    #Simulamos el modelo que 'mp' debería devolver
    mockModeloRetorno = QStandardItemModel()
    mockModeloRetorno.setObjectName("modelo_simulado")
    
    #Simulamos las columnas que 'gd' debería devolver
    mockColumnasRetorno = dfTest.columns.tolist()
    
    #Reemplazamos las funciones reales por las simulaciones
    mockMp = mocker.patch('MainWindowCtrl.mp',
                           return_value=mockModeloRetorno)
    
    mockGdCarga = mocker.patch(
        'MainWindowCtrl.gd.cargaColumnas',
        return_value=mockColumnasRetorno
    )
    
    #Ahora en vez de cargar nuestras funciones, llamarán a las simulaciones
    ventana = MainWindowCtrl()
    qtbot.addWidget(ventana)
    
    #Entregamos la ventana y las simulaciones a la prueba
    yield ventana, mockMp, mockGdCarga
    

#Realizamos los tests
def testActualizacionCorrecta(ventanaReal,dfTest):
    """Prueba que la interfaz se actualiza correctamente
    después de llamar a cargarTabla
    """
    ventana, _,_ = ventanaReal
    #Ignoramos las simulaciones en esta prueba
    #Estado inicial
    mensajeDefecto = mensajeDefectoCmb
    
    #Comprobamos que los QComboBox están vacíos
    assert ventana.ui.cmbEntrada.count() == 0
    assert ventana.ui.cmbSalida.count() == 0
    
    #Llamamos a la función 
    ventana.cargarTabla(dfTest)
    
    #Verificamos la interfaz:
    
    #Tabla
    assert ventana.ui.tableViewDataFrame.model().objectName() == "modelo_simulado"
    
    #cmbEntrada
    assert ventana.ui.cmbEntrada.count() == 2
    assert ventana.ui.cmbEntrada.itemText(0) == 'col_A'
    
    #cmbSalida
    assert ventana.ui.cmbSalida.count() == 3
    assert ventana.ui.cmbSalida.itemText(0) == mensajeDefecto
    assert ventana.ui.cmbSalida.itemText(1) == 'col_A'
    

def testLlamarDependencias (ventanaReal,dfTest):
    """Prueba unitaria que verifica que cargarTabla llama a sus dependencias
    (mp y gd) como esperamos
    """
    
    #Esta vez capturamos las simulaciones desde la fixture
    ventana,mockMp,mockGdCarga = ventanaReal
    
    #Llamamos a la función
    ventana.cargarTabla(dfTest)
    
    #Verificamos las simulaciones
    
    mockMp.assert_called_once_with(dfTest) #¿Se llamó a 'mp(dfTest) exactamente una vez?
    mockGdCarga.assert_called_once_with(dfTest)

#Pruebas de "creación de modelo"

def testCrearModeloYMetricas(ventanaReal,dfTest):
    """
    Prueba unitaria para 'crearAjustarModelo'.
    Verifica que el modelo y las métricas (r2, ecm) se calculan y guardan.
    """
    
    #Capturamos las simulaciones
    ventana,_,_ = ventanaReal
    
    #Para tests unitarios los simulamos nosotros mismos.
    ventana.dataFrameTrain = dfTest
    ventana.dataFrameTest = dfTest
    ventana.columnasEntradaGraficada = ['col_A']
    ventana.columnaSalidaGraficada = 'col_B'
    
    #Verificamos el estado inicial
    assert ventana.modelo is None
    assert ventana.r2Test is None
    assert ventana.ecmTest is None
    
    #Llamamos a la función
    ventana.crearAjustarModelo() 
    
    #Verificamos 
    assert ventana.modelo is not None
    assert ventana.r2Test is not None
    assert ventana.ecmTest is not None
    
    #Verificamos que las métricas son floats
    assert isinstance(ventana.r2Test, float)
    assert isinstance(ventana.ecmTest, float)
    
    #Comprobamos que el modelo está entrenado
    assert hasattr(ventana.modelo, 'coef_') #Comprueba si existe un atributo con ese nombre dentro del objeto

#Pruebas de "predicciones"

def testPredicciones(ventanaReal, mocker):
    """
    Prueba unitaria para 'pipeLinePrediccion'.
    Simula un modelo, la entrada y comprueba la etiqueta de salida.
    """
    #Capturamos las simulaciones
    ventana,_,_ = ventanaReal
    
    #Creamos un modelo falso
    mockModelo = MagicMock()
    mockModelo.predict.return_value = [99.5] # Una predicción falsa
    
    #Metemos nuestro modelo falso en la ventana
    ventana.modelo = mockModelo
    ventana.columnasEntradaGraficada = ['col_A'] # Simulamos 1 sola entrada
    ventana.columnaSalidaGraficada = 'col_B'
    
    #Simulamos la entrada del usuario en el SpinBox
    ventana.ui.spinBoxEntrada.setValue(10)
    
    #Silenciamos 'plotPrediccion' para que no intente dibujar

    mocker.patch.object(ventana, 'plotPrediccion')
    
    #Llamamos a la función
    ventana.pipelinePrediccion() # Llamamos a la función
    
    #Verificamos que el label de predicción se actualizó
    
    #assert ventana.ui.labelPrediccion.isVisible()    
    assert ventana.ui.labelPrediccion.text() == "Valor de col_B predicho: 99.5000"
    
    #Verificamos que se llamó a 'predict' con los datos del SpinBox
    mockModelo.predict.assert_called_once_with([[10.0]])


#Pruebas de "guardado y carga del modelo"
def testGuardarModelo (ventanaReal,mocker):
    """
    Prueba unitaria para 'guardarModelo'.
    Verifica que se construye el diccionario del modelo y se llama
    a la función 'gd.crearModeloDisco' con los datos correctos.
    """
    ventana, _, _ = ventanaReal
    
    #Falseamos todos los atributos que 'guardarModelo' necesita
    ventana.modelo = "mi_modelo_falso"
    ventana.columnasEntradaGraficada = ['col_A']
    ventana.columnaSalidaGraficada = 'col_B'
    ventana.r2Train = 0.95
    ventana.r2Test = 0.92
    ventana.ecmTrain = 1.5
    ventana.ecmTest = 1.8
    descripcion_test = "Un modelo de prueba"
    
    #Simulamos la función que escribe en disco
    mockCrearDiccionario = mocker.patch('MainWindowCtrl.gd.crearDiccionarioModelo')
    mocker.patch('MainWindowCtrl.gd.crearModeloDisco', return_value=None)
    mocker.patch('MainWindowCtrl.msj.crearInformacion')
    # ACT
    ventana.guardarModelo("ruta/falsa/test.pkl", descripcion_test)
    
    # ASSERT
    # Obtenemos los 'kwargs' (argumentos por palabra clave) enviados a la función
    kwargs_enviados = mockCrearDiccionario.call_args.kwargs
    
    # Ahora verificamos el diccionario 'parametros' original
    assert kwargs_enviados['modelo'] == "mi_modelo_falso"
    assert kwargs_enviados['r2Test'] == 0.92
    assert kwargs_enviados['descripcion'] == "Un modelo de prueba"

def testCargarModelo(ventanaReal,mocker):
    """
    Prueba unitaria para 'cargarModelo'.
    Simula la carga de un archivo .pkl y verifica que tanto los 
    atributos internos (ventana.modelo) como la interfaz se actualizan.
    """
    
    ventana, _, _ = ventanaReal
    
    #Datos falsos que simularemos cargar desde el .pkl
    mockDatosModelo = {
        "modelo": "modelo_cargado_falso",
        "columnasEntrada": ["col_X_cargada"],
        "columnaSalida": "col_Y_cargada",
        "metricas": {
            "r2Train": 0.81, "r2Test": 0.80,
            "ecmTrain": 2.1, "ecmTest": 2.2
        },
        "descripcion": "Descripción cargada",
        "formula": "y = mx+b"
    }
    
    #Simulamos el 'QFileDialog' para que devuelva una ruta falsa
    mocker.patch(
        'MainWindowCtrl.QtWidgets.QFileDialog.getOpenFileName',
        return_value=("ruta/falsa/modelo.pkl", "")
    )
    
    #Simulamos para que devuelva nuestros datos falsos
    mocker.patch('MainWindowCtrl.pk.load', return_value=mockDatosModelo)
    
    #Simulamos 'open' (necesario para el 'with open(...) as f:')
    mocker.patch('builtins.open', mocker.mock_open())
    
    
    ventana.cargarModelo()
    
    
    # Verificamos atributos internos
    assert ventana.modelo == "modelo_cargado_falso"
    assert ventana.r2Test == 0.80
    assert ventana.columnasEntradaGraficada == ["col_X_cargada"]
    
    # Verificamos la Interfaz
    assert ventana.ui.textDescribirModelo.toPlainText() == "Descripción cargada"
    assert "R**2 Test: 0.8000" in ventana.ui.labelR2Test.text()
    assert "ECM Test: 2.2000" in ventana.ui.labelR2Test.text()
    assert ventana.ui.labelFormula.text() == "y = mx+b"