import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
import joblib

# ==========================================
# 1. قراءة بيانات الـ Piezo الفعالة
# ==========================================
print("جاري تحميل وتحليل بيانات GP.csv...")
df = pd.read_csv("GP.csv")

# ==========================================
# 2. تجهيز البيانات (Data Preprocessing)
# ==========================================
# تحويل الحالة النصية إلى أرقام يفهمها الموديل: 
# PRESSED (خطوة فعلية) = 1
# IDLE (خمول) = 0
df['is_step'] = (df['Step Status'] == 'PRESSED').astype(int)

# تحديد المدخلات (Features) والمخرجات (Target)
# النموذج سيعتمد على الجهد والطاقة لتأكيد الخطوة
X = df[['Voltage (V)', 'Power (W)']]
y = df['is_step']

# ==========================================
# 3. تقسيم البيانات (تدريب واختبار)
# ==========================================
# 80% من البيانات لتعليم النموذج، و 20% لاختبار ذكائه
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# ==========================================
# 4. تدريب نموذج Random Forest
# ==========================================
print("جاري تدريب النموذج على بصمة القدم الكهربائية...")
piezo_model = RandomForestClassifier(n_estimators=100, random_state=42)
piezo_model.fit(X_train, y_train)

# ==========================================
# 5. اختبار الدقة
# ==========================================
predictions = piezo_model.predict(X_test)
accuracy = accuracy_score(y_test, predictions)

print(f"\nدقة النموذج في التعرف على الخطوات: {accuracy * 100:.2f}%")
print("\nتقرير الأداء التفصيلي:")
print(classification_report(y_test, predictions))

# ==========================================
# 6. حفظ النموذج للاستخدام في كود التشغيل
# ==========================================
# نحفظه بنفس الاسم المستخدم في الـ Main Controller
joblib.dump(piezo_model, 'piezo_step_model.joblib')
print("\nتم حفظ النموذج بنجاح باسم 'piezo_step_model.joblib'!")