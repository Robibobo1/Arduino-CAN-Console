import sys
import json
import time
import serial
import threading
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QTableWidget, QTableWidgetItem, QWidget, QLabel, 
                             QLineEdit, QPushButton, QFormLayout, QTabWidget,
                             QComboBox, QSpinBox, QMessageBox)
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
        self.recent_periods = {}

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
                        if len(self.recent_periods[can_id]) > 10:  # Rolling window of 10
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

    def send_message(self, can_id, length, data):
        """
        Send a CAN frame through the serial connection.
        :param can_id: int - CAN ID of the frame
        :param length: int - Length of the data (1-8 bytes)
        :param data: list[int] - List of data bytes (0-255)
        """
        if not self.serial_connection or not self.running:
            print("Error: Serial connection is not active.")
            return

        if length > 8 or length < 1:
            print("Error: Length must be between 1 and 8 bytes.")
            return

        try:
            outString = f"{can_id},{length},{','.join([str(d) for d in data])}"
            # Send the frame as a JSON string
            self.serial_connection.write((outString + '\n').encode('utf-8'))
            print(f"Sent frame: {outString}")
        except Exception as e:
            print(f"Error sending message: {e}")

    def stop(self):
        self.running = False
        if self.serial_connection:
            self.serial_connection.close()

class GraphTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Main layout for the graph tab
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Upper controls layout
        upper_controls_layout = QHBoxLayout()
        
        # CAN ID Selector
        self.id_selector = QComboBox()
        self.id_selector.currentTextChanged.connect(self.update_graph_options)
        upper_controls_layout.addWidget(QLabel("CAN ID:"))
        upper_controls_layout.addWidget(self.id_selector)
        
        # Byte Start Selector
        self.byte_start_selector = QComboBox()
        self.byte_start_selector.currentTextChanged.connect(self.update_bit_options)
        upper_controls_layout.addWidget(QLabel("Start Byte:"))
        upper_controls_layout.addWidget(self.byte_start_selector)
        
        layout.addLayout(upper_controls_layout)
        
        # Bit selection layout
        bit_controls_layout = QHBoxLayout()
        
        # Bit Start Selector
        self.bit_start_selector = QComboBox()
        bit_controls_layout.addWidget(QLabel("Start Bit:"))
        bit_controls_layout.addWidget(self.bit_start_selector)
        
        # Total Bit Length Selector
        self.bit_length_selector = QComboBox()
        bit_controls_layout.addWidget(QLabel("Total Bit Length:"))
        bit_controls_layout.addWidget(self.bit_length_selector)
        
        # Endianness Selector
        self.endian_selector = QComboBox()
        self.endian_selector.addItems(["Big Endian", "Little Endian"])
        bit_controls_layout.addWidget(QLabel("Endianness:"))
        bit_controls_layout.addWidget(self.endian_selector)
        
        layout.addLayout(bit_controls_layout)
        
        # Lower controls layout
        lower_controls_layout = QHBoxLayout()
        
        # Plot type selector
        self.plot_type_selector = QComboBox()
        self.plot_type_selector.addItems(["Line Plot", "Scatter Plot", "Bar Plot"])
        lower_controls_layout.addWidget(QLabel("Plot Type:"))
        lower_controls_layout.addWidget(self.plot_type_selector)
        
        # Max data points
        self.max_points_spinner = QSpinBox()
        self.max_points_spinner.setRange(10, 500)
        self.max_points_spinner.setValue(100)
        lower_controls_layout.addWidget(QLabel("Max Points:"))
        lower_controls_layout.addWidget(self.max_points_spinner)
        
        # Plot button
        plot_button = QPushButton("Plot")
        plot_button.clicked.connect(self.plot_data)
        lower_controls_layout.addWidget(plot_button)
        
        layout.addLayout(lower_controls_layout)
        
        # Matplotlib Figure
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        # Data storage
        self.can_data = {}
        
    def update_can_ids(self, can_data):
        """Update available CAN IDs in the selector"""
        current_id = self.id_selector.currentText()
        self.can_data = can_data
        
        # Update CAN ID selector
        self.id_selector.clear()
        self.id_selector.addItems(list(can_data.keys()))
        
        # Restore previous selection if possible
        if current_id in can_data:
            index = self.id_selector.findText(current_id)
            if index >= 0:
                self.id_selector.setCurrentIndex(index)
    
    def update_graph_options(self):
        """Update byte start selector based on selected CAN ID"""
        if not self.id_selector.currentText():
            return
        
        can_id = self.id_selector.currentText()
        data = self.can_data.get(can_id, {}).get('last_data', [])
        
        # Update byte start selector
        self.byte_start_selector.clear()
        self.byte_start_selector.addItems([f"Byte {i} (0x{data[i]:02X})" for i in range(len(data))])
        
        # Trigger bit options update for first byte
        self.update_bit_options()
    
    def update_bit_options(self):
        """Update bit selectors based on selected byte"""
        # Clear previous bit selections
        self.bit_start_selector.clear()
        self.bit_length_selector.clear()
        
        can_id = self.id_selector.currentText()
        data_length = len(self.can_data.get(can_id, {}).get('last_data', []))
        
        # Bit start options
        self.bit_start_selector.addItems([str(i) for i in range(8)])
        
        # Total bit length options
        # Dynamically adjust max possible length based on selected start byte and total message length
        if self.byte_start_selector.currentText():
            start_byte = int(self.byte_start_selector.currentText().split()[1])
            max_bits = (data_length - start_byte) * 8
            length_options = [str(i) for i in range(1, max_bits + 1)]
            self.bit_length_selector.addItems(length_options)
    
    def extract_multi_bit_value(self, messages, start_byte, start_bit, total_bit_length, is_little_endian=True):
        """
        Extract multi-byte value from CAN messages
        
        :param messages: List of message byte arrays
        :param start_byte: Starting byte index
        :param start_bit: Starting bit within the start byte (0-7)
        :param total_bit_length: Total number of bits to extract
        :param is_little_endian: Endianness of the value
        :return: List of extracted values
        """
        collected_values = []
        
        for msg in messages:
            # Ensure we have enough bytes in the message
            if start_byte + (total_bit_length + 7) // 8 > len(msg):
                continue
            
            # Calculate total bytes needed
            bytes_needed = (start_bit + total_bit_length + 7) // 8
            
            # Extract bytes
            extracted_bytes = msg[start_byte:start_byte + bytes_needed]
            
            # Reconstruct value considering endianness
            value = 0
            if is_little_endian:
                # Little Endian: Least significant byte first
                for i, byte in enumerate(extracted_bytes):
                    value |= (byte << (i * 8))
            else:
                # Big Endian: Most significant byte first
                for i, byte in enumerate(reversed(extracted_bytes)):
                    value |= (byte << (i * 8))
            
            # Create bit mask
            mask = (1 << total_bit_length) - 1
            
            # Apply mask and shift if start_bit is non-zero
            value = (value >> start_bit) & mask
            
            collected_values.append(value)
        
        return collected_values
    
    def plot_data(self):
        """Plot the selected data"""
        if not self.id_selector.currentText():
            return
        
        # Clear previous plot
        self.ax.clear()
        
        # Get selected data
        can_id = self.id_selector.currentText()
        start_byte = int(self.byte_start_selector.currentText().split()[1])
        start_bit = int(self.bit_start_selector.currentText())
        total_bit_length = int(self.bit_length_selector.currentText())
        plot_type = self.plot_type_selector.currentText()
        max_points = self.max_points_spinner.value()
        is_little_endian = self.endian_selector.currentText() == "Little Endian"
        
        # Collect data for this CAN ID 
        messages = self.can_data[can_id].get('raw_messages', [])[-max_points:]
        
        try:
            # Extract multi-bit value
            collected_data = self.extract_multi_bit_value(
                messages, 
                start_byte, 
                start_bit, 
                total_bit_length, 
                is_little_endian
            )
            
            # Plot based on selected type
            if plot_type == "Line Plot":
                self.ax.plot(collected_data, marker='o')
                title_text = f"Line Plot for {can_id}\nStart: Byte {start_byte}, Bit {start_bit}, Length {total_bit_length}"
            elif plot_type == "Scatter Plot":
                self.ax.scatter(range(len(collected_data)), collected_data)
                title_text = f"Scatter Plot for {can_id}\nStart: Byte {start_byte}, Bit {start_bit}, Length {total_bit_length}"
            else:  # Bar Plot
                self.ax.bar(range(len(collected_data)), collected_data)
                title_text = f"Bar Plot for {can_id}\nStart: Byte {start_byte}, Bit {start_bit}, Length {total_bit_length}"
            
            self.ax.set_title(title_text)
            self.ax.set_xlabel("Message Index")
            self.ax.set_ylabel("Extracted Value")
            
            # Refresh the canvas
            self.canvas.draw()
        
        except Exception as e:
            # Show error message if extraction fails
            QMessageBox.critical(self, "Plot Error", 
                f"Could not extract data: {str(e)}\n"
                "Check your byte and bit selections.")

