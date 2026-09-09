import pandas as pd
import json
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score

# 1. قراءة الملف الأصلي
df = pd.read_csv("live_piezo_data_json.csv")

# 2. التعديل الأول: فك بيانات الـ JSON إلى أعمدة 
parsed_data = df['JSON_Data'].apply(json.loads).apply(pd.Series)

# 3. التعديل الثاني (الأهم): إنشاء عمود الهدف (Label) بناءً على عتبة الجهد
# سنعتبر أي قراءة أعلى من 0.1 فولت هي "خطوة قدم فعلية"
parsed_data['label'] = (parsed_data['voltage'] > 0.1).astype(int)

# 4. تحديد الميزات (X) والهدف (y)
X = parsed_data[['voltage', 'avg_watt']]
y = parsed_data['label']

# 5. تقسيم البيانات لتدريب واختبار (80% تدريب - 20% اختبار)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 6. بناء وتدريب نموذج Random Forest
rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
rf_model.fit(X_train, y_train)

# 7. التقييم
predictions = rf_model.predict(X_test)
print("دقة النموذج:", accuracy_score(y_test, predictions))
print("\nتقرير الأداء التفصيلي:\n", classification_report(y_test, predictions))

joblib.dump(rf_model, 'piezo_step_model.joblib')
print("تم حفظ نموذج الـ Piezo بنجاح!")