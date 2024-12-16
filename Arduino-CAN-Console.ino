#include <Adafruit_MCP2515.h>
#include <Wire.h>

#define CS_PIN    9
#define INT_PIN   3

#define CAN_BAUDRATE (500000)
#define REPORT_INTERVAL 200 // Report every 200 ms
#define MAX_CAN_IDS 20      // Maximum number of unique CAN IDs to track

// Uncomment for more verbose debugging
#define VERBOSE_DEBUG

Adafruit_MCP2515 mcp(CS_PIN);

struct CanFrameStats {
  uint16_t id = 0;
  uint8_t data[8] = {0}; 
  unsigned long lastReceiveTime = 0;
  unsigned long receivePeriod = 0;
};

// Dynamic-like storage using fixed-size array
CanFrameStats canFrameStats[MAX_CAN_IDS];
uint8_t canFrameStatsCount = 0;
unsigned long lastReportTime = 0;

// Find or create a stats entry for a given CAN ID
CanFrameStats* findOrCreateCanStats(uint16_t canId) {
  // First, try to find an existing entry
  for (uint8_t i = 0; i < canFrameStatsCount; i++) {
    if (canFrameStats[i].id == canId) {
      return &canFrameStats[i];
    }
  }
  
  // If not found and we have space, create a new entry
  if (canFrameStatsCount < MAX_CAN_IDS) {
    CanFrameStats* newStats = &canFrameStats[canFrameStatsCount];
    newStats->id = canId;
    canFrameStatsCount++;
    return newStats;
  }
  
  // No space left, return NULL or the last entry
  return &canFrameStats[MAX_CAN_IDS - 1];
}

void setup() {
  
  // Initialize Serial with a longer timeout
  Serial.begin(115200);
  //Serial.setTimeout(2000);

  #ifdef VERBOSE_DEBUG
  Serial.println("Starting CAN Monitor");
  Serial.print("Initializing MCP2515 on CS Pin: ");
  Serial.println(CS_PIN);
  #endif

  // Perform extensive MCP2515 initialization checks
  pinMode(CS_PIN, OUTPUT);
  digitalWrite(CS_PIN, HIGH);

  // Additional delay to ensure stable initialization
  delay(100);

  // Detailed MCP2515 initialization
  if (!mcp.begin(CAN_BAUDRATE)) {
    Serial.println("ERROR: Failed to initialize MCP2515");
    Serial.println("Possible issues:");
    Serial.println("1. Check wiring");
    Serial.println("2. Verify CS pin connection");
    Serial.println("3. Ensure MCP2515 is properly seated");
    
    // Continuous error indication
    while(1) {
      Serial.println("Initialization FAILED");
      delay(1000);
    }
  }

  #ifdef VERBOSE_DEBUG
  Serial.println("MCP2515 Successfully Initialized");
  Serial.print("Baudrate: ");
  Serial.println(CAN_BAUDRATE);
  #endif

  
  // Configure interrupt pin
  pinMode(INT_PIN, INPUT);

  // Attach interrupt handler
  mcp.onReceive(INT_PIN, onReceive);

  Serial.println("CAN Monitor Ready");
}

void loop() {
  // Periodic reporting every 200 ms
  unsigned long currentTime = millis();
  if (currentTime - lastReportTime >= REPORT_INTERVAL) {
    Serial.println("here");
    //reportCanStats();
    lastReportTime = currentTime;
  }

  // Optional: Add a small delay to prevent tight looping
  delay(10);
}

void reportCanStats() {
  if (canFrameStatsCount == 0) {
    Serial.println("No CAN messages received yet");
    return;
  }

  for (uint8_t i = 0; i < canFrameStatsCount; i++) {
    CanFrameStats& stats = canFrameStats[i];

    Serial.print("CAN ID (0x");
    Serial.print(stats.id, HEX);
    Serial.print("): Data [");
    
    for (int j = 0; j < 8; j++) {
      Serial.print(stats.data[j], HEX);
      if (j < 7) Serial.print(" ");
    }
    Serial.print("] Period: ");
    Serial.print(stats.receivePeriod);
    Serial.println(" ms");
  }
}

void onReceive(int packetSize) {
  /*
  uint16_t currentCanId = mcp.packetId();
  unsigned long currentTime = millis();


  #ifdef VERBOSE_DEBUG
  Serial.print("Received CAN message. ID: 0x");
  Serial.print(currentCanId, HEX);
  Serial.print(" Packet Size: ");
  Serial.println(packetSize);
  #endif

  // Find or create stats for this CAN ID
  CanFrameStats* frameStats = findOrCreateCanStats(currentCanId);
  
  // Sanity check
  if (frameStats == NULL) return;

  // Calculate receive period if not the first receive
  if (frameStats->lastReceiveTime > 0) {
    frameStats->receivePeriod = currentTime - frameStats->lastReceiveTime;
  }

  // Update last receive time
  frameStats->lastReceiveTime = currentTime;

  // Clear previous data
  memset(frameStats->data, 0, sizeof(frameStats->data));

  // Read data into stats
  for (uint8_t idx = 0; mcp.available() && idx < 8; idx++) {
    frameStats->data[idx] = (uint8_t)mcp.read();
  }*/
}