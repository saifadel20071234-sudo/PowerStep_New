import pandas as pd
import xgboost as xgb
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

# 1. قراءة بيانات الأسبوع الجامعي المحاكية
df = pd.read_csv("university_simulated_week.csv")

# 2. تحديد مستويات الإشغال (الهدف)
# 0 = خمول (لا يوجد أحد)، 1 = تواجد متوسط (1-2 أشخاص)، 2 = ذروة (3 أشخاص فأكثر)
def categorize_occupancy(count):
    if count >= 3: return 2
    elif count > 0: return 1
    else: return 0
    
df['occupancy_level'] = df['people_count'].apply(categorize_occupancy)

# 3. تحديد الميزات (Features)
# النموذج سيتعلم من الوقت فقط ليتوقع الحالة مسبقاً
X = df[['hour', 'minute', 'day_of_week']]
y = df['occupancy_level']

# 4. تقسيم البيانات (80% تدريب - 20% اختبار)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 5. تهيئة وتدريب النموذج
xgb_model = xgb.XGBClassifier(eval_metric='mlogloss', random_state=42)
xgb_model.fit(X_train, y_train)

# 6. التقييم
predictions = xgb_model.predict(X_test)
print("دقة توقع أوقات الذروة:", accuracy_score(y_test, predictions))
print("\nتقرير الأداء التفصيلي:\n", classification_report(y_test, predictions))

# 7. حفظ النموذج للاستخدام في محرك اتخاذ القرار
joblib.dump(xgb_model, 'xgboost_peak_predictor_new.joblib')