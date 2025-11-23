import sys
from PyQt6.QtCore import QObject
from PyQt6.QtWidgets import QStackedWidget

class TransicionPaginas(QObject):
    """
    Gestiona el cambio de página en un QStackedWidget.
    
    Versión Simplificada: Realiza un cambio directo (instantáneo) sin animaciones
    para evitar parpadeos, bloqueos o problemas de opacidad. 
    Se comporta exactamente como un QTabWidget nativo.
    """
    
    def __init__(self, main_window, duration=300):
        super().__init__()
        self.stacked_widget = main_window.ui.conjuntoTabs
        # El parámetro 'duration' se mantiene para compatibilidad con tu código existente,
        # pero ya no se utiliza para animaciones.

    def _asegurar_visibilidad(self):
        """
        Elimina cualquier efecto de opacidad residual que haya podido quedar
        de versiones anteriores del código, asegurando que la página sea visible.
        """
        for i in range(self.stacked_widget.count()):
            widget = self.stacked_widget.widget(i)
            if widget and widget.graphicsEffect():
                widget.setGraphicsEffect(None)

    def cambiarPagina(self, new_index):
        """
        Cambia la página de forma directa.
        """
        # 1. Limpieza de seguridad (por si quedó algún efecto 'fade' a medias antes)
        self._asegurar_visibilidad()
        
        # 2. Cambio estándar de Qt (Instantáneo y fluido)
        self.stacked_widget.setCurrentIndex(new_index)