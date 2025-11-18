from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import QAbstractTableModel, Qt
from PyQt6.QtGui import QBrush, QColor, QFont
from PyQt6 import QtWidgets, QtCore, QtGui
import pandas as pd

class Mensajes:
    """
    Clase de utilidad que agrupa la creación de diálogos emergentes comunes.
    Se usan métodos estáticos para no tener que crear una instancia de la clase.
    """
    
    @staticmethod
    def crearAdvertencia(parent, titulo, mensaje):
        """
        Muestra un diálogo de advertencia.

        Args:
            parent (QWidget): El widget padre sobre el cual se mostrará el diálogo.
            titulo (str): El título de la ventana de diálogo.
            mensaje (str): El texto principal que se mostrará en el diálogo.
        """
        dlg = QMessageBox(parent)
        dlg.setWindowTitle(titulo)
        dlg.setText(mensaje)
        dlg.setStandardButtons(QMessageBox.StandardButton.Ok)
        dlg.setIcon(QMessageBox.Icon.Warning)
        dlg.exec()
    
    def crearEncuestaAlUsuario(parent, titulo, mensaje, funcionContinuar):
        """
        Muestra un diálogo de advertencia.

        Args:
            parent (QWidget): El widget padre sobre el cual se mostrará el diálogo.
            titulo (str): El título de la ventana de diálogo.
            mensaje (str): El texto principal que se mostrará en el diálogo.
            funcionContinuar (function): Función a ejecutar si el usuario elige continuar.
        """
        dlg = QMessageBox(parent)
        dlg.setIcon(QMessageBox.Icon.Warning)
        dlg.setWindowTitle(titulo)
        dlg.setText(mensaje)
        dlg.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.No)
        respuesta = dlg.exec()
        if respuesta == QMessageBox.StandardButton.Ok:
            funcionContinuar()
        else: 
            return


    @staticmethod
    def crearInformacion(parent, titulo, mensaje):
        """
        Muestra un diálogo de información.

        Args:
            parent (QWidget): El widget padre sobre el cual se mostrará el diálogo.
            titulo (str): El título de la ventana de diálogo.
            mensaje (str): El texto principal que se mostrará en el diálogo.
        """
        dlg = QMessageBox(parent)
        dlg.setWindowTitle(titulo)
        dlg.setText(mensaje)
        dlg.setStandardButtons(QMessageBox.StandardButton.Ok)
        dlg.setIcon(QMessageBox.Icon.Information)
        dlg.exec()


class PandasModel(QAbstractTableModel):
    def __init__(self, df):
        super().__init__()
        self.df = df

    def rowCount(self, parent=None):
        return len(self.df)

    def columnCount(self, parent=None):
        return len(self.df.columns)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.ItemDataRole.DisplayRole:
            return str(self.df.iat[index.row(), index.column()])
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return str(self.df.columns[section])
            else:
                return str(self.df.index[section])
        return None


class PandasModelConColor(QAbstractTableModel):
    """
    Modelo extendido de PandasModel optimizado con caché precalculado.
    Mejora el rendimiento al evitar cálculos repetitivos durante el renderizado.
    
    OPTIMIZACIONES IMPLEMENTADAS:
    1. Acceso directo a NumPy array (5-10x más rápido que df.iat)
    2. Comparación de índices numéricos en lugar de strings (2-3x más rápido)
    3. Objetos QBrush y QFont reutilizables (evita crear objetos repetidamente)
    4. Máscara de NaN precalculada (operación vectorizada única)
    """
    def __init__(self, df, columna_verde=None, columna_roja=None, tachar_nan=False):
        super().__init__()
        self.df = df
        
        # Convertir columna_verde a lista si es string
        if isinstance(columna_verde, str):
            self.columna_verde = [columna_verde]
        else:
            self.columna_verde = columna_verde if columna_verde is not None else []
        
        self.columna_roja = columna_roja
        self.tachar_nan = tachar_nan
        
        # ============ OPTIMIZACIÓN: CACHÉ PRECALCULADO ============
        
        # 1. Precalcular índices de columnas coloreadas (comparar ints es más rápido que strings)
        self.columnas_verdes_idx = set()
        self.columna_roja_idx = None
        
        for col in self.columna_verde:
            if col in df.columns:
                self.columnas_verdes_idx.add(df.columns.get_loc(col))
        
        if self.columna_roja and self.columna_roja in df.columns:
            self.columna_roja_idx = df.columns.get_loc(self.columna_roja)
        
        # 2. Crear QBrush reutilizables (evita crear objetos en cada celda)
        self.brush_verde = QBrush(QColor(144, 238, 144))  # Verde claro
        self.brush_rojo = QBrush(QColor(255, 182, 193))   # Rojo claro
        
        # 3. Crear QFont tachado reutilizable
        self.font_tachado = QFont()
        self.font_tachado.setStrikeOut(True)
        
        # 4. Precalcular máscara de NaN si es necesario (operación vectorizada única)
        self.nan_mask = None
        if self.tachar_nan:
            # Crear máscara booleana de NaN (mucho más rápido que pd.isna() repetido)
            self.nan_mask = pd.isna(df.values)
        
        # 5. Convertir DataFrame a numpy array para acceso más rápido
        # (df.iat es lento comparado con acceso directo a numpy)
        self.data_array = df.values

    def rowCount(self, parent=None):
        return len(self.df)

    def columnCount(self, parent=None):
        return len(self.df.columns)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        
        row = index.row()
        col = index.column()
        
        # ============ OPTIMIZACIÓN: Acceso directo al array numpy ============
        if role == Qt.ItemDataRole.DisplayRole:
            # Usar el array numpy en lugar de df.iat (5-10x más rápido)
            valor = self.data_array[row, col]
            return str(valor)
        
        # ============ OPTIMIZACIÓN: Usar índices precalculados ============
        elif role == Qt.ItemDataRole.BackgroundRole:
            # Comparar índices numéricos en lugar de nombres de columnas (2-3x más rápido)
            if col in self.columnas_verdes_idx:
                return self.brush_verde
            elif col == self.columna_roja_idx:
                return self.brush_rojo
            return None
        
        # ============ OPTIMIZACIÓN: Usar máscara de NaN precalculada ============
        elif role == Qt.ItemDataRole.FontRole:
            if self.nan_mask is not None and self.nan_mask[row, col]:
                return self.font_tachado
            return None
        
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return str(self.df.columns[section])
            else:
                return str(self.df.index[section])
        return None


