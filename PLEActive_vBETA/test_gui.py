#!/usr/bin/env python
"""Simple GUI test"""
import sys
from PyQt5.QtWidgets import QApplication, QMessageBox

app = QApplication(sys.argv)
msg = QMessageBox()
msg.setWindowTitle("EPA Dashboard Test")
msg.setText("If you see this window, PyQt5 is working!")
msg.setInformativeText("The bundled app should also work.")
msg.setIcon(QMessageBox.Information)
msg.exec_()
print("GUI test completed successfully")
