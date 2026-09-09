import csv
import json
import serial
import time

PORT = 'COM6'
BAUD = 115200

# إنشاء اسم ملف فريد بناءً على وقت التشغيل الحالي عشان يعمل ملف جديد في كل مرة
file_timestamp = time.strftime('%Y%m%d_%H%M%S')
csv_file = f'grid_powerstep_new_{file_timestamp}.csv'

try:
    arduino = serial.Serial(PORT, BAUD, timeout=1)
    time.sleep(2)
    print(f"Connected successfully. Creating new file: {csv_file}")
except Exception as e:
    print(f"Error opening port: {e}")
    exit()

with open(csv_file, mode='w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    
    # كتابة رأس الجدول للملف الجديد
    writer.writerow([
        'Timestamp', 'Sim Time', 'Uptime', 'Voltage (V)', 
        'Current (A)', 'Power (W)', 'Cumulative Gen (Wh)', 'SOC (%)', 'Power Source', 'Step Status'
    ])
    
    while True:
        try:
            if arduino.in_waiting > 0:
                raw_line = arduino.readline()
                line = raw_line.decode('utf-8', errors='ignore').strip()
                
                if line.startswith('{') and line.endswith('}'):
                    try:
                        data = json.loads(line)
                        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                        
                        sim_time = data.get('sim_time', '')
                        uptime = data.get('system_uptime', '')
                        voltage = data.get('voltage_v', 0)
                        current = data.get('current_a', 0)
                        power = data.get('generation_w', 0)
                        cum_gen = data.get('cumulative_gen_wh', 0)
                        soc = data.get('storage_soc_pct', 0)
                        source = data.get('power_source', '')
                        
                        # التقاط حالة الضغط من الـ tiles
                        tiles = data.get('tiles', [])
                        is_pressed = False
                        if tiles and len(tiles) > 0:
                            is_pressed = tiles[0].get('stepped_on', False)
                        
                        status_text = "PRESSED" if is_pressed else "IDLE"
                        
                        writer.writerow([
                            timestamp, sim_time, uptime, voltage, 
                            current, power, cum_gen, soc, source, status_text
                        ])
                        f.flush()
                        
                        print(f"V: {voltage:.4f}V | Status: {status_text} | P: {power:.2e}W")
                        
                    except json.JSONDecodeError:
                        pass
                        
        except KeyboardInterrupt:
            print("\nLogging stopped by user.")
            break
        except Exception as e:
            print(f"Error: {e}")
print("\nDone logging.")
input("Press Enter to close this window...")