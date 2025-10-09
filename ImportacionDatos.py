import pandas as pd
import sqlite3
import os


#Gestion de tipo de carga

def cargarCsvExcel(ruta):
    """Carga datos desde un archivo CSV o Excel, asumiendo encabezado."""
    extension = os.path.splitext(ruta)[1].lower()
    if extension == '.csv':
        return pd.read_csv(ruta)
    else:
        return pd.read_excel(ruta)

def cargarSqlite(ruta):
    """Carga la única tabla de una base de datos SQLite."""
    with sqlite3.connect(ruta) as con:
        cursor = con.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tablas = cursor.fetchall()
        
        if len(tablas) == 0:
            raise ValueError("La tabla no existe en la base de datos.")
        if len(tablas) > 1:
            raise ValueError("La base de datos debe contener exactamente una tabla.")
            
        nombreTabla = tablas[0][0]
        return pd.read_sql_query(f"SELECT * FROM {nombreTabla}", con)


# Asocia cada extensión con la función de carga correspondiente.
formatos = {
    ".csv": cargarCsvExcel,
    ".xls": cargarCsvExcel,
    ".xlsx": cargarCsvExcel,
    ".sqlite": cargarSqlite,
    ".db": cargarSqlite,
}

#Funciones Principales

def obtenerExtension(ruta):
    """Obtiene la extensión en minúsculas de un archivo a partir de su ruta."""
    _, extension = os.path.splitext(ruta)
    return extension.lower()

def cargarDatos(ruta):
    """
    Selecciona la función de carga adecuada según la extensión del archivo
    y maneja centralmente los errores durante la ejecución.
    """
    extension = obtenerExtension(ruta)
    funcionCarga = formatos.get(extension)
    
    if not funcionCarga:
        raise ValueError("Formato de archivo inválido.")
        
    try:
        return funcionCarga(ruta)
    
    # Gestion Errores
    except FileNotFoundError:
        raise ValueError(f"El archivo no se encuentra en la ruta: {ruta}")
    except (pd.errors.ParserError, sqlite3.DatabaseError, ValueError, Exception) as e:
        if "La tabla no existe" in str(e) or "debe contener exactamente una tabla" in str(e):
             raise e
        raise ValueError(f"Archivo corrupto o formato de archivo inválido.")


def previsualizar(ruta):
    """Carga datos y muestra una previsualización o un mensaje de error."""
    try:
        datos = cargarDatos(ruta)
        print(f"--- Carga exitosa de: {os.path.basename(ruta)} ---")
        print("\n--- Previsualización de los datos ---")
        print(datos.head())
        print("\n--- Tipos de datos inferidos ---")
        datos.info()
    except ValueError as e:
        print(f"Error al cargar el archivo: {e}")

