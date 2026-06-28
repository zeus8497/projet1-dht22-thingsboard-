// Projet 1 — ESP32 + DHT22 + LED → ThingsBoard (MQTT)

#include <WiFi.h>
#include <PubSubClient.h>
#include <DHTesp.h>
#include <ArduinoJson.h>

#define MQTT_MAX_PACKET_SIZE 512

#if __has_include("secrets.h")
#include "secrets.h"
#else
#define TB_HOST "eu.thingsboard.cloud"
#define TB_PORT 1883
#define TB_ACCESS_TOKEN "REMPLACER_PAR_VOTRE_TOKEN"
#define DEVICE_LATITUDE 14.6928
#define DEVICE_LONGITUDE -17.4467
#endif

const char* WIFI_SSID = "Wokwi-GUEST";
const char* WIFI_PASS = "";

const int DHT_PIN = 18;
const int LED_PIN = 25;
const unsigned long TELEMETRY_INTERVAL_MS = 10000;

DHTesp dhtSensor;
WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);

unsigned long lastTelemetry = 0;
bool attributesSent = false;

void printSensorLine(float humidity, float temperature) {
  Serial.printf("#%.0f, %.1f\n", humidity, temperature);
}

void connectWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  Serial.print("Wi-Fi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println(" OK");
}

void connectMQTT() {
  mqttClient.setServer(TB_HOST, TB_PORT);
  while (!mqttClient.connected()) {
    Serial.print("MQTT");
    if (mqttClient.connect("esp32-dht22", TB_ACCESS_TOKEN, nullptr)) {
      Serial.println(" OK");
    } else {
      Serial.printf(" rc=%d\n", mqttClient.state());
      delay(5000);
    }
  }
}

void sendClientAttributes() {
  StaticJsonDocument<128> doc;
  doc["latitude"] = DEVICE_LATITUDE;
  doc["longitude"] = DEVICE_LONGITUDE;
  doc["city"] = "Dakar";
  char buffer[128];
  size_t len = serializeJson(doc, buffer);
  mqttClient.publish("v1/devices/me/attributes", buffer, len);
  attributesSent = true;
}

void publishTelemetry(float humidity, float temperature) {
  StaticJsonDocument<192> doc;
  doc["humidity"] = humidity;
  doc["temperature"] = temperature;
  doc["latitude"] = DEVICE_LATITUDE;
  doc["longitude"] = DEVICE_LONGITUDE;
  doc["ledAlert"] = (temperature >= 40.0);

  char buffer[192];
  size_t len = serializeJson(doc, buffer);
  mqttClient.publish("v1/devices/me/telemetry", buffer, len);
  printSensorLine(humidity, temperature);
}

void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);
  dhtSensor.setup(DHT_PIN, DHTesp::DHT22);
  connectWiFi();
  connectMQTT();
  sendClientAttributes();
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    connectWiFi();
  }
  if (!mqttClient.connected()) {
    connectMQTT();
    attributesSent = false;
  }
  mqttClient.loop();

  if (!attributesSent) {
    sendClientAttributes();
  }

  unsigned long now = millis();
  if (now - lastTelemetry < TELEMETRY_INTERVAL_MS) {
    return;
  }
  lastTelemetry = now;

  TempAndHumidity data = dhtSensor.getTempAndHumidity();
  if (isnan(data.temperature) || isnan(data.humidity)) {
    Serial.println("DHT22: erreur lecture");
    return;
  }

  digitalWrite(LED_PIN, data.temperature >= 40.0 ? HIGH : LOW);
  publishTelemetry(data.humidity, data.temperature);
}
