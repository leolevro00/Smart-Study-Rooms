#include <DHT.h>

// Set 1 to test the serial bridge without physical sensors, 0 to read real sensors.
#define USE_SIMULATION 1

// Room configuration for the Arduino UNO serial node.
const char* ROOM_NAME = "Aula 2";

// Sensor pins. Adjust according to your wiring.
const int DHT_PIN = 2;
const int DHT_TYPE = DHT22; // Change to DHT11 if needed.
const int NOISE_PIN = A0;
const int PIR_PIN = 3;
const bool USE_PIR_SENSOR = true;

const unsigned long SEND_INTERVAL_MS = 10000;

DHT dht(DHT_PIN, DHT_TYPE);
unsigned long lastSendMs = 0;

struct RoomReading {
  float temperature;
  float humidity;
  int noise;
  bool presence;
};

void setup() {
  Serial.begin(115200);

  pinMode(NOISE_PIN, INPUT);
  pinMode(PIR_PIN, INPUT);

  randomSeed(analogRead(A5));
  dht.begin();
}

void loop() {
  unsigned long now = millis();
  if (now - lastSendMs >= SEND_INTERVAL_MS || lastSendMs == 0) {
    lastSendMs = now;

    RoomReading reading = readRoom();
    Serial.println(buildJsonPayload(reading));
  }
}

RoomReading readRoom() {
#if USE_SIMULATION
  return simulateReading();
#else
  return readSensors();
#endif
}

RoomReading readSensors() {
  RoomReading reading;

  reading.temperature = dht.readTemperature();
  reading.humidity = dht.readHumidity();

  if (isnan(reading.temperature)) {
    reading.temperature = -100.0;
  }
  if (isnan(reading.humidity)) {
    reading.humidity = -1.0;
  }

  int rawNoise = analogRead(NOISE_PIN);
  reading.noise = map(rawNoise, 0, 1023, 0, 100);
  reading.noise = constrain(reading.noise, 0, 100);

  if (USE_PIR_SENSOR) {
    reading.presence = digitalRead(PIR_PIN) == HIGH;
  } else {
    reading.presence = false;
  }

  return reading;
}

RoomReading simulateReading() {
  RoomReading reading;

  reading.temperature = random(190, 271) / 10.0;
  reading.humidity = random(350, 701) / 10.0;
  reading.noise = random(20, 81);
  reading.presence = random(0, 2) == 1;

  return reading;
}

String buildJsonPayload(RoomReading reading) {
  String json = "{";
  json += "\"name\":\"";
  json += ROOM_NAME;
  json += "\",";
  json += "\"temperature\":";
  json += String(reading.temperature, 1);
  json += ",";
  json += "\"humidity\":";
  json += String(reading.humidity, 1);
  json += ",";
  json += "\"noise\":";
  json += String(reading.noise);
  json += ",";
  json += "\"presence\":";
  json += (reading.presence ? "true" : "false");
  json += "}";

  return json;
}
