#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <ArduinoHttpClient.h>

// Set 1 to test Firebase without physical sensors, 0 to read real sensors.
#define USE_SIMULATION 0

// Room configuration
const char* ROOM_ID = "room1";
const char* ROOM_NAME = "Aula 1";

// WiFi
const char* WIFI_SSID = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

// Firebase host without https://
const char* FIREBASE_HOST =
    "smartstudyrooms-ab798-default-rtdb.europe-west1.firebasedatabase.app";

// Leave empty if database rules are public
const char* FIREBASE_AUTH = "";

// TMP36 pin
const int TMP36_PIN = 34;

const unsigned long SEND_INTERVAL_MS = 10000;

WiFiClientSecure wifiClient;
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

  randomSeed(micros());

  connectToWiFi();

  // For Firebase HTTPS
  wifiClient.setInsecure();
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

  Serial.print("Connecting to WiFi: ");
  Serial.println(WIFI_SSID);

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }

  Serial.println();
  Serial.println("WiFi connected");
  Serial.print("IP: ");
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

  // ESP32 ADC
  int adcValue = analogRead(TMP36_PIN);

  float voltage = adcValue * (3.3 / 4095.0);

  // TMP36 formula
  reading.temperature = (voltage - 0.5) * 100.0;

  // Placeholder values until more sensors are added
  reading.humidity = 0.0;
  reading.noise = 0;
  reading.presence = false;

  return reading;
}

RoomReading simulateReading() {

  RoomReading reading;

  reading.temperature = random(190, 271) / 10.0;
  reading.humidity = random(350, 701) / 10.0;
  reading.noise = random(20, 81);
  reading.presence = random(0, 2);

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

  if (strlen(FIREBASE_AUTH) > 0) {
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
