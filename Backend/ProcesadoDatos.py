from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error

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

#Entradas: pd.DataFrame, pd.DataFrame, List[str], str -> Salidas: Tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series, LinearRegression, float, float, float, float]
def crearAjustarModelo(dataFrameTrain, dataFrameTest, columnasEntradaGraficada, columnaSalidaGraficada):
    """Método usado para crear, ajustar, testear y obtener estadísticas como R**2 y ECM a partir de los datos procesados anteriormente"""
    
    try:
        if dataFrameTrain is None or dataFrameTest is None:
            raise TypeError("No hay datos de entrenamiento o test disponibles")

        if columnasEntradaGraficada is None or columnaSalidaGraficada is None:
            raise TypeError("Para continuar al datasplit no puede tener nulos en las columnas de entrada o salida")
    
        xTrain = dataFrameTrain[columnasEntradaGraficada]        
        yTrain = dataFrameTrain[columnaSalidaGraficada]
        xTest = dataFrameTest[columnasEntradaGraficada]
        yTest = dataFrameTest[columnaSalidaGraficada]

        modelo = LinearRegression().fit(xTrain, yTrain)

        yTrainPred = modelo.predict(xTrain)  #Tiene la forma [pred1, pred2, ...], siendo pred la predicción de cada muestra de xTrain (con muestras me refiero a las listas internas)
        yTestPred = modelo.predict(xTest)

        r2Train = r2_score(yTrain, yTrainPred)
        r2Test = r2_score(yTest, yTestPred)

        ecmTrain = mean_squared_error(yTrain, yTrainPred)
        ecmTest = mean_squared_error(yTest, yTestPred)


    except Exception as e:
        raise Exception
    
    return xTrain, yTrain, xTest, yTest, modelo, r2Train, r2Test, ecmTrain, ecmTest
