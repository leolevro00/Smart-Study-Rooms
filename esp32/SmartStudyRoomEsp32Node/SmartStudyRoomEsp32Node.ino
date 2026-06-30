#include <WiFi.h>
#include <HTTPClient.h>
#include <DHT.h>

// Set 1 to test the bridge without physical sensors, 0 to read real sensors.
#define USE_SIMULATION 1

// Room configuration. Change these values on the second Wi-Fi node if needed.
const char* ROOM_ID = "room1";
const char* ROOM_NAME = "Aula 1";

// Wi-Fi configuration.
const char* WIFI_SSID = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

// Local bridge configuration.
// Use the IP address of the PC running bridge/bridge_server.py.
const char* BRIDGE_HOST = "192.168.1.50";
const int BRIDGE_PORT = 3000;

// Sensor pins. Adjust according to your wiring.
const int DHT_PIN = 4;
const int DHT_TYPE = DHT22; // Change to DHT11 if needed.
const int NOISE_PIN = 34;
const int PIR_PIN = 27;
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
  delay(1000);

  pinMode(NOISE_PIN, INPUT);
  pinMode(PIR_PIN, INPUT);

  randomSeed(analogRead(NOISE_PIN));
  dht.begin();

  connectToWiFi();
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    connectToWiFi();
  }

  unsigned long now = millis();
  if (now - lastSendMs >= SEND_INTERVAL_MS || lastSendMs == 0) {
    lastSendMs = now;

    RoomReading reading = readRoom();
    String payload = buildJsonPayload(reading);
    sendToBridge(payload);
  }
}

void connectToWiFi() {
  Serial.print("Connecting to Wi-Fi: ");
  Serial.println(WIFI_SSID);

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();
  Serial.print("Connected. IP address: ");
  Serial.println(WiFi.localIP());
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
  reading.noise = map(rawNoise, 0, 4095, 0, 100);
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

void sendToBridge(String payload) {
  String url = "http://";
  url += BRIDGE_HOST;
  url += ":";
  url += String(BRIDGE_PORT);
  url += "/rooms/";
  url += ROOM_ID;

  Serial.print("POST bridge ");
  Serial.println(url);
  Serial.println(payload);

  HTTPClient http;
  http.begin(url);
  http.addHeader("Content-Type", "application/json");

  int statusCode = http.POST(payload);
  String response = http.getString();

  Serial.print("Bridge status: ");
  Serial.println(statusCode);
  Serial.print("Bridge response: ");
  Serial.println(response);

  http.end();
}
