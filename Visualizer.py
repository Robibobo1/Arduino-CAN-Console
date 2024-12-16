import sys
import time 
import json
import serial
import threading
import pandas as pd
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QTableWidget, QTableWidgetItem, QWidget, QLabel)
from PyQt5.QtCore import pyqtSignal, QObject, Qt
from PyQt5.QtGui import QFont

class CANMessageReceiver(QObject):
    # Signal to update the GUI with new CAN message
    message_received = pyqtSignal(dict)

    def __init__(self, port, baudrate=250000):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.running = False
        self.serial_connection = None
        self.last_receive_times = {}
        self.recent_periods = {}  # Tracks recent periods for each CAN ID

    def connect(self):
        try:
            self.serial_connection = serial.Serial(self.port, self.baudrate, timeout=1)
            self.running = True
            threading.Thread(target=self.receive_messages, daemon=True).start()
            return True
        except serial.SerialException as e:
            print(f"Error connecting to serial port: {e}")
            return False

    def receive_messages(self):
        while self.running:
            try:
                if self.serial_connection.in_waiting:
                    line = self.serial_connection.readline().decode('utf-8').strip()
                    try:
                        message = json.loads(line)

                        # Calculate period
                        current_time = time.time()  # Use current timestamp
                        can_id = message['ID']
                        period = 0

                        if can_id in self.last_receive_times:
                            period = (current_time - self.last_receive_times[can_id]) * 1000  # Convert to ms

                        self.last_receive_times[can_id] = current_time

                        # Track recent periods for smoothing
                        if can_id not in self.recent_periods:
                            self.recent_periods[can_id] = []

                        self.recent_periods[can_id].append(period)
                        if len(self.recent_periods[can_id]) > 20:  # Rolling window of 5
                            self.recent_periods[can_id].pop(0)

                        # Compute average of recent periods
                        average_period = sum(self.recent_periods[can_id]) / len(self.recent_periods[can_id])

                        # Add the smoothed, rounded period to the message
                        message['Period'] = round(average_period, 2)

                        self.message_received.emit(message)
                    except json.JSONDecodeError:
                        # Skip invalid JSON
                        pass
            except Exception as e:
                print(f"Error receiving message: {e}")
                self.running = False


    def stop(self):
        self.running = False
        if self.serial_connection:
            self.serial_connection.close()

class CANMessageVisualizer(QMainWindow):
    def __init__(self, serial_port):
        super().__init__()
        self.setWindowTitle('CAN Message Analyzer')
        self.resize(800, 600)

        # Data tracking
        self.can_data = {}

        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # Title
        title = QLabel('CAN Message Analyzer')
        title.setFont(QFont('Arial', 16))
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # Table to display CAN messages
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['CAN ID', 'Last Data', 'Length', 'Period (ms)'])
        main_layout.addWidget(self.table)

        # Setup message receiver
        self.receiver = CANMessageReceiver(serial_port)
        self.receiver.message_received.connect(self.update_can_data)

        # Connect to serial port
        if not self.receiver.connect():
            print("Failed to connect to serial port")
            sys.exit(1)

        self.show()

    def update_can_data(self, message):
        # Convert ID to hex string for consistent key
        can_id = f"0x{message['ID']:X}"

        # Update or create entry for this CAN ID
        if can_id not in self.can_data:
            self.can_data[can_id] = {
                'last_data': message['Data'],
                'length': message['Length'],
                'period': message.get('Period', 0),
                'count': 1
            }
        else:
            self.can_data[can_id].update({
                'last_data': message['Data'],
                'period': message.get('Period', 0),
                'count': self.can_data[can_id]['count'] + 1
            })

        # Update table
        self.update_table()

    def update_table(self):
        # Clear existing rows
        self.table.setRowCount(0)

        # Populate table with current data
        for can_id, data in self.can_data.items():
            row_position = self.table.rowCount()
            self.table.insertRow(row_position)

            # CAN ID
            self.table.setItem(row_position, 0, QTableWidgetItem(can_id))

            # Last Data (convert to hex string)
            data_str = ' '.join([f'{d:02X}' for d in data['last_data']])
            self.table.setItem(row_position, 1, QTableWidgetItem(data_str))

            # Length
            self.table.setItem(row_position, 2, QTableWidgetItem(str(data['length'])))

            # Period
            self.table.setItem(row_position, 3, QTableWidgetItem(f"{data['period']:.2f} ms"))

        # Resize columns to content
        self.table.resizeColumnsToContents()

    def closeEvent(self, event):
        # Stop the receiver when the window is closed
        self.receiver.stop()
        event.accept()

def main():
    # Specify the serial port (change this to match your Arduino's port)
    #SERIAL_PORT = '/dev/ttyACM0'  # Linux/Mac example
    SERIAL_PORT = 'COM3'  # Windows example

    app = QApplication(sys.argv)
    visualizer = CANMessageVisualizer(SERIAL_PORT)
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

# Dependencies:
# pip install pyserial pyqt5 numpy pandas