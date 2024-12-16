import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QSpinBox, QPushButton, QMessageBox

class GraphTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Controls
        self.id_selector = QComboBox()
        self.byte_start_selector = QComboBox()
        self.bit_start_selector = QComboBox()
        self.bit_length_selector = QComboBox()
        self.endian_selector = QComboBox()
        self.endian_selector.addItems(["Big Endian", "Little Endian"])
        self.plot_type_selector = QComboBox()
        self.plot_type_selector.addItems(["Line Plot", "Scatter Plot", "Bar Plot"])
        self.max_points_spinner = QSpinBox()
        self.max_points_spinner.setRange(10, 500)
        self.max_points_spinner.setValue(100)

        # Graphing
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        self.can_data = {}

    def update_can_ids(self, can_data):
        self.can_data = can_data
        self.id_selector.clear()
        self.id_selector.addItems(can_data.keys())

    def plot_data(self):
        self.ax.clear()
        self.canvas.draw()
