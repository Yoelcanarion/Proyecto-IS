import pandas as pd
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