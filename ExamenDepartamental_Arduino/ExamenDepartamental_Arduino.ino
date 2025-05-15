#include <ArduinoJson.h>
#include <DHT.h>

#define DHTPIN 2
#define DHTTYPE DHT11
#define FAN_PIN 3
#define SEND_INTERVAL 2000  // 2 segundos

DHT dht(DHTPIN, DHTTYPE);
unsigned long lastSendTime = 0;
float minTemperature = 40.0;  // Valor por defecto

void setup() {
  Serial.begin(9600);
  while (!Serial);  // Esperar a que se inicie el puerto serial
  
  dht.begin();
  pinMode(FAN_PIN, OUTPUT);
  digitalWrite(FAN_PIN, LOW);
  
  Serial.println("Sistema de control de temperatura iniciado");
}

void loop() {
  unsigned long currentTime = millis();
  
  // Enviar datos cada 2 segundos
  if (currentTime - lastSendTime >= SEND_INTERVAL) {
    lastSendTime = currentTime;
    sendSensorData();
  }
  
  // Revisar si hay datos recibidos
  checkSerial();
}

void sendSensorData() {
  float humidity = dht.readHumidity();
  float temperature = dht.readTemperature();

  if (isnan(humidity) || isnan(temperature)) {
    Serial.println("{\"error\":\"Failed to read from DHT sensor\"}");
    return;
  }

  // Crear JSON de salida
  StaticJsonDocument<200> outputDoc;
  outputDoc["sensor"] = "DHT11";
  outputDoc["temperature"] = temperature;
  outputDoc["humidity"] = humidity;
  
  serializeJson(outputDoc, Serial);
  Serial.println();  // Nueva línea para separar mensajes

  // Controlar ventilador
  controlFan(temperature);
}

void checkSerial() {
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    input.trim();
    
    if (input.length() > 0) {
      processIncomingMessage(input);
    }
  }
}

void processIncomingMessage(String jsonInput) {
  StaticJsonDocument<200> inputDoc;
  DeserializationError error = deserializeJson(inputDoc, jsonInput);

  if (error) {
    Serial.print("{\"error\":\"");
    Serial.print(error.c_str());
    Serial.println("\"}");
    return;
  }

  // Procesar mensaje de configuración
  if (inputDoc.containsKey("min_temperature")) {
    minTemperature = inputDoc["min_temperature"];
    Serial.print("{\"status\":\"Config updated\",\"new_min_temp\":");
    Serial.print(minTemperature);
    Serial.println("}");
  }
}

void controlFan(float currentTemp) {
  if (currentTemp > minTemperature) {
    digitalWrite(FAN_PIN, HIGH);
  } else {
    digitalWrite(FAN_PIN, LOW);
  }
}