#include <ESP8266WiFi.h>
#include <ArduinoJson.h>

extern "C" {
  #include "user_interface.h"
}

// =========================================================
// إعدادات البحث عن الواي فاي (Sniffer)
// =========================================================
#define MAX_DEVICES 50
#define TIMEOUT_MS 60000

struct SeenDevice {
  uint8_t mac[6];
  unsigned long lastSeen;
};

SeenDevice seenDevices[MAX_DEVICES];
int deviceCount = 0;

void sniffer_callback(uint8_t *buf, uint16_t len) {
  if (len < 28) return; 
  // استخراج الـ MAC Address الخاص بالجهاز الذي أرسل الإشارة
  uint8_t *srcMac = &buf[22];

  unsigned long now = millis();
  for (int i = 0; i < deviceCount; i++) {
    // نقارن أول 3 أجزاء من الماك للسرعة والتبسيط
    if (seenDevices[i].mac[0] == srcMac[0] && 
        seenDevices[i].mac[1] == srcMac[1] &&
        seenDevices[i].mac[2] == srcMac[2]) { 
      seenDevices[i].lastSeen = now;
      return;
    }
  }
  
  if (deviceCount < MAX_DEVICES) {
    for (int i = 0; i < 6; i++) seenDevices[deviceCount].mac[i] = srcMac[i];
    seenDevices[deviceCount].lastSeen = now;
    deviceCount++;
  }
}

int getActiveDeviceCount() {
  unsigned long now = millis(); 
  noInterrupts(); // حماية المتغيرات المشتركة من المقاطعات بشكل جذري
  int writeIndex = 0;
  // حذف الأجهزة القديمة التي اختفت منذ أكثر من دقيقة
  for (int i = 0; i < deviceCount; i++) {
    if (now - seenDevices[i].lastSeen <= TIMEOUT_MS) {
      if (writeIndex != i) seenDevices[writeIndex] = seenDevices[i];
      writeIndex++;
    }
  }
  deviceCount = writeIndex;
  interrupts(); // إعادة المقاطعات
  return deviceCount;
}

// =========================================================
// إعدادات البيزو (A0)
// =========================================================
const int piezoPin = A0; 
unsigned long lastStepTime = 0;
const int debounceDelay = 150; 
float cumulativeGenWh = 0.0; 
unsigned long lastPiezoSendTime = 0;
unsigned long lastWifiSendTime = 0;
// قناة الواي فاي لعمل مسح (Sniffing) - يمكن تغييرها
int wifiChannel = 1; 
unsigned long lastChannelSwitch = 0;

void setup() {
  Serial.begin(115200);
  delay(500);

  // تشغيل وضع الـ Sniffer للبحث عن الموبايلات
  wifi_set_opmode(STATION_MODE);
  wifi_set_channel(wifiChannel);
  wifi_promiscuous_enable(0);
  wifi_set_promiscuous_rx_cb(sniffer_callback);
  wifi_promiscuous_enable(1);

  lastPiezoSendTime = millis();
  lastWifiSendTime = millis();
}

void loop() {
  unsigned long currentMillis = millis();

  // 1. تقليب قنوات الواي فاي لتوسيع نطاق البحث عن الموبايلات
  if (currentMillis - lastChannelSwitch >= 2000) {
    lastChannelSwitch = currentMillis;
    wifi_promiscuous_enable(0); // إيقاف قبل تغيير القناة لمنع كراش الـ ESP
    wifiChannel++;
    if (wifiChannel > 11) wifiChannel = 1;
    wifi_set_channel(wifiChannel);
    wifi_promiscuous_enable(1);
  }

  // 2. إرسال البيانات بشكل دوري للـ Python
  if (currentMillis - lastPiezoSendTime >= 100) {
    lastPiezoSendTime = currentMillis;
    
    // قراءة البيزو من المنفذ التناظري
    int rawValue = analogRead(piezoPin);
    float voltage = 0.0;
    float current = 0.0;
    float generationW = 0.0;
    bool isStepped = false;
    
    // فلترة التشويش (Noise Filter):
    // الحساس المعلق بالهواء يقرأ قيماً عشوائية، لذا نتجاهل أي قراءة أقل من 150
    if (rawValue > 150) {
      voltage = (rawValue * 3.3) / 1023.0; 
      current = voltage / 1000.0;
      generationW = voltage * current;
      cumulativeGenWh += (generationW / 3600.0);
      
      if ((currentMillis - lastStepTime) > debounceDelay) {
        isStepped = true;
        lastStepTime = currentMillis; 
      }
    }

    StaticJsonDocument<512> doc;
    doc["day"] = 1;
    
    // إزالة الـ String لمنع تكسر الذاكرة (Heap Fragmentation) الذي يسبب الكراش
    char uptimeStr[16];
    sprintf(uptimeStr, "%lus", millis() / 1000);
    doc["system_uptime"] = uptimeStr;

    doc["voltage_v"] = voltage;            
    doc["current_a"] = current;            
    doc["generation_w"] = generationW;    
    doc["cumulative_gen_wh"] = cumulativeGenWh; 
    doc["storage_soc_pct"] = 50.0;        
    doc["power_source"] = "harvested";
    doc["footfall"] = isStepped ? 1 : 0;  
    
    // 3. دمج بيانات الواي فاي (عدد الأشخاص) كل 5 ثوانٍ فقط لتخفيف الضغط
    if (currentMillis - lastWifiSendTime >= 5000) {
      lastWifiSendTime = currentMillis;
      int count = getActiveDeviceCount();
      // تقدير عدد الأشخاص (مثلاً كل شخص يمتلك جهازين أو حساب تقريبي)
      int simulatedPeople = count > 0 ? (count / 2) + 1 : 0; 
      
      doc["people_count"] = simulatedPeople;
      doc["device_count_raw"] = count;
      // محاكاة رقم الـ CSI لأن الـ 8266 لا يدعمها حقيقياً
      doc["csi_variance"] = count > 0 ? 15.5 : 0.5; 
      doc["csi_people_estimate"] = simulatedPeople;
    }

    // إرسال كود الـ JSON بالكامل عبر كابل الـ USB
    serializeJson(doc, Serial);
    Serial.println();
  }

  // إعطاء فرصة للـ ESP8266 لمعالجة مهام الواي فاي الخلفية لمنع ريستارت الـ Watchdog
  delay(1);
}
