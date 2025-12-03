
Proyecto IS

<div align="center">

![Python Version](https://img.shields.io/badge/python-3.9%2B-blue?style=for-the-badge&logo=python)
![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green?style=for-the-badge&logo=qt)
![Scikit-Learn](https://img.shields.io/badge/ML-Scikit--Learn-orange?style=for-the-badge&logo=scikit-learn)
![Status](https://img.shields.io/badge/Status-Release%20Candidate-success?style=for-the-badge)

**Una suite de escritorio completa para análisis de datos, preprocesamiento y Machine Learning sin código.**

[Reportar Bug](https://github.com/tu-usuario/proyecto-is/issues) · [Solicitar Feature](https://github.com/tu-usuario/proyecto-is/issues)

</div>

---

##  Descripción
**ML Desktop Assistant** es una herramienta diseñada para cerrar la brecha entre los datos crudos y las predicciones analíticas. Permite a los usuarios importar datasets, limpiar datos, entrenar modelos de regresión y clasificación, y visualizar resultados complejos a través de una interfaz gráfica intuitiva, eliminando la barrera de entrada de la programación.

Esta documentación corresponde a la **Versión Final (Release)** y cubre desde la instalación hasta detalles arquitectónicos para desarrolladores.

---

##  Características Principales

###  1. Gestión de Datos (ETL)
* **Importación Multi-formato:** Carga nativa de archivos `.csv`, `.xlsx`, `.xls` y bases de datos `.sqlite` / `.db`.
* **Preprocesamiento Visual:**
    * Detección y eliminación de filas con valores nulos (NaN).
    * Imputación automática mediante **Media**, **Mediana** o valores **Constantes**.
* **Selección de Features:** Interfaz para definir múltiples columnas de entrada y la variable objetivo.

###  2. Motor de Machine Learning
El sistema adapta automáticamente los algoritmos disponibles según el tipo de dato de salida:

| Tipo de Problema | Algoritmos Disponibles |
| :--- | :--- |
| **Regresión** | • Regresión Lineal & Polinómica<br>• SVR (Support Vector Regression)<br>• Árboles de Decisión<br>• KNN Regressor |
| **Clasificación** | • Regresión Logística (Estándar & Binaria)<br>• Árboles de Clasificación<br>• KNN Classifier |

> **Nota:** El sistema incluye detección automática de variables binarias (ej: "Sí/No") para permitir su uso en modelos numéricos.

###  3. Visualización y Métricas
* **Gráficos Interactivos:** Renderizado de gráficos de dispersión 2D y superficies 3D con **Plotly**.
* **Evaluación de Modelos:** Cálculo automático de métricas clave:
    * $R^2$ y ECM (Error Cuadrático Medio) para regresión.
    * Accuracy y Matrices de Confusión para clasificación.
* **Fórmulas Matemáticas:** Generación de la ecuación textual del modelo resultante.

###  4. Persistencia
* **Guardar/Cargar:** Exportación de modelos a archivos `.pkl` incluyendo metadatos y descripciones personalizadas.
* **Predicción Manual:** Interfaz dedicada para ingresar nuevos datos y obtener predicciones en tiempo real sobre modelos cargados.

---

##  Instalación y Puesta en Marcha

Para asegurar un funcionamiento correcto y evitar conflictos con otras librerías de tu sistema, recomendamos seguir estos pasos detallados.

### Prerrequisitos
* **Python 3.9** o superior instalado.
* Git instalado para clonar el repositorio.

### 1. Clonar el repositorio
Descarga el código fuente a tu máquina local:

```bash
git clone [https://github.com/tu-usuario/proyecto-is.git](https://github.com/tu-usuario/proyecto-is.git)
cd Proyecto-IS
````

### 2\. Crear un Entorno Virtual (Recomendado)

Es una buena práctica aislar las dependencias del proyecto.

  * **En Windows:**

    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    ```

  * **En macOS/Linux:**

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

### 3\. Instalar dependencias

Instala las librerías necesarias. Hemos incluido `PyQt6-WebEngine` necesaria para la visualización de gráficos avanzados y `openpyxl` para leer archivos Excel.

```bash
pip install --upgrade pip
pip install pandas numpy scikit-learn PyQt6 PyQt6-WebEngine plotly matplotlib scipy pytest openpyxl
```

> **Nota para usuarios de Linux:** Si encuentras errores al instalar PyQt6, asegúrate de tener instaladas las librerías base de Qt en tu sistema (ej: `libxcb-cursor0` en Ubuntu).

### 4\. Ejecutar la aplicación

Una vez instaladas las dependencias, lanza la interfaz gráfica desde el directorio raíz del proyecto:

```bash
python src/main.py
```

-----

## 📖 Guía de Uso Rápida

### Paso 1: Preprocesamiento

1.  Ve a la pestaña **Preprocesado**.
2.  Carga tu archivo de datos (`.csv`, `.xlsx`, etc.).
3.  Selecciona las **Columnas de Entrada** (Features) y la **Columna de Salida** (Target).
4.  Aplica limpieza de datos si es necesario (ej: "Rellenar con la media").

### Paso 2: Entrenamiento

1.  Ajusta el **Slider** para definir el porcentaje de datos de Test vs. Train.
2.  Selecciona un modelo del menú desplegable (ej: "Regresión Lineal").
3.  Haz clic en **"Aplicar División"** (esto entrena el modelo automáticamente).

### Paso 3: Visualización y Predicción

1.  Automáticamente serás redirigido a la pestaña **Visualización**.
2.  Analiza la gráfica interactiva y las métricas ($R^2$, ECM).
3.  Usa el panel derecho para introducir valores manuales y predecir resultados nuevos.
4.  Usa el botón **"Guardar Modelo"** para exportar tu trabajo.

-----

##  Solución de Problemas (Troubleshooting)

| Error Común | Causa Probable | Solución |
| :--- | :--- | :--- |
| `ModuleNotFoundError: No module named 'PyQt6'` | Dependencias no instaladas | Ejecuta `pip install PyQt6` dentro de tu entorno virtual. |
| La gráfica no aparece en la UI | Falta el componente WebEngine | Ejecuta `pip install PyQt6-WebEngine`. |
| Error al leer `.xlsx` | Falta el motor de Excel | Ejecuta `pip install openpyxl`. |

-----

##  Notas Técnicas (Arquitectura)

Esta sección está destinada a futuros desarrolladores que deseen mantener o extender el proyecto.

### Estructura del Proyecto

El software sigue una arquitectura **MVC (Modelo-Vista-Controlador)** adaptada:

  * `src/UI/`: Contiene la lógica visual (`MainWindowUI.py`) y el controlador de eventos (`MainWindowCtrl.py`).
  * `src/Backend/`:
      * `ProcesadoDatos.py`: Lógica de negocio para entrenamiento y validación de modelos Scikit-Learn.
      * `GestionDatos.py`: Persistencia (Pickle), CRUD y generación de fórmulas.
      * `PreprocesamientoDatos.py`: Algoritmos de limpieza e imputación.
      * `ImportacionDatos.py`: Facade para la gestión de diferentes formatos de archivo.

### Optimizaciones Implementadas

Para garantizar el rendimiento con datasets grandes, se han implementado técnicas específicas en `UtilidadesInterfaz.py`:

  * **`PandasModelConColor`:** Una implementación optimizada de `QAbstractTableModel` que utiliza caché precalculado para índices y acceso directo a arrays de **NumPy** en lugar de iterar sobre el DataFrame, mejorando drásticamente la velocidad de renderizado.
  * **`CheckableComboBox`:** Widget personalizado con manejo de eventos en el `viewport` para permitir selección múltiple estable.

-----

##  Testing

El proyecto incluye una suite de pruebas automatizadas con **Pytest** para validar la integridad de la release.

Para ejecutar las pruebas y verificar que todo funciona correctamente antes de desplegar:

```bash
pytest src/test/Tests_test.py
```

**Cobertura:**

  * Validación de métricas de Regresión vs Clasificación.
  * Ciclo de vida completo: Entrenar -\> Guardar -\> Cargar -\> Predecir.
  * Manejo de escenarios híbridos (datos binarios en modelos de regresión).

-----

##  Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](https://www.google.com/search?q=LICENSE) para más detalles.

-----

*Documentación actualizada para la Release Final v1.0.0*

```
```
