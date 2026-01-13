// ========================================
// SMART DOOR LOCK – ARDUINO DEMO
// ========================================

#define RELAY_PIN 7
#define UNLOCK_TIME 5000  // milliseconds (5 seconds)

String command = "";

void setup() {
  Serial.begin(9600);
  pinMode(RELAY_PIN, OUTPUT);

  digitalWrite(RELAY_PIN, LOW);  // Lock engaged
  Serial.println("Arduino ready");
}

void loop() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') {
      command.trim();
      handleCommand(command);
      command = "";
    } else {
      command += c;
    }
  }
}

void handleCommand(String cmd) {
  if (cmd == "UNLOCK") {
    unlockDoor();
  }
}

void unlockDoor() {
  Serial.println("UNLOCKING DOOR");
  digitalWrite(RELAY_PIN, HIGH);   // Unlock
  delay(UNLOCK_TIME);
  digitalWrite(RELAY_PIN, LOW);    // Relock
  Serial.println("DOOR LOCKED");
}
