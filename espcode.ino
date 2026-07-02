#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <U8g2lib.h>
#include <Wire.h>

// ── USER SETTINGS / KULLANICI AYARLARI ──────────────────────────────────────────
const char* ssid     = "YOUR_WIFI_SSID";          // Your Wi-Fi Name / Wi-Fi Adınız
const char* password = "YOUR_WIFI_PASSWORD";      // Your Wi-Fi Password / Wi-Fi Şifreniz
const char* ip_address = "YOUR_COMPUTER_IP";      // Your PC's Local IP (e.g. 192.168.1.35) / Bilgisayarınızın Yerel IP Adresi

// Endpoint definitions / İstek adresleri
const String serverName = "http://" + String(ip_address) + ":5000/now-playing";
const String volumeUrl  = "http://" + String(ip_address) + ":5000/set-volume?vol=";
// ────────────────────────────────────────────────────────────────────────────────

#define POT_PIN 34 // Potentiometer middle pin (Analog ADC1) / Potansiyometre orta bacak pini

// SH1106 128x64 OLED Display configuration (SDA=21, SCL=22)
// SH1106 128x64 OLED Ekran Tanımlaması (SDA=21, SCL=22)
U8G2_SH1106_128X64_NONAME_1_HW_I2C u8g2(U8G2_R0, /* reset=*/ U8X8_PIN_NONE, /* clock=*/ 22, /* data=*/ 21);

// Global Spotify Variables / Global Spotify Değişkenleri
String trackName = "---";
String artistName = "---";
long progressMs = 0;
long durationMs = 1;
bool isPlaying = false;

// Interface and Animation Variables / Arayüz ve Animasyon Değişkenleri
int scrollPos = 0;
int textWidth = 0; 
bool shouldScroll = false; 
int lastVolume = 0; 

// Timers / Zamanlayıcılar
unsigned long lastFetchTime = 0;
unsigned long lastScrollTime = 0;
unsigned long lastPotTime = 0;

void setup() {
  Serial.begin(115200);
  u8g2.begin();
  
  pinMode(POT_PIN, INPUT); 
  
  // Connect to Wi-Fi / Wi-Fi Bağlantısını Başlatma
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWi-Fi Connected / Baglandi!");
}

void loop() {
  unsigned long currentMillis = millis();

  // 1. Potentiometer Read & Volume Update Loop (Every 200ms)
  // 1. Potansiyometre Okuma ve Ses Gönderme Döngüsü (Her 200ms'de bir)
  if (currentMillis - lastPotTime >= 200) {
    lastPotTime = currentMillis;
    
    int potValue = analogRead(POT_PIN);
    // Map 12-bit ADC (0-4095) to percentage (0-100)
    // 12-bit ADC değerini (0-4095) yüzdeye (%0-100) haritalıyoruz
    int currentVolume = map(potValue, 0, 4095, 0, 100); 
    
    // Send request only if change is greater than 2% to avoid noise jitter
    // Parazitleri engellemek için sadece %2 ve üzeri değişimlerde istek at
    if (abs(currentVolume - lastVolume) >= 2) { 
      lastVolume = currentVolume;
      
      if (WiFi.status() == WL_CONNECTED) {
        HTTPClient http;
        String fullVolUrl = volumeUrl + String(currentVolume);
        
        http.begin(fullVolUrl);
        int httpCode = http.GET(); 
        http.end();
        
        Serial.print("PC Volume Set: %");
        Serial.println(currentVolume);
      }
    }
  }

  // 2. Fetch Spotify Data from Python Bridge (Every 1500ms)
  // 2. 1.5 saniyede bir Python Flask Köprüsünden verileri çek
  if (currentMillis - lastFetchTime >= 1500) {
    lastFetchTime = currentMillis;
    
    if (WiFi.status() == WL_CONNECTED) {
      HTTPClient http;
      http.begin(serverName);
      http.setUserAgent("ESP32");
      
      int httpCode = http.GET();
      
      if (httpCode == 200) {
        String payload = http.getString();
        JsonDocument doc; 
        DeserializationError error = deserializeJson(doc, payload);
        
        if (!error) {
          String newTrack = doc["track"].as<String>();
          artistName = doc["artist"].as<String>();
          progressMs = doc["progress"].as<long>();
          durationMs = doc["duration"].as<long>();
          isPlaying = doc["is_playing"].as<bool>();
          
          // If song changed, calculate text width for scrolling
          // Eğer yeni bir şarkıya geçildiyse kaydırma kontrolü için genişlik hesapla
          if (newTrack != trackName) {
            trackName = newTrack;
            u8g2.setFont(u8g2_font_7x14_tr);
            textWidth = u8g2.getUTF8Width(trackName.c_str());
            
            // Scroll only if text is wider than screen (128px), otherwise center it
            // Yazı ekrandan (128px) büyükse kaydır, sığıyorsa ortala
            if (textWidth > 128) {
              shouldScroll = true;
              scrollPos = 10; 
            } else {
              shouldScroll = false;
              scrollPos = (128 - textWidth) / 2; 
            }
          }
        }
      }
      http.end();
    }
  }

  // Fluid progress bar estimation / Akıcı ilerleme çubuğu simülasyonu
  if (isPlaying && progressMs < durationMs) {
    progressMs += (currentMillis - lastScrollTime); 
  }

  // 3. Screen Refresh & Scroll Animation Loop (Every 30ms)
  // 3. Ekran Güncelleme ve Kaydırma Animasyonu Döngüsü (Her 30ms'de bir)
  if (currentMillis - lastScrollTime >= 30) {
    lastScrollTime = currentMillis;
    
    if (shouldScroll && isPlaying) {
      scrollPos--;
      if (scrollPos < -textWidth) {
        scrollPos = 128; 
      }
    }
    
    u8g2.firstPage();
    do {
      // Header Frame / Üst Arayüz Çerçevesi
      u8g2.drawFrame(0, 0, 128, 13);
      u8g2.setFont(u8g2_font_5x7_tr);
      
      if (isPlaying) {
        u8g2.drawStr(4, 9, ">> CYBERPUNK SPOTIFY");
        u8g2.setFont(u8g2_font_7x14_tr);
        u8g2.drawStr(scrollPos, 32, trackName.c_str());
      } else {
        u8g2.drawStr(4, 9, "|| PAUSED");
        u8g2.setFont(u8g2_font_7x14_tr);
        int pausedWidth = u8g2.getUTF8Width("Paused...");
        u8g2.drawStr((128 - pausedWidth) / 2, 32, "Paused...");
      }

      // Artist Info & Current Volume / Sanatçı ve Güncel Ses Seviyesi
      u8g2.setFont(u8g2_font_6x12_tr);
      String displayStr = "@ " + artistName + " | V:" + String(lastVolume) + "%";
      int strWidth = u8g2.getUTF8Width(displayStr.c_str());
      int strX = (strWidth > 128) ? 0 : (128 - strWidth) / 2;
      u8g2.drawStr(strX, 48, displayStr.c_str());

      // Progress Bar Frame & Box / Alt Bar: İlerleme Çubuğu Çizimi
      u8g2.drawFrame(0, 56, 128, 6);
      if (durationMs > 0) {
        int barWidth = (progressMs * 126) / durationMs;
        if (barWidth > 126) barWidth = 126;
        if (barWidth < 0) barWidth = 0;
        u8g2.drawBox(1, 57, barWidth, 4);
      }
    } while (u8g2.nextPage());
  }
}