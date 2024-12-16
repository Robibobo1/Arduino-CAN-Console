#include <Adafruit_MCP2515.h>

// Define the CS (Chip Select) pin for the MCP2515
#define CS_PIN 9

// Set the CAN bus baud rate
#define CAN_BAUDRATE 500000

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

  // Display the received CAN message
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
  Serial.println("Enter message in format: <ID>,<LEN>,<DATA1>,<DATA2>,...");

  String input = Serial.readStringUntil('\n');
  input.trim();

  // Parse the input
  int firstComma = input.indexOf(',');
  if (firstComma == -1) {
    Serial.println("Invalid format. Use <ID>,<LEN>,<DATA1>,<DATA2>,...");
    return;
  }

  String idStr = input.substring(0, firstComma);
  uint32_t id = strtoul(idStr.c_str(), NULL, 16);

  String rest = input.substring(firstComma + 1);
  int secondComma = rest.indexOf(',');
  if (secondComma == -1) {
    Serial.println("Invalid format. Missing data bytes.");
    return;
  }

  String lenStr = rest.substring(0, secondComma);
  uint8_t len = (uint8_t)lenStr.toInt();
  if (len > 8) {
    Serial.println("Length exceeds maximum of 8 bytes.");
    return;
  }

  String dataStr = rest.substring(secondComma + 1);
  uint8_t buf[8] = {0};

  int i = 0;
  int lastComma = -1;
  while (i < len) {
    int nextComma = dataStr.indexOf(',', lastComma + 1);
    String byteStr = nextComma == -1 ? dataStr.substring(lastComma + 1) : dataStr.substring(lastComma + 1, nextComma);
    buf[i] = (uint8_t)strtoul(byteStr.c_str(), NULL, 16);
    lastComma = nextComma;
    i++;
  }
  
  // Send the CAN message
  if (mcp.beginPacket(id)) {
    for (uint8_t i = 0; i < len; i++) {
      mcp.write(buf[i]);
    }
    mcp.endPacket();
  } else {
    Serial.println("Error starting CAN packet.");
  }
}
