import pandas as pd
import numpy as np
def aplicarPreprocesadoCalcular(columnasEntrada, columnaSalida, df, opcion, constante):
        """
        Aplica la operación de preprocesamiento seleccionada.
        OPTIMIZADO: Usa el modelo optimizado para mostrar los resultados.
        """

        if isinstance(columnasEntrada, str):
            columnasEntrada = [columnasEntrada]

        columnasSeleccionadas = columnasEntrada + [columnaSalida]

        dfProcesado = df.copy(deep=True)
        tamDf = len(df)
        try:
            match opcion:
                case "Eliminar filas con NaN":
                    nanAntes = dfProcesado[columnasSeleccionadas].isna().sum().sum()
                    # Eliminar filas que tengan NaN en las columnas seleccionadas
                    dfProcesado.dropna(subset=columnasSeleccionadas,
                                        inplace=True, ignore_index=True)
                    
                    mensaje = f"Filas eliminadas: {tamDf - len(dfProcesado)}\nNaN eliminados: {nanAntes}"

                case "Rellenar con la media (Numpy)":
                    dfProcesado = rellenarNanColumnasNumericas(dfProcesado, columnasEntrada, columnaSalida, metodo='media')
                    mensaje = "NaN rellenados con la media en columnas seleccionadas"

                case "Rellenar con la mediana":
                    dfProcesado = rellenarNanColumnasNumericas(dfProcesado, columnasEntrada, columnaSalida, metodo='mediana')
                    mensaje = "NaN rellenados con la mediana en columnas seleccionadas"
        

                case "Rellenar con un valor constante":
                        dfProcesado = rellenarNanColumnasNumericas(
                            dfProcesado,
                            columnasEntrada, 
                            columnaSalida,
                            metodo='constante',
                            valorConstante=float(constante))
                        mensaje = f"NaN rellenados con {constante} en columnas seleccionadas"
                            

        except Exception as e:
            raise Exception

        return dfProcesado[columnasSeleccionadas],  mensaje, columnasSeleccionadas



def rellenarNanColumnasNumericas(df, columnasEntrada, columnaSalida, metodo,  valorConstante=None):
        """
        Rellena valores NaN en las columnas de entrada y salida seleccionadas.

        Args:
            df: DataFrame a procesar
            metodo: 'media', 'mediana' o 'constante'
            valorConstante: valor a usar si metodo='constante'

        Returns:
            DataFrame con valores NaN rellenados en las columnas seleccionadas
        """
        if isinstance(columnasEntrada, str):
            columnasEntrada = [columnasEntrada]
  

        # Combinar columnas de entrada y salida
        columnasAProcesar = columnasEntrada + [columnaSalida]

        for col in columnasAProcesar:
            # Verificar que la columna existe y es numérica
            if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
                if df[col].isna().any():
                    if metodo == 'media':
                        valor = np.nanmean(df[col])
                        df[col] = df[col].fillna(valor)
                    elif metodo == 'mediana':
                        valor = np.nanmedian(df[col].to_numpy())
                        df[col] = df[col].fillna(valor)
                    elif metodo == 'constante' and valorConstante is not None:
                        df[col] = df[col].fillna(valorConstante)

        return df

