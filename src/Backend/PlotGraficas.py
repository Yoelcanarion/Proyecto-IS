from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QVBoxLayout, QWidget
import plotly.graph_objects as go
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix
from sklearn.base import is_classifier
from UI.UtilidadesInterfaz import Mensajes as msj


def _mostrarPlotlyEnQt(fig, placeholder):
    """Helper para incrustar gráficas Plotly en el layout de Qt"""
    limpiarLayout(placeholder)
    vistaWeb = QWebEngineView()
    html = fig.to_html(include_plotlyjs='cdn') 
    vistaWeb.setHtml(html)
    layout = QVBoxLayout(placeholder)
    layout.addWidget(vistaWeb)
    placeholder.setLayout(layout)



def plotGrafica(xTrain, yTrain, xTest, yTest, columnasEntradaGraficada, columnaSalidaGraficada, dicColumnaSalida, modelo, placeholderGrafica, puntoPrediccion=None):
    """
    Orquestador principal para la generación de gráficas 2D/3D.
    """
    nCols = len(columnasEntradaGraficada)
    if nCols == 0 or nCols > 2:
        return 
    
    if modelo is None:
            return

    fig = go.Figure()

    if nCols == 1:
        _configurarGrafica2D(modelo, xTrain, yTrain, xTest, yTest, columnasEntradaGraficada, columnaSalidaGraficada, dicColumnaSalida, fig, puntoPrediccion)
    elif nCols == 2:
        _configurarGrafica3D(modelo,xTrain, yTrain, xTest, yTest, columnasEntradaGraficada, columnaSalidaGraficada, dicColumnaSalida, fig, puntoPrediccion)

    _mostrarPlotlyEnQt(fig, placeholderGrafica)



def _configurarGrafica2D(modelo, xTrain, yTrain, xTest, yTest, columnasEntradaGraficada, columnaSalidaGraficada, dicColumnaSalida, fig, puntoPrediccion):
    """Configura gráfica 2D y aplica mapeo de texto en eje Y si existe."""
    nombreX = columnasEntradaGraficada[0]
    xMin, xMax = _dibujarDatosReales2D(xTrain, yTrain, xTest, yTest, fig, nombreX)
    
    if puntoPrediccion and xMin == 0 and xMax == 10:
        valX = puntoPrediccion[0][0]; xMin, xMax = valX - 5, valX + 5

    _dibujarLineaModelo(modelo, fig, nombreX, xMin, xMax)
    
    if puntoPrediccion:
        _dibujarPuntoDestacado(fig, x=[puntoPrediccion[0][0]], y=[puntoPrediccion[1]], nombre="Predicción")
    
    # === LÓGICA DE DICCIONARIO PARA EJE Y ===
    layoutArgs = dict(title="Modelo 2D", xaxis_title=nombreX, yaxis_title=columnaSalidaGraficada)
    
    if dicColumnaSalida:
        # Obtenemos los valores ordenados (0, 1)
        ticksVals = sorted(dicColumnaSalida.values())
        # Obtenemos las claves (texto) que corresponden a esos valores
        ticksText = [k for v in ticksVals for k, val in dicColumnaSalida.items() if val == v]
        
        # Forzamos que el eje Y muestre el texto en esos valores exactos    
        layoutArgs['yaxis'] = dict(tickmode='array', tickvals=ticksVals, ticktext=ticksText)
        
    fig.update_layout(**layoutArgs)



def _configurarGrafica3D(modelo, xTrain, yTrain, xTest, yTest, columnasEntradaGraficada, columnaSalidaGraficada, dicColumnaSalida, fig, puntoPrediccion):
    """Configura gráfica 3D y aplica mapeo de texto en eje Z si existe."""
    nombreX, nombreY = columnasEntradaGraficada
    limites = _dibujarDatosReales3D(xTrain, yTrain, xTest, yTest, fig, nombreX, nombreY)
    
    if puntoPrediccion and limites == (0, 10, 0, 10):
        vx, vy = puntoPrediccion[0]; limites = (vx-5, vx+5, vy-5, vy+5)

    _dibujarSuperficieModelo(modelo, fig, nombreX, nombreY, limites)
    
    if puntoPrediccion:
        _dibujarPuntoDestacado3D(fig, x=[puntoPrediccion[0][0]], y=[puntoPrediccion[0][1]], z=[puntoPrediccion[1]], nombre="Predicción")
    
    # === LÓGICA DE DICCIONARIO PARA EJE Z ===
    sceneDict = dict(xaxis_title=nombreX, yaxis_title=nombreY, zaxis_title=columnaSalidaGraficada)
    
    if dicColumnaSalida:
        ticksVals = sorted(dicColumnaSalida.values())
        ticksText = [k for v in ticksVals for k, val in dicColumnaSalida.items() if val == v]
        sceneDict['zaxis'] = dict(tickmode='array', tickvals=ticksVals, ticktext=ticksText)

    fig.update_layout(title="Modelo 3D", scene=sceneDict)


