# ⚡ Cyberpunk Spotify Display & PC Volume Mixer

An ESP32 and Python Flask-driven open-source desktop hardware monitor. It displays real-time Spotify playback data (Track name, Artist, Progress Bar) on an OLED screen with a custom dynamic text-scrolling engine and provides a physical knob (potentiometer) to control Windows Master Volume directly via local networks.

---

## 🚀 Features

* **Dynamic Text Scrolling:** Detects text boundaries dynamically using getUTF8Width. If the track title fits the screen, it centers automatically; if it exceeds 128px, it triggers a smooth horizontal marquee scroll.
* **Hardware Volume Knob:** Maps a 12-bit potentiometer input into a clean 0-100% volume request. Filtered with mathematical logic to avoid analog signal jitters.
* **Dual-Threaded Flask Bridge:** Python backend fetches data continuously from Spotify Web API without blocking incoming hardware API calls.
* **Zero Jumper Display Freeze:** Implements U8g2's page loop method to ensure animations stay completely fluid during network request delays.

---

## 💻 Hardware Requirements

* **ESP32** Development Board (NodeMCU / ESP32-WROOM-32)
* **SH1106 OLED Display** (128x64 I2C Module)
* **Potentiometer** (10k Ohm recommended)
* Jumper wires & Breadboard

### Pin Mapping (ESP32)
| Component Pin | ESP32 GPIO | Description |
| :--- | :--- | :--- |
| **OLED SDA** | GPIO 21 | I2C Data |
| **OLED SCL** | GPIO 22 | I2C Clock |
| **Potentiometer Output** | GPIO 34 | Analog ADC1 Input |
| **Potentiometer VCC** | 3V3 | Power |
| **Potentiometer GND** | Ground |

---

## 🛠️ Software Setup & Installation

### 1. Clone the Repository
git clone [https://github.com/YOUR_USERNAME/cyberpunk-spotify-hardware-monitor.git](https://github.com/YOUR_USERNAME/cyberpunk-spotify-hardware-monitor.git)
cd cyberpunk-spotify-hardware-monitor

### 2. Python Backend Setup
First, ensure you have the required python packages installed:
pip install spotipy flask pycaw comtypes

1. Go to the Spotify Developer Dashboard and create an App to obtain your CLIENT_ID and CLIENT_SECRET.
2. Add [http://127.0.0.1:8888/callback](http://127.0.0.1:8888/callback) into your Spotify App's Redirect URIs settings.
3. Open backend/app.py and paste your credentials:
   CLIENT_ID = "YOUR_SPOTIFY_CLIENT_ID"
   CLIENT_SECRET = "YOUR_SPOTIFY_CLIENT_SECRET"
4. Open a command prompt as Administrator (required for Windows Master Volume modification) and run:
   cd backend
   python app.py

### 3. ESP32 Firmware
1. Open firmware/Cyberpunk_Spotify_Display.ino in Arduino IDE.
2. Install dependencies via Library Manager: U8g2, ArduinoJson.
3. Update configuration blocks with your network access information:
   const char* ssid     = "YOUR_WIFI_SSID";
   const char* password = "YOUR_WIFI_PASSWORD";
   const char* ip_address = "YOUR_COMPUTER_IP"; // Run 'ipconfig' in CMD to get this local IP
4. Flash the code to your ESP32 board.

---

## 🤝 Contributing
Contributions, issues, and feature requests are welcome! Feel free to check the issues page.

## 📝 License
This project is MIT licensed.
