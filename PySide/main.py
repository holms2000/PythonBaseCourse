import sys
from PySide6 import QtWidgets
from ui_main import *

class LearnPyQtWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
    
    def initUI(self):
        self.setupUi(self)
        btn1 = self.LoginButton
        btn1.clicked.connect(self.buttonClicked)
        btn2 = self.cancelButton
        btn2.clicked.connect(self.buttonClicked)
        self.show()

    def accept(self):
     
        print("You clicked the OK button...")
        # Enable self.close() to close the dialog on clicking.
        # self.close()
 
    def reject(self):
        print("You clicked the Cancel button...")
        # Enable self.close() to close the dialog on clicking.
        # self.close()

    def keyPressEvent(self, e):
        print(e.key())
        if e.key() == Qt.Key_Escape:
            self.close()
    
    def buttonClicked(self):

        sender = self.sender()
        print(sender.text() + ' was pressed')
 
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    login = LearnPyQtWindow()
    sys.exit(app.exec())