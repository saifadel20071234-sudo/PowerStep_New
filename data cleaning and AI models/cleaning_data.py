import pandas as pd
import numpy as np

# 1. إنشاء إطار زمني لأسبوع كامل (دقيقة بدقيقة)
# يبدأ من الأحد 6 سبتمبر 2026
dates = pd.date_range(start='2026-09-06 00:00:00', periods=7*24*60, freq='min')
df = pd.DataFrame({'timestamp': dates})

# 2. استخراج خصائص الوقت لتطبيق منطق الجامعة
df['hour'] = df['timestamp'].dt.hour
df['minute'] = df['timestamp'].dt.minute
df['day_of_week'] = df['timestamp'].dt.dayofweek

# تهيئة الأعمدة
df['people_count'] = 0
df['csi_variance'] = 0.0
df['piezo_voltage'] = 0.0
df['piezo_avg_watt'] = 0.0

# 3. محاكاة البيانات بناءً على الوقت والأرقام الحقيقية
for index, row in df.iterrows():
    h = row['hour']
    m = row['minute']
    d = row['day_of_week']
    
    # عطلات نهاية الأسبوع (الجمعة والسبت) أو الليل (من 6 مساءً لـ 7 صباحاً)
    if d in [4, 5] or h < 7 or h >= 18:
        # خمول تام (يحاكي أرقامك الصفرية)
        df.at[index, 'people_count'] = np.random.choice([0, 1], p=[0.9, 0.1])
        df.at[index, 'csi_variance'] = np.random.uniform(4.0, 9.5)
        df.at[index, 'piezo_voltage'] = np.random.uniform(0.0, 0.045)
        df.at[index, 'piezo_avg_watt'] = np.random.uniform(0.0, 0.002)
        
    else:
        # أوقات تبديل المحاضرات (مثلاً أول 15 دقيقة من كل محاضرة زوجية 8:00, 10:00, 12:00)
        is_transition = (h % 2 == 0) and (m < 15)
        
        if is_transition:
            # ذروة حقيقية (حركة كثيفة وضغط على الـ Piezo)
            df.at[index, 'people_count'] = np.random.choice([3, 4, 5], p=[0.2, 0.5, 0.3])
            df.at[index, 'csi_variance'] = np.random.uniform(15.0, 65.5)
            # توليد قفزات جهد تحاكي الـ 1.3 فولت
            df.at[index, 'piezo_voltage'] = np.random.uniform(0.15, 1.32)
            df.at[index, 'piezo_avg_watt'] = np.random.uniform(0.01, 0.065)
            
        else:
            # أثناء المحاضرة (ممرات شبه هادئة)
            df.at[index, 'people_count'] = np.random.choice([1, 2, 3], p=[0.4, 0.4, 0.2])
            df.at[index, 'csi_variance'] = np.random.uniform(9.0, 14.5)
            # إشارات Piezo عشوائية منخفضة
            df.at[index, 'piezo_voltage'] = np.random.uniform(0.0, 0.052)
            df.at[index, 'piezo_avg_watt'] = np.random.uniform(0.0, 0.0026)

# 4. تنظيف وحفظ الملف
df = df.round({'csi_variance': 4, 'piezo_voltage': 3, 'piezo_avg_watt': 4})
df.to_csv('university_simulated_week_1st.csv', index=False)
print("تم توليد ملف البيانات الاصطناعية 'university_simulated_week.csv' بنجاح!")