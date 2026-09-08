#include <DHT.h>

// Set 1 to test the serial bridge without physical sensors, 0 to read real sensors.
#define USE_SIMULATION 0

// Set 1 only while calibrating the noise sensor. It adds noisePeak to the serial JSON.
#define NOISE_DEBUG 0

// Room configuration for the Arduino UNO serial node.
const char* ROOM_NAME = "Aula 2";

// Sensor pins. Adjust according to your wiring.
const int DHT_PIN = 2;
const int DHT_TYPE = DHT22; // Change to DHT11 if needed.
const int NOISE_PIN = A1; // Connect the analog output AO of the noise sensor here.
const int GREEN_LED_PIN = 12; // LED for cooling
const int RED_LED_PIN = 13; // LED for heating
const int YELLOW_LED_PIN = 11; // LED on when this is the recommended room


// Noise calibration. The sketch samples the microphone for a short window and
// converts the peak-to-peak variation to a 0..100 level.
// KY-037/KY-038 analog signals can be very small. These values intentionally use maximum sensitivity for study rooms.
const unsigned long NOISE_SAMPLE_WINDOW_MS = 80;
const int NOISE_RAW_MIN = 0;
const int NOISE_RAW_MAX = 200;
const float HEATING_THRESHOLD = 25.0; // upper temperature threshold: simulate cooling
const float COOLING_THRESHOLD = 20.0; // lower temperature threshold: simulate heating
const unsigned long SEND_INTERVAL_MS = 10000;

DHT dht(DHT_PIN, DHT_TYPE);
unsigned long lastSendMs = 0;
int maxNoiseSinceLastSend = 0;
int maxNoisePeakSinceLastSend = 0;

struct NoiseReading {
  int level;
  int peakToPeak;
};

struct RoomReading {
  float temperature;
  float humidity;
  int noise;
  int noisePeak;
};

void setup() {
  Serial.begin(115200);

  pinMode(NOISE_PIN, INPUT);
  pinMode(GREEN_LED_PIN, OUTPUT);
  pinMode(RED_LED_PIN, OUTPUT);
  pinMode(YELLOW_LED_PIN, OUTPUT);
  digitalWrite(GREEN_LED_PIN, LOW);
  digitalWrite(RED_LED_PIN, LOW);
  digitalWrite(YELLOW_LED_PIN, LOW);
 

  randomSeed(analogRead(A5));
  dht.begin();
}

void loop() {
  handleSerialCommands();

#if !USE_SIMULATION
  NoiseReading currentNoise = readNoiseLevel();
  if (currentNoise.level > maxNoiseSinceLastSend) {
    maxNoiseSinceLastSend = currentNoise.level;
  }
  if (currentNoise.peakToPeak > maxNoisePeakSinceLastSend) {
    maxNoisePeakSinceLastSend = currentNoise.peakToPeak;
  }
#endif

  unsigned long now = millis();
  if (now - lastSendMs >= SEND_INTERVAL_MS || lastSendMs == 0) {
    lastSendMs = now;

    RoomReading reading = readRoom(maxNoiseSinceLastSend, maxNoisePeakSinceLastSend);
    updateTemperatureActuators(reading.temperature);
    Serial.println(buildJsonPayload(reading));
    maxNoiseSinceLastSend = 0;
    maxNoisePeakSinceLastSend = 0;
  }
}

void handleSerialCommands() {
  while (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();

    if (command == "BEST_LED_ON") {
      digitalWrite(YELLOW_LED_PIN, HIGH);
    } else if (command == "BEST_LED_OFF") {
      digitalWrite(YELLOW_LED_PIN, LOW);
    }
  }
}

void updateTemperatureActuators(float temperature) {
  if (temperature > HEATING_THRESHOLD) {
    digitalWrite(GREEN_LED_PIN, HIGH);
    digitalWrite(RED_LED_PIN, LOW);
  } else if (temperature < COOLING_THRESHOLD) {
    digitalWrite(GREEN_LED_PIN, LOW);
    digitalWrite(RED_LED_PIN, HIGH);
  } else {
    digitalWrite(GREEN_LED_PIN, LOW);
    digitalWrite(RED_LED_PIN, LOW);
  }
}

RoomReading readRoom(int noiseLevel, int noisePeak) {
#if USE_SIMULATION
  return simulateReading();
#else
  return readSensors(noiseLevel, noisePeak);
#endif
}

RoomReading readSensors(int noiseLevel, int noisePeak) {
  RoomReading reading;

  reading.temperature = dht.readTemperature();
  reading.humidity = dht.readHumidity();

  if (isnan(reading.temperature)) {
    reading.temperature = -100.0;
  }
  if (isnan(reading.humidity)) {
    reading.humidity = -1.0;
  }

  reading.noise = noiseLevel;
  reading.noisePeak = noisePeak;

  return reading;
}

NoiseReading readNoiseLevel() {
  int signalMin = 1023;
  int signalMax = 0;
  unsigned long startMs = millis();

  while (millis() - startMs < NOISE_SAMPLE_WINDOW_MS) {
    int sample = analogRead(NOISE_PIN);
    if (sample < signalMin) {
      signalMin = sample;
    }
    if (sample > signalMax) {
      signalMax = sample;
    }
  }

  int peakToPeak = signalMax - signalMin;
  int level = map(peakToPeak, NOISE_RAW_MIN, NOISE_RAW_MAX, 0, 100);

  NoiseReading reading;
  reading.level = constrain(level, 0, 100);
  reading.peakToPeak = peakToPeak;
  return reading;
}

RoomReading simulateReading() {
  RoomReading reading;

  reading.temperature = random(190, 271) / 10.0;
  reading.humidity = random(350, 701) / 10.0;
  reading.noise = random(20, 81);
  reading.noisePeak = reading.noise;

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
#if NOISE_DEBUG
  json += ",";
  json += "\"noisePeak\":";
  json += String(reading.noisePeak);
#endif
  json += "}";

  return json;
}

