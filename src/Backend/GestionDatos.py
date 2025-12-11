import pandas as pd
import pickle as pk
import numpy as np
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


def crearDiccionarioModelo(modelo, columnasEntrada, columnaSalida, r2Train, r2Test, ecmTrain, ecmTest, descripcion, dicColumnaSalida):
    """
    Crea un diccionario con los datos del modelo para guardarlo.
    CORRECCIÓN: Aplana los coeficientes con numpy para soportar Regresión Logística (que devuelve matrices) 
    y Regresión Lineal (que devuelve vectores) sin errores de formato.
    """
    formula = "Fórmula no disponible"

    # Verificamos si el modelo tiene coeficientes paramétricos
    if hasattr(modelo, 'coef_') and hasattr(modelo, 'intercept_'):
        try:
            # 1. APLANAR COEFICIENTES
            coefs = np.array(modelo.coef_).flatten()
            intercepts = np.array(modelo.intercept_).flatten()
            val_intercept = intercepts[0] if len(intercepts) > 0 else 0

            # 2. Construir la ecuación iterando sobre el array plano
            formula_parts = []
            for i, col in enumerate(columnasEntrada):
                # Protección: asegurarnos de no salirnos del índice si hay discrepancia
                if i < len(coefs):
                    val_coef = coefs[i]
                    formula_parts.append(f"{val_coef:.4f} * {col}")
            
            # 3. Distinguir tipo de fórmula para ser más precisos
            nombre_modelo = str(type(modelo).__name__)
            if "Logistic" in nombre_modelo:
                # En logística, la ecuación lineal calcula el logit, no la salida directa
                formula = f"logit(p) = {val_intercept:.4f} + {' + '.join(formula_parts)}"
            else:
                formula = f"y = {val_intercept:.4f} + {' + '.join(formula_parts)}"

        except Exception as e:
            # Si falla algo raro (ej: modelo complejo no estándar), ponemos fallback
            print(f"No se pudo generar la fórmula texto: {e}")
            formula = "Fórmula compleja / No paramétrica"
    
    else:
        # Para KNN, Árboles, SVR (rbf), etc.
        formula = "Modelo no paramétrico (Caja negra)"

    # Construcción del diccionario
    dict_modelo = {
        "modelo": modelo,
        "columnasEntrada": columnasEntrada,
        "columnaSalida": columnaSalida,
        "metricas": {
            "r2Train": r2Train,
            "r2Test": r2Test,
            "ecmTrain": ecmTrain,
            "ecmTest": ecmTest
        },
        "formula": formula,
        "descripcion": descripcion,
        "dicColumnaSalida":dicColumnaSalida
    }
    
    return dict_modelo

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
    
    
    
def transformarColumnaBinaria(df, nombreColumna, diccionarioMapeo):
    """
    Transforma los valores de una columna específica a numéricos (0 y 1) 
    usando un diccionario.
    
    IMPORTANTE: Modifica el DataFrame original (in-place) y NO devuelve nada.
    """
    try:
        if nombreColumna not in df.columns:
            raise ValueError(f"La columna '{nombreColumna}' no existe en el DataFrame.")
        df[nombreColumna] = df[nombreColumna].map(diccionarioMapeo)
        df[nombreColumna] = pd.to_numeric(df[nombreColumna], errors='coerce')


    except Exception as e:
        raise Exception(f"Error al transformar la columna '{nombreColumna}': {str(e)}")


def transformarColumnaBinariaAuto(df, nombreColumna):
    """
    Detecta automáticamente los 2 valores únicos, genera el diccionario y 
    llama a transformarColumnaBinaria para modificar el DF.

    Returns:
        dict: El diccionario de mapeo generado (ej: {'F': 0, 'M': 1}).
    """
    try:
        if nombreColumna not in df.columns:
            raise ValueError(f"Columna '{nombreColumna}' no encontrada.")

        valoresUnicos = df[nombreColumna].dropna().unique()

        if len(valoresUnicos) != 2:
            raise ValueError(f"La columna '{nombreColumna}' no es binaria. Tiene {len(valoresUnicos)} valores únicos: {valoresUnicos}.")

        try:
            valoresUnicos = sorted(valoresUnicos)
        except:
            pass 

        diccionarioMapeo = {valoresUnicos[0]: 0, valoresUnicos[1]: 1}
        transformarColumnaBinaria(df, nombreColumna, diccionarioMapeo)

        return diccionarioMapeo

    except Exception as e:
        raise Exception(f"Error en transformación automática: {str(e)}")
    
    
def generarTextoFormula(modelo, columnasEntrada):
    """
    Genera el string de la fórmula matemática del modelo.
    Usa notación científica si los coeficientes son muy pequeños (evita 0.0000).
    """
    if not (hasattr(modelo, 'coef_') and hasattr(modelo, 'intercept_')):
        return "Fórmula: Modelo no paramétrico (Caja negra)"

    try:
        # Aplanar arrays para evitar problemas de dimensiones
        coefs = np.array(modelo.coef_).flatten()
        inter = np.array(modelo.intercept_).flatten()[0]
        
        # Función de formateo inteligente: 
        # Si el valor es muy pequeño (< 0.001) pero no 0, usa científica. Si no, normal.
        def fmt(v):
            if abs(v) < 0.0001 and v != 0:
                return f"{v:.4e}" # Ej: 1.2345e-05
            else:
                return f"{v:.4f}"  # Ej: 0.5234

        # Construir las partes: "m1*x1", "m2*x2"...
        parts = []
        for i, col in enumerate(columnasEntrada):
            if i < len(coefs):
                val = coefs[i]
                strVal = fmt(val)
                parts.append(f"{strVal}*{col}")
        
        nombreModelo = str(type(modelo).__name__)
        prefix = "logit(p)" if "Logistic" in nombreModelo else "y"
        
        # Unir todo
        formula = f"{prefix} = {fmt(inter)}"
        for p in parts:
            # Si el término ya empieza por "-", lo añadimos directo, si no, ponemos "+"
            if p.strip().startswith("-"):
                formula += f" {p}" 
            else:
                formula += f" + {p}"
                
        return formula

    except Exception as e:
        return f"Fórmula no disponible: {str(e)}"
