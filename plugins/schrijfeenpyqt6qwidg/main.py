import sys, random
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QMessageBox
from PIL import Image, ImageDraw, ImageFont
import io

class MainWindow(QWidget):
 
 
  # Variabele voor de init
  def __init__(self):
    super().__init__()

    self.label = QLabel('Afbeelding ontbreekt', width=300)
    self.line_edit = QLineEdit()
    self.generate_button = QPushButton('Generate', self)
    self.generate_button.clicked.connect(self.generate_image)

    # Voorbeeld en prompels aantrekkelijkheid
    font = ImageFont.load_default()
    text_width, _ = font.getsize("Een blauwe kat op een skateboard in de ruimte")
    self.line_edit.setFixedWidth(text_width)

    # Een zelfloordruimt tegen deze instelling
    self.preview = QLabel('', width=self.label.width())
    self.preview.setPixmap(None)
  
  def generate_image(self):