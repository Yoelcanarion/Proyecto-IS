# Guía de Contribución - ML Desktop Assistant

¡Gracias por tu interés en contribuir a **T-PAPIPLAIN**! 🎉

Este documento establece las pautas para contribuir al proyecto, asegurando que el código se mantenga limpio, escalable y libre de errores. Por favor, lee estas normas antes de enviar tu Pull Request.

---

## 🚀 Primeros Pasos

### 1. Configuración del Entorno
Para asegurar la compatibilidad y evitar el "infierno de dependencias", sigue estos pasos:

1.  **Clona el repositorio:**
    ```bash
    git clone [https://github.com/Yoelcanarion/Proyecto-IS.git]
    cd Proyecto-IS
    ```

2.  **Crea un entorno de conda:**
    * Windows: conda create --n NombreEntorno python==3.11

3.  **Instala las dependencias:**
    ```bash
    pip install pandas numpy scikit-learn PyQt6 plotly scipy pytest openpyxl PyQt6-WebEngine
    ```

---

## 🛠️ Flujo de Trabajo (Gitflow)

Utilizamos una variante simplificada de **Gitflow**.

* 🔴 **`main`**: Contiene el código de producción estable (versiones finales). **Nunca hagas push directo aquí.**
* 🟡 **`dev`**: Rama principal de desarrollo. Aquí se integran las nuevas funcionalidades.
* 🔵 **Ramas de Feature/Fix**: Crea una rama para cada tarea desde `dev`.

### Naming de Ramas
Usa el formato: `tipo/descripcion-breve`
* `feature/nueva-grafica`
* `fix/error-carga-csv`
* `docs/actualizar-readme`
* `test/cobertura-regresion`

---

## 📝 Normas de Commit (Conventional Commits)

Es **obligatorio** seguir la convención de [Conventional Commits](https://www.conventionalcommits.org/) para mantener un historial limpio y legible.

**Estructura:**
`tipo(ámbito): descripción breve en imperativo`

**Tipos permitidos:**
* `feat`: Una nueva funcionalidad (ej: añadir soporte para archivos .json).
* `fix`: Solución a un bug.
* `docs`: Cambios solo en la documentación.
* `style`: Cambios de formato (espacios, puntos y comas) que no afectan el código.
* `refactor`: Cambio de código que no arregla bugs ni añade features (limpieza).
* `test`: Añadir o corregir tests.
* `chore`: Tareas de mantenimiento (actualizar dependencias, configurar CI).

**Ejemplos:**
✅ `feat(backend): añadir imputación de nulos por mediana`
✅ `fix(ui): corregir cierre inesperado en ventana de predicción`
✅ `docs(readme): actualizar instrucciones de instalación`

---

## 🏗️ Estándares de Código

### Arquitectura MVC
El proyecto sigue estrictamente el patrón **Modelo-Vista-Controlador**.
1.  **Vista (`src/UI/`):** Solo código visual. No añadas lógica de negocio aquí.
2.  **Controlador (`src/UI/MainWindowCtrl.py`):** Gestiona eventos y comunica la vista con el backend.
3.  **Modelo (`src/Backend/`):** Aquí va toda la lógica de Machine Learning, Pandas y cálculos.

### Estilo de Python
* **Variables y Funciones:** Usamos **`camelCase`** (ej: `cargarDatos`, `columnasEntrada`) para mantener consistencia con PyQt.
* **Clases:** Usamos **`PascalCase`** (ej: `MainWindowCtrl`).
* **Docstrings:** Todas las funciones complejas deben tener comentarios explicando argumentos y retornos.

---

## 🧪 Tests y Calidad

Antes de enviar tu código, asegúrate de que no rompe nada.

1.  **Ejecuta los tests locales:**
    ```bash
    pytest src/test/Tests_test.py
    ```
2.  **Integración Continua (CI):**
    Al subir tu PR, GitHub Actions ejecutará los tests automáticamente en un entorno Linux (con `xvfb` para la GUI). Si el CI falla (❌), tu PR no será aceptado hasta que lo arregles.

---

## 🔄 Proceso de Pull Request (PR)

1.  Asegúrate de que tu rama está actualizada con `dev`.
2.  Sube tu rama (`git push origin feature/mi-feature`).
3.  Abre un Pull Request hacia la rama **`dev`**.
4.  Rellena la descripción del PR explicando qué cambios has hecho.
5.  Espera a que un compañero revise el código y el CI pase en verde.

---

¡Gracias por ayudarnos a mejorar T-PAPIPLAIN*! 🚀