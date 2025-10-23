import pandas as pd
import pickle as pk
#LEED LOS COMENTARIOS
#En este archivo deberia ir todo lo relacionado con carga actualizacion y consulta a datos(CRUD)

def cargaColumnas(datos):
    """
     Extrae las columnas de un dataframe.
     
    Args:
        datos (Dataframe): La tabla de la cual se desea extraer las colunas
        """
    try:
        return datos.columns.tolist()
    except:
        raise "Ha habido algun error durante la extraccion de columnas"
    
def crearDiccionarioModelo(modelo,columnaEntrada,columnaSalida,r2Train,r2Test, ecmTrain,ecmTest,descripcion):
    modeloGuardado = {
    "modelo": modelo,
    "descripcion": descripcion,
    "columnaEntrada": columnaEntrada,
    "columnaSalida": columnaSalida,
    "metricas": {
        "r2Train": r2Train,
        "r2Test": r2Test,
        "ecmTrain": ecmTrain,
        "ecmTest": ecmTest
    },
    "formula": f"y = {modelo.coef_[0]:.2f} * x + {modelo.intercept_:.2f}",
    }
    return modeloGuardado

import pickle as pk

def crearModeloDisco(dict_modelo, ruta):
    """
    Guarda un modelo de regresión lineal y sus metadatos en disco.
    
    Parámetros:
        dict_modelo: diccionario con el modelo y su información asociada
        ruta: ruta del archivo donde se guardará el modelo (.pkl)
    
    Retorna:
        None si todo ha ido bien.
        str con el mensaje de error si ha ocurrido un fallo durante la serialización o el guardado.
    """
    try:
        with open(ruta, 'wb') as f:
            pk.dump(dict_modelo, f)
        return None  # Éxito
    except (pk.PickleError, TypeError) as e:
        # Errores específicos de serialización
        return f"Error al serializar el modelo: {e}"
    except OSError as e:
        # Errores del sistema (ruta no válida, permisos, espacio, etc.)
        return f"Error al acceder al archivo: {e}"
    except Exception as e:
        # Cualquier otro error no previsto
        return f"Error desconocido al guardar el modelo: {e}"

        
    
    