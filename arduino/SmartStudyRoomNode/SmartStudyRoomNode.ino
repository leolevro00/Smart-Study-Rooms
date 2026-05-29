#include <WiFiS3.h>
#include <ArduinoHttpClient.h>
#include <DHT.h>

// Set 1 to test Firebase without physical sensors, 0 to read real sensors.
#define USE_SIMULATION 1

// Room configuration. Change these values on the second node.
const char* ROOM_ID = "room1";
const char* ROOM_NAME = "Aula 1";

// Wi-Fi configuration.
const char* WIFI_SSID = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

// Firebase Realtime Database host without "https://".
// Example: smart-study-rooms-default-rtdb.europe-west1.firebasedatabase.app
const char* FIREBASE_HOST = "YOUR_PROJECT-default-rtdb.europe-west1.firebasedatabase.app";

// If your test database rules are public, leave this empty.
// If you use a token/database secret, set it here and the code will append ?auth=...
const char* FIREBASE_AUTH = "";

// Sensor pins.
const int DHT_PIN = 2;
const int DHT_TYPE = DHT22; // Change to DHT11 if needed.
const int NOISE_PIN = A0;
const int PIR_PIN = 3;
const bool USE_PIR_SENSOR = true;

const unsigned long SEND_INTERVAL_MS = 10000;

DHT dht(DHT_PIN, DHT_TYPE);
WiFiSSLClient wifiClient;
HttpClient httpClient(wifiClient, FIREBASE_HOST, 443);

unsigned long lastSendMs = 0;

struct RoomReading {
  float temperature;
  float humidity;
  int noise;
  bool presence;
};

void setup() {
  Serial.begin(115200);
  while (!Serial) {
    ; // Wait for serial monitor on boards that need it.
  }

  pinMode(NOISE_PIN, INPUT);
  pinMode(PIR_PIN, INPUT);

  randomSeed(analogRead(A5));
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
    sendToFirebase(payload);
  }
}

void connectToWiFi() {
  Serial.print("Connecting to Wi-Fi: ");
  Serial.println(WIFI_SSID);

  while (WiFi.status() != WL_CONNECTED) {
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    delay(3000);
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
  json += ",";
  json += "\"lastUpdate\":{\".sv\":\"timestamp\"}";
  json += "}";

  return json;
}

void sendToFirebase(String payload) {
  String path = "/rooms/";
  path += ROOM_ID;
  path += ".json";

  if (String(FIREBASE_AUTH).length() > 0) {
    path += "?auth=";
    path += FIREBASE_AUTH;
  }

  Serial.print("PUT ");
  Serial.println(path);
  Serial.println(payload);

  httpClient.put(path, "application/json", payload);

  int statusCode = httpClient.responseStatusCode();
  String response = httpClient.responseBody();

  Serial.print("Firebase status: ");
  Serial.println(statusCode);
  Serial.print("Firebase response: ");
  Serial.println(response);

  httpClient.stop();
}