def _configurarGraficaCorrelacion(modelo, xTest, yTest, columnaSalidaGraficada, fig):
    """Genera la gráfica clásica de Real vs Predicho para regresión."""
    yPred = modelo.predict(xTest)
    
    # Puntos
    fig.add_trace(go.Scatter(
        x=yTest, y=yPred, 
        mode='markers', name='Datos Test',
        marker=dict(
            color=yTest, # Opcional: mantener escala visual
            colorscale='Viridis',
            showscale=True,
            opacity=0.7,
            line=dict(width=0.5, color='DarkSlateGrey')
        )
    ))

    # Línea Ideal
    minVal = min(yTest.min(), yPred.min())
    maxVal = max(yTest.max(), yPred.max())
    
    fig.add_trace(go.Scatter(
        x=[minVal, maxVal], y=[minVal, maxVal],
        mode='lines', name='Ideal (Perfecto)',
        line=dict(color='black', dash='dash', width=2)
    ))

    fig.update_layout(
        title="Correlación: Real vs Predicho",
        xaxis_title=f"Valor Real ({columnaSalidaGraficada})",
        yaxis_title="Valor Predicho",
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
    )

# --- MÉTODOS HELPER 2D (Privados) ---

def _dibujarDatosReales2D(xTrain, yTrain, xTest, yTest, fig, colX):
    """Dibuja scatter de entrenamiento y test si existen. Retorna (min, max) de X."""
    xMin, xMax = 0, 10 # Valores por defecto

    # Verificamos si existen los datos en memoria (no es un modelo cargado)
    if xTrain is not None and yTrain is not None:
        xTr = _extraerColumna(xTrain, colX)
        xTe = _extraerColumna(xTest, colX)

        fig.add_trace(go.Scatter(x=xTr, y=yTrain, mode='markers', name='Entrenamiento', marker=dict(color='blue', opacity=0.5)))
        fig.add_trace(go.Scatter(x=xTe, y=yTest, mode='markers', name='Test', marker=dict(color='orange', opacity=0.5)))
        
        if len(xTr) > 0:
            xMin, xMax = min(xTr.min(), xTe.min()), max(xTr.max(), xTe.max())
    
    return xMin, xMax



def _dibujarLineaModelo(modelo, fig, colX, xMin, xMax):
    """Genera la línea de regresión evaluando el modelo."""
    # Calcular margen visual
    padding = (xMax - xMin) * 0.1 if xMax != xMin else 1
    xRange = np.linspace(xMin - padding, xMax + padding, 100)
    
    # Crear DataFrame explícito para respetar nombres de columnas del modelo
    dfRange = pd.DataFrame({colX: xRange})
    
    try:
        yRange = modelo.predict(dfRange)
        fig.add_trace(go.Scatter(x=xRange, y=yRange, mode='lines', name='Modelo', line=dict(color='red', width=3)))
    except Exception:
        # Silenciosamente ignoramos si falla la predicción de rango (ej: tipo de dato incompatible)
        pass


# --- MÉTODOS HELPER 3D (Privados) ---

def _dibujarDatosReales3D(xTrain, yTrain, xTest, yTest, fig, colX, colY):
    """Dibuja scatter 3D de entrenamiento y test si existen. Retorna límites."""
    bounds = (0, 10, 0, 10)

    if xTrain is not None and yTrain is not None:
        xTr = _extraerColumna(xTrain, colX)
        yTr = _extraerColumna(xTrain, colY)
        zTr = yTrain

        xTe = _extraerColumna(xTest, colX)
        yTe = _extraerColumna(xTest, colY)
        zTe = yTest

        fig.add_trace(go.Scatter3d(x=xTr, y=yTr, z=zTr, mode='markers', name='Train', marker=dict(size=4, color='blue', opacity=0.5)))
        fig.add_trace(go.Scatter3d(x=xTe, y=yTe, z=zTe, mode='markers', name='Test', marker=dict(size=4, color='orange', opacity=0.5)))
        
        if len(xTr) > 0:
            bounds = (xTr.min(), xTr.max(), yTr.min(), yTr.max())
    
    return bounds



