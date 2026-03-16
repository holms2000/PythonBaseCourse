# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main.ui'
##
## Created by: Qt User Interface Compiler version 6.10.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QLineEdit,
    QMainWindow, QMenuBar, QPushButton, QSizePolicy,
    QStatusBar, QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(800, 600)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayoutWidget = QWidget(self.centralwidget)
        self.verticalLayoutWidget.setObjectName(u"verticalLayoutWidget")
        self.verticalLayoutWidget.setGeometry(QRect(0, 0, 801, 561))
        self.verticalLayout = QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout1 = QHBoxLayout()
        self.horizontalLayout1.setObjectName(u"horizontalLayout1")
        self.lblUsername = QLabel(self.verticalLayoutWidget)
        self.lblUsername.setObjectName(u"lblUsername")

        self.horizontalLayout1.addWidget(self.lblUsername)

        self.txtUsername = QLineEdit(self.verticalLayoutWidget)
        self.txtUsername.setObjectName(u"txtUsername")

        self.horizontalLayout1.addWidget(self.txtUsername)


        self.verticalLayout.addLayout(self.horizontalLayout1)

        self.horizontalLayout2 = QHBoxLayout()
        self.horizontalLayout2.setObjectName(u"horizontalLayout2")
        self.lblPassword = QLabel(self.verticalLayoutWidget)
        self.lblPassword.setObjectName(u"lblPassword")

        self.horizontalLayout2.addWidget(self.lblPassword)

        self.txtPassword = QLineEdit(self.verticalLayoutWidget)
        self.txtPassword.setObjectName(u"txtPassword")

        self.horizontalLayout2.addWidget(self.txtPassword)


        self.verticalLayout.addLayout(self.horizontalLayout2)

        self.horizontalLayout3 = QHBoxLayout()
        self.horizontalLayout3.setObjectName(u"horizontalLayout3")
        self.LoginButton = QPushButton(self.verticalLayoutWidget)
        self.LoginButton.setObjectName(u"LoginButton")

        self.horizontalLayout3.addWidget(self.LoginButton)

        self.cancelButton = QPushButton(self.verticalLayoutWidget)
        self.cancelButton.setObjectName(u"cancelButton")

        self.horizontalLayout3.addWidget(self.cancelButton)


        self.verticalLayout.addLayout(self.horizontalLayout3)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 800, 23))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.lblUsername.setText(QCoreApplication.translate("MainWindow", u"Username:", None))
        self.lblPassword.setText(QCoreApplication.translate("MainWindow", u"Password:", None))
        self.LoginButton.setText(QCoreApplication.translate("MainWindow", u"Authenticate", None))
        self.cancelButton.setText(QCoreApplication.translate("MainWindow", u"Cancel", None))
    # retranslateUi

