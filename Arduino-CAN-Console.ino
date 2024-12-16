#include <Adafruit_MCP2515.h>

// Define the CS (Chip Select) pin for the MCP2515
#define CS_PIN 9

// Set the CAN bus baud rate
#define CAN_BAUDRATE 250000
#define SERIAL_BAUDRATE 250000

// Create an instance of the MCP2515 controller
Adafruit_MCP2515 mcp(CS_PIN);

void setup() {
  Serial.begin(250000);
  while (!Serial) delay(10);

  Serial.println("Adafruit MCP2515 CAN Console Example");

  // Initialize the MCP2515 controller
  if (mcp.begin(CAN_BAUDRATE) != 1) {
    Serial.println("Error initializing MCP2515. Check wiring.");
    while (1) delay(10);
  }
  Serial.println("MCP2515 initialized successfully.");
}

void loop() {
  // Check if a CAN message is available
  if (mcp.parsePacket()) {
    receiveCANMessage();
  }

  // Check for user input to send a message
  if (Serial.available()) {
    sendCANMessage();
  }
}

void receiveCANMessage() {
  uint32_t id = mcp.packetId();
  bool isExtended = mcp.packetExtended();
  bool isRemote = mcp.packetRtr();
  uint8_t len = mcp.available();
  uint8_t data[8];

  for (uint8_t i = 0; i < len; i++) {
    data[i] = mcp.read();
  }

  // Send the message Data in JSON
  Serial.print("{\"ID\":");
  Serial.print(id);

  Serial.print(",\"Length\":");
  Serial.print(len);

  Serial.print(",\"Data\":[");
  for (uint8_t i = 0; i < len; i++) {
    if(i != 0) Serial.print(",");
    Serial.print(data[i]);
  }
  Serial.println("]}");
}


void sendCANMessage() {
  // Prompt the user to enter a CAN message in the format: <ID>,<LEN>,<DATA1>,<DATA2>,...
  Serial.println("Enter message in format: <ID>,<LEN>,<DATA1>,<DATA2>,...");

  // Read the user input from the serial port until a newline character
  String input = Serial.readStringUntil('\n');
  input.trim(); // Remove any leading or trailing whitespace

  // Parse the input to extract the ID
  int firstComma = input.indexOf(','); // Find the position of the first comma
  if (firstComma == -1) { // If no comma is found, the format is invalid
    Serial.println("Invalid format. Use <ID>,<LEN>,<DATA1>,<DATA2>,...");
    return; // Exit the function
  }

  // Extract the ID part of the input (substring before the first comma)
  String idStr = input.substring(0, firstComma);
  uint32_t id = strtoul(idStr.c_str(), NULL, 16); // Convert the ID from a hex string to an unsigned integer

  // Extract the rest of the input after the ID
  String rest = input.substring(firstComma + 1);

  // Parse the length of the CAN message
  int secondComma = rest.indexOf(','); // Find the position of the second comma
  if (secondComma == -1) { // If no second comma is found, data bytes are missing
    Serial.println("Invalid format. Missing data bytes.");
    return; // Exit the function
  }

  // Extract the length part of the input (substring before the second comma)
  String lenStr = rest.substring(0, secondComma);
  uint8_t len = (uint8_t)lenStr.toInt(); // Convert the length from a string to an integer
  if (len > 8) { // Check if the length exceeds the maximum allowed (8 bytes for CAN)
    Serial.println("Length exceeds maximum of 8 bytes.");
    return; // Exit the function
  }

  // Extract the data bytes part of the input (substring after the second comma)
  String dataStr = rest.substring(secondComma + 1);
  uint8_t buf[8] = {0}; // Initialize a buffer to store up to 8 data bytes

  // Parse each data byte from the string and store it in the buffer
  int i = 0;
  int lastComma = -1;
  while (i < len) { // Loop until all bytes are parsed or the specified length is reached
    int nextComma = dataStr.indexOf(',', lastComma + 1); // Find the position of the next comma
    // Extract the byte as a substring between commas, or to the end of the string if no comma is found
    String byteStr = nextComma == -1 ? dataStr.substring(lastComma + 1) : dataStr.substring(lastComma + 1, nextComma);
    buf[i] = (uint8_t)strtoul(byteStr.c_str(), NULL, 16); // Convert the byte from a hex string to an integer
    lastComma = nextComma; // Update the last comma position
    i++; // Move to the next byte
  }

  // Attempt to send the CAN message using the MCP CAN library
  if (mcp.beginPacket(id)) { // Start a new CAN packet with the specified ID
    for (uint8_t i = 0; i < len; i++) { // Write each byte from the buffer into the packet
      mcp.write(buf[i]);
    }
    mcp.endPacket(); // Finalize and send the packet
  } else { // If starting the CAN packet fails, print an error message
    Serial.println("Error starting CAN packet.");
  }
}

