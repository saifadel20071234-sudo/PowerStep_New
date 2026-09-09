import pandas as pd
import json
import numpy as np

# ==========================================
# 1. دوال لاستخراج البيانات الحقيقية من الملفات الأربعة
# ==========================================
def parse_wifi_file(file_path):
    df = pd.read_csv(file_path)
    if 'data' in df.columns:
        parsed = df['data'].apply(json.loads).apply(pd.Series)
        return parsed[['csi_variance', 'device_count_raw', 'people_count']]
    return df[['csi_variance', 'device_count_raw', 'people_count']]

def parse_piezo_file(file_path):
    df = pd.read_csv(file_path)
    # فك تشفير JSON إذا كان الملف القديم (live_piezo)
    if 'data' in df.columns:
        df = df['data'].apply(json.loads).apply(pd.Series)
    
    # توحيد أسماء الأعمدة لتتطابق مع ملف GP.csv والمنظومة
    if 'Voltage (V)' in df.columns:
        df = df.rename(columns={'Voltage (V)': 'piezo_voltage', 'Power (W)': 'piezo_avg_watt'})
    
    # إذا لم يكن هناك عمود للحالة، نعتبر الجهد > 0.12 هو ضغط (PRESSED)
    if 'Step Status' not in df.columns:
        df['Step Status'] = np.where(df['piezo_voltage'] >= 0.12, 'PRESSED', 'IDLE')
        
    return df[['piezo_voltage', 'piezo_avg_watt', 'Step Status']]

# ==========================================
# 2. تحميل بنوك البيانات الأصلية (Data Pools)
# ==========================================
print("جاري تحميل الملفات الأربعة لاستخلاص القراءات الحقيقية...")
# بنوك الواي فاي
wifi_idle_pool = parse_wifi_file("wifi_dataset (2).csv")
wifi_peak_pool = parse_wifi_file("wifi_dataset (3).csv")

# بنوك البيزو (دمج الملفين لزيادة تنوع القراءات الحقيقية)
piezo_gp = parse_piezo_file("GP.csv")
try:
    piezo_live = parse_piezo_file("live_piezo_data_json.csv")
    piezo_combined = pd.concat([piezo_gp, piezo_live], ignore_index=True)
except:
    piezo_combined = piezo_gp

# فصل البيزو لحالات الضغط والخمول
piezo_pressed_pool = piezo_combined[piezo_combined['Step Status'] == 'PRESSED']
piezo_idle_pool = piezo_combined[piezo_combined['Step Status'] == 'IDLE']

# ==========================================
# 3. بناء الجدول الزمني لأسبوع جامعي
# ==========================================
# من الأحد إلى الخميس، من 8 صباحاً حتى 6 مساءً، قراءة كل دقيقة
dates = pd.date_range(start="2026-10-04 08:00:00", end="2026-10-08 18:00:00", freq="30s")
simulated_data = []

print("جاري بناء الأسبوع وتسكين القراءات...")
for dt in dates:
    # تخطي يومي الجمعة والسبت، وتخطي أوقات الليل
    if dt.weekday() > 4 or dt.hour < 8 or dt.hour >= 18:
        continue

    # تحديد أوقات الذروة (أوقات تبديل المحاضرات: رأس كل ساعتين مثلاً لربع ساعة)
    is_peak = (dt.hour in [8, 10, 12, 14]) and (dt.minute <= 15)
    
    # ==========================================
    # 4. سحب القراءات العشوائية المطابقة للحالة
    # ==========================================
    if is_peak:
        # وقت تكدس -> نسحب سطر حقيقي من ملف الذروة (3) ومن ضغطات البيزو
        wifi_row = wifi_peak_pool.sample(1).iloc[0]
        piezo_row = piezo_pressed_pool.sample(1).iloc[0]
    else:
        # وقت خمول/محاضرات -> نسحب سطر حقيقي من ملف الخمول (2) ومن سكون البيزو
        wifi_row = wifi_idle_pool.sample(1).iloc[0]
        # احتمالية 10% لمرور شخص متأخر في وقت الخمول
        if np.random.rand() < 0.10:
            piezo_row = piezo_pressed_pool.sample(1).iloc[0]
        else:
            piezo_row = piezo_idle_pool.sample(1).iloc[0]

    # دمج السطرين في قراءة واحدة متكاملة
    simulated_data.append({
        'timestamp': dt.strftime('%Y-%m-%d %H:%M:%S'),
        'day_of_week': dt.weekday(),
        'hour': dt.hour,
        'minute': dt.minute,
        'csi_variance': wifi_row['csi_variance'],
        'device_count_raw': wifi_row['device_count_raw'],
        'people_count': wifi_row['people_count'],
        'piezo_voltage': piezo_row['piezo_voltage'],
        'piezo_avg_watt': piezo_row['piezo_avg_watt']
    })

# ==========================================
# 5. الحفظ النهائي
# ==========================================
df_simulated = pd.DataFrame(simulated_data)
df_simulated.to_csv("university_simulated_week.csv", index=False)
print(f"تم إنشاء الملف بنجاح! يحتوي على {len(df_simulated)} قراءة فعلية.")