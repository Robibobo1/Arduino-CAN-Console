# CAN Message Analyzer and Sender

This repository contains two main components for working with CAN messages:

1. A **Python GUI** for analyzing and sending CAN messages.
2. An **Arduino sketch** for receiving and sending CAN frames using the MCP2515 CAN controller.

---

## Features

### Python GUI Application
- **Receive CAN Messages**:
  - Displays CAN ID, data bytes, length, and message period in milliseconds.
  - Dynamically updates the GUI as messages arrive.

- **Send CAN Frames**:
  - User-friendly input form to send CAN messages via the connected hardware.
  - Validates input fields for proper format (ID, length, and data bytes).

- **Period Calculation**:
  - Tracks the time difference between consecutive messages for the same CAN ID.
  - Displays the period in milliseconds, rounded to 2 decimal places.

### Arduino Sketch
- Interfaces with an MCP2515 CAN controller to send and receive CAN messages.
- CAN messages are sent/received in JSON format for easy integration with the Python application.
- Supports serial input for sending CAN frames.

---

## Python Application

### Requirements
Install the dependencies using:
```bash
pip install pyserial pyqt5 pandas numpy
```

### Running the Application
1. Update the `SERIAL_PORT` variable in `main()` to match your hardware port.
2. Run the Python application:
   ```bash
   python can_message_analyzer.py
   ```

---

## Arduino Sketch

### Overview
The Arduino sketch works with an MCP2515 CAN controller and provides two primary functionalities:

1. **Receive CAN Messages**:
   - Reads CAN frames and sends them to the serial port in JSON format.

2. **Send CAN Messages**:
   - Allows the user to input a CAN frame in the format `<ID>,<LEN>,<DATA1>,<DATA2>,...`.
   - Parses the input, validates the data, and sends the frame using the MCP2515.

---

## Compatibility
- **Hardware**:
  - MCP2515 CAN Controller
  - Any Arduino-compatible board (e.g., Arduino Uno, Mega)
- **Software**:
  - Python 3.x
  - Arduino IDE

---

## Future Improvements
- Add filters for specific CAN IDs in the Python application.
- Provide real-time graphing of specific data fields from CAN messages.
