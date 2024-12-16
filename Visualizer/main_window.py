from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QTabWidget, QLabel, QFormLayout, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem
from can_receiver import CANMessageReceiver
from graph_tab import GraphTab

class CANMessageVisualizer(QMainWindow):
    def __init__(self, serial_port):
        super().__init__()
        self.setWindowTitle('CAN Message Visualizer')

        self.receiver = CANMessageReceiver(serial_port)
        self.receiver.message_received.connect(self.update_can_data)

        self.graph_tab = GraphTab()
        self.init_ui()

        if not self.receiver.connect():
            print("Failed to connect to the serial port")
            exit()

    def init_ui(self):
        self.tabs = QTabWidget(self)
        self.setCentralWidget(self.tabs)

        self.message_tab = QWidget()
        self.message_layout = QVBoxLayout()
        self.message_tab.setLayout(self.message_layout)

        self.table = QTableWidget(0, 4)
        self.message_layout.addWidget(self.table)

        self.graph_tab = GraphTab()
        self.tabs.addTab(self.message_tab, "Messages")
        self.tabs.addTab(self.graph_tab, "Graphs")

    def update_can_data(self, message):
        # Update table with incoming CAN data
        pass
