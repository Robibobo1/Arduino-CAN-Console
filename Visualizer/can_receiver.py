import json
import time
import serial
import threading
from PyQt5.QtCore import pyqtSignal, QObject

class CANMessageReceiver(QObject):
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
                        current_time = time.time()
                        can_id = message['ID']
                        period = 0

                        if can_id in self.last_receive_times:
                            period = (current_time - self.last_receive_times[can_id]) * 1000

                        self.last_receive_times[can_id] = current_time

                        if can_id not in self.recent_periods:
                            self.recent_periods[can_id] = []

                        self.recent_periods[can_id].append(period)
                        if len(self.recent_periods[can_id]) > 10:
                            self.recent_periods[can_id].pop(0)

                        average_period = sum(self.recent_periods[can_id]) / len(self.recent_periods[can_id])
                        message['Period'] = round(average_period, 2)

                        self.message_received.emit(message)
                    except json.JSONDecodeError:
                        pass
            except Exception as e:
                print(f"Error receiving message: {e}")
                self.running = False

    def send_message(self, can_id, length, data):
        if not self.serial_connection or not self.running:
            print("Error: Serial connection is not active.")
            return

        if length > 8 or length < 1:
            print("Error: Length must be between 1 and 8 bytes.")
            return

        try:
            out_string = f"{can_id},{length},{','.join([str(d) for d in data])}"
            self.serial_connection.write((out_string + '\n').encode('utf-8'))
            print(f"Sent frame: {out_string}")
        except Exception as e:
            print(f"Error sending message: {e}")

    def stop(self):
        self.running = False
        if self.serial_connection:
            self.serial_connection.close()