def _dibujarSuperficieModelo(modelo, fig, colX, colY, limites):
    """Genera la malla 3D del modelo."""
    xMin, xMax, yMin, yMax = limites
    
    # Crear malla
    xLin = np.linspace(xMin, xMax, 20)
    yLin = np.linspace(yMin, yMax, 20)
    xMesh, yMesh = np.meshgrid(xLin, yLin)
    
    # Aplanar para predecir
    xyFlat = np.c_[xMesh.ravel(), yMesh.ravel()]
    dfMesh = pd.DataFrame(xyFlat, columns=[colX, colY])
    
    try:
        zFlat = modelo.predict(dfMesh)
        
        # Solo graficamos superficie si la salida es numérica (para evitar error en clasificación de texto)
        if  not is_classifier(modelo):
            zMesh = zFlat.reshape(xMesh.shape)
            fig.add_trace(go.Surface(z=zMesh, x=xLin, y=yLin, colorscale='Reds', opacity=0.5, name='Modelo', showscale=False))
    except Exception:
        pass


# --- UTILIDADES ---

def _extraerColumna(data, nombre_col):
    """Extrae una columna de DataFrame o Series de forma segura."""
    if hasattr(data, 'columns'):
        return data[nombre_col]
    # Si es un array de numpy o una serie sin nombre
    return data.iloc[:, 0] if hasattr(data, 'iloc') and data.ndim > 1 else data



def _dibujarPuntoDestacado(fig, x, y, nombre):
    """Dibuja un punto 2D destacado (estrella verde)."""
    fig.add_trace(go.Scatter(
        x=x, y=y, mode='markers', name=nombre,
        marker=dict(color='green', size=15, symbol='star', line=dict(color='black', width=2))
    ))



def _dibujarPuntoDestacado3D(fig, x, y, z, nombre):
    """Dibuja un punto 3D destacado (diamante verde)."""
    fig.add_trace(go.Scatter3d(
        x=x, y=y, z=z, mode='markers', name=nombre,
        marker=dict(color='green', size=12, symbol='diamond', line=dict(color='black', width=2))
    ))



def plotCorrelacion(parent, modelo, xTest, yTest, columnaSalidaGraficada, dicColumnaSalida, placeholderCorrelacion):
    """
    Decide qué gráfica mostrar según el tipo de datos:
    - Datos Numéricos -> Gráfica de Correlación (Real vs Predicho).
    - Datos Categóricos -> Matriz de Confusión.
    """
    # Validación de seguridad
    if yTest is None or xTest is None:
        msj.crearAdvertencia(parent, "Aviso", "Faltan datos de test para generar estadísticas.")
        limpiarLayout(placeholderCorrelacion)
        return

    fig = go.Figure()

    try:
        # Determinamos si es Clasificación (Texto/Categoría) o Regresión (Números)
        esClasificador =  is_classifier(modelo)
        if not esClasificador:
            _configurarGraficaCorrelacion(modelo, xTest, yTest, columnaSalidaGraficada, fig)
        else:
            _configurarMatrizConfusion(modelo, dicColumnaSalida, xTest, yTest, fig)

        _mostrarPlotlyEnQt(fig, placeholderCorrelacion)
        
    except Exception as e:
        msj.crearAdvertencia(parent, "Error", f"Error al graficar estadísticas: {e}")



def _configurarMatrizConfusion(modelo, dicColumnaSalida, xTest, yTest, fig):
    """Genera Matriz de Confusión usando nombres reales si existen en el diccionario."""
    yPred = modelo.predict(xTest)
    
    # Obtenemos las etiquetas numéricas presentes (0, 1)
    lblsNum = sorted(list(set(yTest) | set(yPred)))
    
    # === LÓGICA DE DICCIONARIO PARA ETIQUETAS ===
    if dicColumnaSalida:
        # Traducimos los números (0,1) al texto original (ej: 'Femenino', 'Masculino')
        lblsText = [next((k for k, v in dicColumnaSalida.items() if v == val), str(val)) for val in lblsNum]
    else:
        lblsText = [str(l) for l in lblsNum]

    cm = confusion_matrix(yTest, yPred, labels=lblsNum)
    
    # Usamos 'lblsText' para los ejes X e Y del Heatmap
    fig.add_trace(go.Heatmap(
        z=cm, 
        x=lblsText, 
        y=lblsText, 
        colorscale='Blues', 
        showscale=True, 
        text=cm, 
        texttemplate="%{z}"
    ))
    
    fig.update_layout(title="Matriz de Confusión", xaxis_title="Predicho", yaxis_title="Real")



def limpiarGrafica(placeholderGrafica, placeholderCorrelacion):
    """Limpia los widgets de gráficas"""
    limpiarLayout(placeholderGrafica)
    limpiarLayout(placeholderCorrelacion)



def limpiarLayout(widgetPlaceholder):
    """Función auxiliar segura para borrar layouts con WebEngines"""
    if widgetPlaceholder.layout() is not None:
        oldLayout = widgetPlaceholder.layout()
        while oldLayout.count():
            item = oldLayout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        QWidget().setLayout(oldLayout)