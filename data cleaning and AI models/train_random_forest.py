import pandas as pd
import json
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

# 1. دمج الملفين لضمان توازن البيانات (قراءات الخمول من ملف 2 والذروة من ملف 3)
df2 = pd.read_csv("wifi_dataset (2).csv")
df3 = pd.read_csv("wifi_dataset (3).csv")
df_combined = pd.concat([df2, df3], ignore_index=True)

# فك تشفير JSON
parsed_data = df_combined['data'].apply(json.loads).apply(pd.Series)

# إنشاء عمود التواجد (0 = فارغ، 1 = مشغول)
parsed_data['is_occupied'] = (parsed_data['people_count'] > 0).astype(int)

# ==========================================
# الموديل الأول: اكتشاف التواجد من الـ CSI فقط
# ==========================================
X_occ = parsed_data[['csi_variance']]
y_occ = parsed_data['is_occupied']

X_train_occ, X_test_occ, y_train_occ, y_test_occ = train_test_split(X_occ, y_occ, test_size=0.2, random_state=42)

occ_model = RandomForestClassifier(n_estimators=100, random_state=42)
occ_model.fit(X_train_occ, y_train_occ)
occ_acc = accuracy_score(y_test_occ, occ_model.predict(X_test_occ))
print(f"دقة نموذج التواجد (CSI Variance): {occ_acc * 100:.2f}%")

# ==========================================
# الموديل الثاني: تحديد العدد من الـ IPs فقط
# ==========================================
# ندرب هذا النموذج فقط على الحالات التي يوجد بها أشخاص فعلاً
active_data = parsed_data[parsed_data['is_occupied'] == 1]
X_cnt = active_data[['device_count_raw']]
y_cnt = active_data['people_count']

X_train_cnt, X_test_cnt, y_train_cnt, y_test_cnt = train_test_split(X_cnt, y_cnt, test_size=0.2, random_state=42)

count_model = RandomForestClassifier(n_estimators=100, random_state=42)
count_model.fit(X_train_cnt, y_train_cnt)
cnt_acc = accuracy_score(y_test_cnt, count_model.predict(X_test_cnt))
print(f"دقة نموذج تحديد العدد (IP Count): {cnt_acc * 100:.2f}%")

# # حفظ نموذج اكتشاف التواجد (يعتمد على CSI+IP)
# joblib.dump(occ_model, 'wifi_occupancy_model.joblib')
# joblib.dump(count_model, 'wifi_count_model.joblib')

# print("تم حفظ كلا النموذجين بنجاح!")