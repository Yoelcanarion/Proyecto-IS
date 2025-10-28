
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve
from PyQt6.QtWidgets import QGraphicsOpacityEffect


class TransicionPaginas:
    """
    Clase para manejar las transiciones animadas entre páginas usando efectos de fade.
    
    Attributes:
        main_window: Referencia a la ventana principal que contiene el QTabWidget
        animando (bool): Flag para prevenir múltiples animaciones simultáneas
    """
    
    def __init__(self, main_window):
        """
        Inicializa el gestor de transiciones.
        
        Args:
            main_window: Instancia de la ventana principal (MainWindowCtrl)
        """
        self.main_window = main_window
        self.animando = False
        self.widget_anterior = None
        
    def cambiarPaginaConAnimacion(self, indice_destino):
        """
        Cambia de página con una animación de desvanecimiento (fade out + fade in).
        
        Args:
            indice_destino (int): Índice de la pestaña de destino
        """
        if self.animando:
            return
            
        self.animando = True
        widget_actual = self.main_window.ui.conjuntoTabs.currentWidget()
        self.widget_anterior = widget_actual
        
        # Crear efecto de opacidad para el fade out
        efecto = QGraphicsOpacityEffect()
        widget_actual.setGraphicsEffect(efecto)
        
        # Animación de fade out (desvanecimiento)
        self.anim_out = QPropertyAnimation(efecto, b"opacity")
        self.anim_out.setDuration(300)  # 300ms de duración
        self.anim_out.setStartValue(1.0)
        self.anim_out.setEndValue(0.0)
        self.anim_out.setEasingCurve(QEasingCurve.Type.InOutCubic)
        
        # Cuando termine el fade out, cambiar de página y hacer fade in
        self.anim_out.finished.connect(lambda: self._completarTransicion(indice_destino))
        self.anim_out.start()
    
    def _completarTransicion(self, indice_destino):
        """
        Completa la transición cambiando de página y aplicando fade in.
        
        Args:
            indice_destino (int): Índice de la pestaña de destino
        """
        # Limpiar efecto del widget anterior ANTES de cambiar
        if self.widget_anterior:
            self.widget_anterior.setGraphicsEffect(None)
        
        # Cambiar a la nueva página
        self.main_window.ui.conjuntoTabs.setCurrentIndex(indice_destino)
        widget_nuevo = self.main_window.ui.conjuntoTabs.currentWidget()
        
        # Crear efecto de opacidad para el fade in
        efecto = QGraphicsOpacityEffect()
        widget_nuevo.setGraphicsEffect(efecto)
        
        # Animación de fade in (aparición)
        self.anim_in = QPropertyAnimation(efecto, b"opacity")
        self.anim_in.setDuration(300)  # 300ms de duración
        self.anim_in.setStartValue(0.0)
        self.anim_in.setEndValue(1.0)
        self.anim_in.setEasingCurve(QEasingCurve.Type.InOutCubic)
        
        # Al terminar, limpiar el efecto y permitir nuevas animaciones
        self.anim_in.finished.connect(self._limpiarEfectos)
        self.anim_in.start()
    
    def _limpiarEfectos(self):
        """
        Limpia los efectos gráficos aplicados y habilita nuevas animaciones.
        """
        # Limpiar efecto del widget actual
        widget = self.main_window.ui.conjuntoTabs.currentWidget()
        widget.setGraphicsEffect(None)
        
        # Limpiar efecto del widget anterior por si acaso
        if self.widget_anterior:
            self.widget_anterior.setGraphicsEffect(None)
            self.widget_anterior = None
        
        # Limpiar TODOS los widgets para asegurar que no quede ningún efecto
        for i in range(self.main_window.ui.conjuntoTabs.count()):
            w = self.main_window.ui.conjuntoTabs.widget(i)
            if w and w.graphicsEffect() is not None:
                w.setGraphicsEffect(None)
        
        self.animando = False