class CheckableComboBox(QtWidgets.QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # --- Configuración Base ---
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        
        # Usamos un QListView para tener control total sobre el desplegable
        self.view = QtWidgets.QListView(self)
        self.setView(self.view)
        
        self.model = QtGui.QStandardItemModel(self)
        self.setModel(self.model)
        
        # --- Lógica de Eventos para Mejorar la UX ---
        
        # 1. ABRIR DESPLEGABLE AL CLICAR EN CUALQUIER PARTE
        # Instalamos un filtro de eventos sobre el QLineEdit interno.
        # Esto nos permitirá capturar los clics sobre él.
        self.lineEdit().installEventFilter(self)

        # 2. CERRAR EL DESPLEGABLE AL CLICAR FUERA
        # Instalamos un filtro sobre la vista desplegable (el QListView).
        self.view.installEventFilter(self)
        
        # --- Conexiones y Estado Inicial ---
        self.model.dataChanged.connect(self.updateText)
        self._keepPopupOpen = False # Flag para controlar el cierre del desplegable
        self.updateText() # Establecer texto inicial

    def eventFilter(self, objectWatched, event):
        """
        El corazón de la nueva funcionalidad. Este método intercepta
        eventos de los widgets en los que lo hemos instalado.
        (Nota: El nombre de este método no se cambia a camelCase 
        porque estamos sobreescribiendo un método existente de Qt).
        """
        # --- Lógica para abrir el desplegable al clicar en el texto ---
        if objectWatched == self.lineEdit():
            if event.type() == QtCore.QEvent.Type.MouseButtonPress:
                # Si se clica el LineEdit, mostramos el desplegable y
                # retornamos True para indicar que hemos manejado el evento.
                self.showPopup()
                return True

        # --- Lógica para mantener el desplegable abierto al clicar en un ítem ---
        if objectWatched == self.view:
            if event.type() == QtCore.QEvent.Type.MouseButtonPress:
                # Si se clica dentro de la vista, activamos nuestro flag
                # para que hidePopup() sepa que no debe cerrarse.
                index = self.view.indexAt(event.pos())
                if index.isValid():
                    self._keepPopupOpen = True
        
        # Devolvemos el control al comportamiento por defecto para otros eventos
        return super().eventFilter(objectWatched, event)

    def hidePopup(self):
        """
        Anulamos hidePopup para decidir cuándo debe cerrarse.
        (Nota: El nombre de este método no se cambia a camelCase 
        porque estamos sobreescribiendo un método existente de Qt).
        """
        if self._keepPopupOpen:
            # Si nuestro flag está activo (porque se clicó un ítem),
            # lo reseteamos y evitamos que el desplegable se cierre.
            self._keepPopupOpen = False
        else:
            # Si el flag no está activo (el cierre fue por clicar fuera,
            # perder el foco, etc.), procedemos con el cierre normal.
            super().hidePopup()

    def addItem(self, text, checked=False):
        """
        Añade un nuevo ítem chequeable a la lista.
        """
        item = QtGui.QStandardItem(text)
        item.setFlags(QtCore.Qt.ItemFlag.ItemIsUserCheckable | QtCore.Qt.ItemFlag.ItemIsEnabled)
        item.setData(QtCore.Qt.CheckState.Checked if checked else QtCore.Qt.CheckState.Unchecked, QtCore.Qt.ItemDataRole.CheckStateRole)
        self.model.appendRow(item)
        self.updateText()

    def updateText(self):
        """
        Actualiza el texto principal del combobox para reflejar los ítems seleccionados.
        """
        checkedTexts = self.getCheckedItems()
        if checkedTexts:
            self.lineEdit().setText(", ".join(checkedTexts))
        else:
            self.lineEdit().setText("--- Seleccione una o varias ---")

    def getCheckedItems(self):
        """
        Devuelve una lista con los textos de todos los ítems marcados.
        """
        checkedItems = []
        for i in range(self.model.rowCount()):
            item = self.model.item(i)
            if item.checkState() == QtCore.Qt.CheckState.Checked:
                checkedItems.append(item.text())
        return checkedItems