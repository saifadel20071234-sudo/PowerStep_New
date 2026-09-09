import joblib

# 1. تحميل النموذج المراد فحصه
model = joblib.load('wifi_occupancy_model.joblib')

print("=== تفاصيل هيكل بيانات النموذج ===")

# 2. معرفة عدد الميزات (عدد الأعمدة المطلوب إدخالها)
if hasattr(model, 'n_features_in_'):
    print(f"عدد الميزات المطلوب إدخالها (Features Count): {model.n_features_in_}")

# 3. معرفة أسماء الأعمدة إن وجدت (Feature Names)
if hasattr(model, 'feature_names_in_'):
    print(f"أسماء الأعمدة المتوقعة: {list(model.feature_names_in_)}")
else:
    print("ملاحظة: النموذج تم تدريبه بدون أسماء أعمدة (يتوقع مصفوفة أرقام بالترتيب).")

# 4. معرفة الفئات التي يستنتجها النموذج (Output Classes)
if hasattr(model, 'classes_'):
    print(f"النتائج المحتملة للموديل (Classes): {list(model.classes_)}")