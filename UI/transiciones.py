import sys
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QCoreApplication
from PyQt6.QtWidgets import QStackedWidget, QGraphicsOpacityEffect

class TransicionPaginas:
    """
    Gestiona una transición de fundido (fade-in/fade-out) para un QStackedWidget.

    Esta clase se inicializa con la ventana principal (que contiene el 
    QStackedWidget en 'ui.conjuntoTabs') y proporciona un método 
    `cambiarPagina` para animar el cambio de pestaña.
    """
    
    def __init__(self, main_window, duration=300):
        """
        Inicializa el gestor de transiciones.

        Args:
            main_window: La instancia de QMainWindow que contiene el 
                         QStackedWidget (se espera en main_window.ui.conjuntoTabs).
            duration (int): Duración de la animación de fundido en milisegundos.
        """
        self.stacked_widget = main_window.ui.conjuntoTabs
        self.duration = duration
        
        # Guardamos las animaciones como atributos para evitar que 
        # el recolector de basura las elimine a mitad de ejecución.
        self.fade_out_anim = None
        self.fade_in_anim = None

    def _get_or_create_opacity_effect(self, widget):
        """
        Obtiene el QGraphicsOpacityEffect de un widget, o crea uno si no existe.
        """
        effect = widget.graphicsEffect()
        if isinstance(effect, QGraphicsOpacityEffect):
            return effect
        else:
            new_effect = QGraphicsOpacityEffect(widget)
            widget.setGraphicsEffect(new_effect)
            return new_effect

    def cambiarPagina(self, new_index):
        """
        Realiza una transición de fundido a la página (índice) especificada.
        """
        current_index = self.stacked_widget.currentIndex()
        if new_index == current_index:
            return  # No hacer nada si ya estamos en esa página

        current_widget = self.stacked_widget.widget(current_index)
        new_widget = self.stacked_widget.widget(new_index)

        # 1. Preparar el widget que entra (totalmente transparente)
        new_effect = self._get_or_create_opacity_effect(new_widget)
        new_effect.setOpacity(0.0)

        # 2. Preparar el widget que sale (totalmente opaco)
        current_effect = self._get_or_create_opacity_effect(current_widget)
        current_effect.setOpacity(1.0)

        # 3. Crear animación de fundido (fade-out) para el widget actual
        self.fade_out_anim = QPropertyAnimation(current_effect, b"opacity")
        self.fade_out_anim.setDuration(self.duration)
        self.fade_out_anim.setStartValue(1.0)
        self.fade_out_anim.setEndValue(0.0)
        self.fade_out_anim.setEasingCurve(QEasingCurve.Type.InQuad)

        # 4. Crear animación de aparición (fade-in) para el nuevo widget
        self.fade_in_anim = QPropertyAnimation(new_effect, b"opacity")
        self.fade_in_anim.setDuration(self.duration)
        self.fade_in_anim.setStartValue(0.0)
        self.fade_in_anim.setEndValue(1.0)
        self.fade_in_anim.setEasingCurve(QEasingCurve.Type.OutQuad)

        # 5. Conectar las animaciones:
        
        #    Cuando el fade-out termine, cambia el índice y empieza el fade-in.
        self.fade_out_anim.finished.connect(lambda: (
            self.stacked_widget.setCurrentIndex(new_index),
            self.fade_in_anim.start()
        ))

        # ===================================================================
        # LÍNEA NUEVA: Esta es la corrección
        # ===================================================================
        # Cuando la animación de ENTRADA (fade_in) termine, restaura la 
        # opacidad del widget que SALIÓ (current_effect) a 1.0.
        # Esto ocurre mientras la página 1 está oculta, así que no se ve.
        self.fade_in_anim.finished.connect(lambda: current_effect.setOpacity(1.0))
        # ===================================================================

        # 6. Iniciar la secuencia
        self.fade_out_anim.start()