class CANMessageVisualizer(QMainWindow):
    def __init__(self, serial_port):
        super().__init__()
        self.setWindowTitle('CAN Message Analyzer')
        self.resize(1000, 700)

        # Data tracking
        self.can_data = {}

        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # Tabbed interface
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # Messages Tab
        messages_tab = QWidget()
        messages_layout = QVBoxLayout()
        messages_tab.setLayout(messages_layout)

        # Title
        title = QLabel('CAN Message Analyzer')
        title.setFont(QFont('Arial', 16))
        title.setAlignment(Qt.AlignCenter)
        messages_layout.addWidget(title)

        # Table to display CAN messages
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['CAN ID', 'Last Data', 'Length', 'Period (ms)'])
        messages_layout.addWidget(self.table)

        # Graph Tab
        self.graph_tab = GraphTab()
        
        # Add tabs
        self.tab_widget.addTab(messages_tab, "Messages")
        self.tab_widget.addTab(self.graph_tab, "Graph")

        # Setup message receiver
        self.receiver = CANMessageReceiver(serial_port)
        self.receiver.message_received.connect(self.update_can_data)

        # Connect to serial port
        if not self.receiver.connect():
            print("Failed to connect to serial port")
            sys.exit(1)

        # Add frame sending section
        self.add_send_frame_section(messages_layout)

        self.show()

    def add_send_frame_section(self, layout):
        # Form layout for sending CAN frames
        form_layout = QFormLayout()

        # Input fields
        self.id_input = QLineEdit()
        self.len_input = QLineEdit()
        self.data_input = QLineEdit()

        form_layout.addRow("CAN ID (hex):", self.id_input)
        form_layout.addRow("Length (1-8):", self.len_input)
        form_layout.addRow("Data (comma-separated):", self.data_input)

        # Send button
        send_button = QPushButton("Send Frame")
        send_button.clicked.connect(self.handle_send_frame)
        form_layout.addWidget(send_button)

        # Add the form to the main layout
        layout.addLayout(form_layout)

    def handle_send_frame(self):
        # Retrieve user input
        try:
            can_id = int(self.id_input.text(), 16)  # Convert hex ID to integer
            length = int(self.len_input.text())  # Convert length to integer
            data = [int(byte.strip(), 16) for byte in self.data_input.text().split(',')]  # Parse data bytes

            # Validate input
            if len(data) != length:
                print("Error: Length does not match number of data bytes.")
                return

            # Send the frame
            self.receiver.send_message(can_id, length, data)
        except ValueError:
            print("Error: Invalid input format. Check your ID, length, and data.")

    def update_can_data(self, message):
        # Convert ID to hex string for consistent key
        can_id = f"0x{message['ID']:X}"

        # Update or create entry for this CAN ID
        if can_id not in self.can_data:
            self.can_data[can_id] = {
                'last_data': message['Data'],
                'length': message['Length'],
                'period': message.get('Period', 0),
                'count': 1,
                'raw_messages': [message['Data']]
            }
        else:
            self.can_data[can_id].update({
                'last_data': message['Data'],
                'period': message.get('Period', 0),
                'count': self.can_data[can_id]['count'] + 1
            })
            # Store raw messages for graphing (limit to 500 messages)
            self.can_data[can_id].setdefault('raw_messages', []).append(message['Data'])
            if len(self.can_data[can_id]['raw_messages']) > 500:
                self.can_data[can_id]['raw_messages'].pop(0)

        # Update table
        self.update_table()

        # Update graph tab's CAN IDs
        self.graph_tab.update_can_ids(self.can_data)


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
    SERIAL_PORT = 'COM3'  # Adjust to match your serial port
    app = QApplication(sys.argv)
    visualizer = CANMessageVisualizer(SERIAL_PORT)
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
