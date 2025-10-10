

from PyQt5 import QtCore, QtGui, QtWidgets 

class Ui_QMainWindow(object):
    def setupUi(self, QMainWindow):
        QMainWindow.setObjectName("QMainWindow")
        QMainWindow.resize(800, 600)
        self.centralwidget = QtWidgets.QWidget(parent=QMainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.QVBoxLayout = QtWidgets.QVBoxLayout()
        self.QVBoxLayout.setObjectName("QVBoxLayout")
        
       
        self.dataTableWidget = QtWidgets.QTableWidget(parent=self.centralwidget)
        self.dataTableWidget.setObjectName("dataTableWidget")
        
        
        self.QVBoxLayout.addWidget(self.dataTableWidget) 
        
        self.QHBoxLayout = QtWidgets.QHBoxLayout()
        self.QHBoxLayout.setObjectName("QHBoxLayout")
        self.openFileButton = QtWidgets.QPushButton(parent=self.centralwidget)
        self.openFileButton.setAutoFillBackground(False)
        self.openFileButton.setObjectName("openFileButton")
        self.QHBoxLayout.addWidget(self.openFileButton)
        self.filePathLineEdit = QtWidgets.QLineEdit(parent=self.centralwidget)
        self.filePathLineEdit.setReadOnly(True)
        self.filePathLineEdit.setObjectName("filePathLineEdit")
        self.QHBoxLayout.addWidget(self.filePathLineEdit)
        self.QVBoxLayout.addLayout(self.QHBoxLayout)
        self.horizontalLayout.addLayout(self.QVBoxLayout)
        QMainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(parent=QMainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 26))
        self.menubar.setObjectName("menubar")
        QMainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(parent=QMainWindow)
        self.statusbar.setObjectName("statusbar")
        QMainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(QMainWindow)
        QtCore.QMetaObject.connectSlotsByName(QMainWindow)

    def retranslateUi(self, QMainWindow):
        _translate = QtCore.QCoreApplication.translate
        QMainWindow.setWindowTitle(_translate("QMainWindow", "MainWindow"))
       
        self.openFileButton.setText(_translate("QMainWindow", "Abrir Archivo"))
        self.filePathLineEdit.setPlaceholderText(_translate("QMainWindow", "Ningún archivo cargado"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    QMainWindow = QtWidgets.QMainWindow()
    ui = Ui_QMainWindow()
    ui.setupUi(QMainWindow)
    QMainWindow.show()
    sys.exit(app.exec_()) # ## CAMBIO 4: Para PyQt5 es app.exec_()