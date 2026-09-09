# ⚡ PowerStep System

**Intelligent Energy Harvesting & Footfall Analytics Platform**

PowerStep is an innovative, AI-driven IoT system that turns ordinary footsteps into actionable data and clean energy. By combining **Piezoelectric energy harvesting** with **Passive WiFi sniffing**, the system accurately measures human traffic, predicts peak hours using Machine Learning, and monitors generated micro-power in real-time.

---

## 🚀 Key Features

* **⚡ Real-Time Energy Harvesting:** Captures voltage and current from piezoelectric floor tiles and calculates generated wattage and cumulative Watt-hours.
* **📶 Passive WiFi Occupancy Tracking:** Uses ESP8266/ESP32 in *Promiscuous Mode* to sniff unencrypted MAC addresses and estimate room occupancy without requiring users to connect to a network.
* **🧠 AI & Machine Learning Integration:**
  * **Step Detection:** ML models filter out noise and accurately detect real human steps.
  * **Occupancy Prediction:** Correlates WiFi device counts with actual human presence.
  * **Peak Forecasting:** Predicts expected high-traffic time slots based on historical data.
* **📊 Live Interactive Dashboard:** A highly responsive Web UI built with Chart.js and WebSockets, rendering live graphs, interactive floor tile animations, and battery State-of-Charge (SOC) gauges at 5 FPS.
* **🚨 Intelligent Alert System:** Automatically detects hardware faults (e.g., footfall detected but no power generated), offline sensors, and unexpected occupancy surges.

---

## 🏗️ System Architecture

```mermaid
graph TD;
    subgraph Hardware Layer
        P[Piezoelectric Sensors] -->|Analog Signal| E[ESP8266 / ESP32]
        W[Smartphones/WiFi Devices] -.->|Probe Requests| E
    end

    subgraph Backend Layer (Python)
        E -->|Serial JSON / HTTP POST| S[Serial Worker & API]
        S --> ML[Inference Engine XGBoost/RF]
        ML --> DB[(SQLite WAL Database)]
        ML --> A[Alert Manager]
        ML --> B[WebSocket Bridge]
    end

    subgraph Frontend Layer
        B -->|Live Sync 5 FPS| UI[Interactive Dashboard]
    end
```

---

## 📂 Project Structure

```text
PowerStep_New/
├── data cleaning and AI models/  # Trained Joblib models (XGBoost, RandomForest)
├── esp8266_combined/             # ESP8266 C++ Firmware (Piezo + WiFi Sniffer)
├── dashboard_frontend/           # HTML/CSS/JS Frontend Dashboard
├── main_system.py                # Core Python Backend (Serial reading, API)
├── realtime_inference.py         # AI Inference Engine for processing sensor data
├── database_manager.py           # SQLite database operations
├── alert_manager.py              # Anomaly detection and alerting logic
├── dashboard_bridge.py           # WebSocket broadcasting logic
├── Start_Dashboard.bat           # 1-Click Startup Script for Windows
└── requirements.txt              # Python dependencies
```

---

## 🛠️ Installation & Setup

### 1. Hardware Setup (ESP8266)
1. Open `esp8266_combined/esp8266_combined.ino` in the Arduino IDE.
2. Install the **ArduinoJson** library.
3. Connect the Piezo sensor to the `A0` analog pin.
4. Flash the code to your ESP8266 board.

### 2. Software Setup
Ensure you have **Python 3.9+** installed.
```bash
# Clone the repository
git clone https://github.com/saifadel20071234-sudo/PowerStep_New.git
cd PowerStep_New

# Install required Python packages
pip install -r requirements.txt
```

### 3. Running the System
Simply double-click the included batch file:
```cmd
Start_Dashboard.bat
```
*This script will automatically:*
1. Start the Python Backend (`main_system.py`) on port `8000`.
2. Start the Frontend Server on port `5500`.
3. Open the Dashboard in your default web browser automatically.

---

## 🧠 Machine Learning Details
The system utilizes pre-trained Scikit-Learn and XGBoost models located in the `data cleaning and AI models/` directory. 
- The backend evaluates sensor data against these models in real-time under `realtime_inference.py`.
- To retrain the models, you can use the provided CSV datasets and training scripts (`train_random_forest.py`, `XGBoost_peak.py`, etc.).

---

## 📝 License
This project is created for educational and prototyping purposes. 
