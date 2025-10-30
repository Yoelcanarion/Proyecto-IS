import pandas as pd
import pickle as pk
#LEED LOS COMENTARIOS
#En este archivo deberia ir todo lo relacionado con carga actualizacion y consulta a datos(CRUD)

def cargaColumnasTotal(datos):
    """
     Extrae las columnas de un dataframe.

    Args:
        datos (Dataframe): La tabla de la cual se desea extraer las colunas
        """
    try:
        return datos.columns.tolist()
    except Exception as e:
        raise Exception(f"Ha habido algún error durante la extracción de columnas: {e}")


def cargaColumnasNumericas(datos):
    """
    Extrae columnas numéricas. Si hay columnas con números en formato string,
    intenta convertirlas a número antes de descartarlas.

    Modifica el DataFrame convirtiendo estas columnas a tipo numérico.
    """
    columnas_validas = []

    for col in datos.columns:
        serie = datos[col]

        if pd.api.types.is_numeric_dtype(serie):
            columnas_validas.append(col)
        else:
            # Intentar convertir la columna completa
            try:
                datos[col] = pd.to_numeric(serie, errors='raise')
                columnas_validas.append(col)
            except Exception:
                # No se puede convertir, no es numérica
                pass

    return columnas_validas


def cargaColumnas(datos, solo_numericas=True):
    if solo_numericas:
        return cargaColumnasNumericas(datos)
    else:
        return cargaColumnasTotal(datos)


def crearDiccionarioModelo(modelo,columnasEntrada,columnaSalida,r2Train,r2Test, ecmTrain,ecmTest,descripcion):
    # CAMBIO IMPORTANTE: La fórmula se genera dinámicamente para soportar una o más variables de entrada.
    # Itera sobre los coeficientes y los nombres de las columnas de entrada para construir la ecuación.
    formula_parts = []
    if hasattr(modelo, 'coef_') and hasattr(modelo, 'intercept_'):
        for i, col in enumerate(columnasEntrada):
            formula_parts.append(f"{modelo.coef_[i]:.4f} * {col}")
        formula = f"y = {modelo.intercept_:.4f} + {' + '.join(formula_parts)}"
    else:
        formula = "Fórmula no disponible"


    modeloGuardado = {
    "modelo": modelo,
    "descripcion": descripcion,
    "columnaEntrada": columnasEntrada,
    "columnaSalida": columnaSalida,
    "metricas": {
        "r2Train": r2Train,
        "r2Test": r2Test,
        "ecmTrain": ecmTrain,
        "ecmTest": ecmTest
    },
    "formula": formula, # CAMBIO IMPORTANTE: Se utiliza la fórmula generada dinámicamente.
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