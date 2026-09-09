#include <ArduinoJson.h>

const int piezoPin = A0; 
const float loadResistance = 1000.0; 

unsigned long lastStepTime = 0;
const int debounceDelay = 150; 
float cumulativeGenWh = 0.0; 

void setup() {
  Serial.begin(115200);
}

void loop() {
  int rawValue = analogRead(piezoPin);
  float voltage = (rawValue * 1.0) / 1023.0; 
  float current = voltage / loadResistance;
  float generationW = voltage * current;
  cumulativeGenWh += (generationW / 3600.0);

  // الشرط المباشر: لو الجهد عدى 0.04 فولت (أي قيمة محسوسة)، اعتبرها ضغطة حقيقية
  bool isStepped = false;
  unsigned long currentTime = millis();
  
  if (voltage > 0.04 && (currentTime - lastStepTime) > debounceDelay) {
    isStepped = true;
    lastStepTime = currentTime; 
  }

  StaticJsonDocument<1024> doc;
  doc["day"] = 1;
  doc["sim_time"] = "14:30";
  doc["system_uptime"] = String(millis() / 1000) + "s";
  doc["voltage_v"] = voltage;            
  doc["current_a"] = current;            
  doc["generation_w"] = generationW;    
  doc["cumulative_gen_wh"] = cumulativeGenWh; 
  doc["storage_soc_pct"] = 50.0;        
  doc["power_source"] = "harvested";
  
  // التأكد من إرسال القيمة الحقيقية صراحة
  doc["footfall"] = isStepped ? 1 : 0;  
  
  JsonObject ai_status = doc.createNestedObject("ai_status");
  ai_status["forecast_model"] = "Standby";
  ai_status["anomaly_model"] = "Standby";

  JsonArray loads = doc.createNestedArray("loads");
  JsonObject load1 = loads.createNestedObject();
  load1["name"] = "Piezo Sensor 1";
  load1["state"] = isStepped ? "ACTIVE" : "IDLE";

  JsonArray tiles = doc.createNestedArray("tiles");
  JsonObject tile1 = tiles.createNestedObject();
  tile1["id"] = 1;
  tile1["efficiency_pct"] = 99.0;
  tile1["stepped_on"] = isStepped;         
  tile1["total_steps"] = isStepped ? 1 : 0; 

  serializeJson(doc, Serial);
  Serial.println();

  delay(100); 
}