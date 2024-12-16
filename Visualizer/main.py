import sys
from PyQt5.QtWidgets import QApplication
from main_window import CANMessageVisualizer

def main():
    app = QApplication(sys.argv)
    visualizer = CANMessageVisualizer(serial_port="COM3")
    visualizer.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
