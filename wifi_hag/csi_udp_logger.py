"""
csi_udp_logger.py
==================
يستقبل حزم CSI من الـ ESP32 عبر UDP (بروتوكول عالي الأداء، بدون overhead
الـ Serial أو HTTP) ويسجلها في ملف CSV جاهز للتدريب عليه.

اللابل (مشغول/فاضي) بيتحدد من الـ ESP32 نفسه — بالأمر اللي بتبعتيه في صندوق
الإرسال بـ Arduino Serial Monitor ('1' أو '0')، وبييجي جوه كل حزمة تلقائيًا.
يعني: سيبي Serial Monitor مفتوح في نافذة، وشغّلي السكريبت ده في نافذة تانية
(Command Prompt)، واكتبي 1/0 في الـ Serial Monitor وانتي بتجمعي البيانات.

التشغيل:
    python csi_udp_logger.py

(مفيش مكتبات إضافية مطلوبة — socket و csv و struct كلها built-in في بايثون)
"""

import socket
import struct
import csv
from datetime import datetime

UDP_PORT = 5005
CSV_FILENAME = f"csi_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

# ⚠️ تنسيق الحزمة لازم يطابق الـ struct CsiPacket بتاع كود الـ ESP32 بالظبط:
#   uint32_t timestamp_ms | int8_t rssi | uint16_t num_subcarriers |
#   float mean_amp | float std_amp | uint8_t label
# "<" = little-endian بدون padding (مطابق لـ attribute((packed)) في الكود)
PACKET_FORMAT = "<IbHffB"
PACKET_SIZE = struct.calcsize(PACKET_FORMAT)


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", UDP_PORT))

    print(f"📡 في انتظار بيانات CSI على المنفذ {UDP_PORT} ...")
    print(f"💾 هيتسجل في: {CSV_FILENAME}")
    print("تأكدي إن Serial Monitor مفتوح واكتبي 1 (مشغول) أو 0 (فاضي) وانتي بتجمعي.")
    print("اضغطي Ctrl+C هنا لإيقاف التسجيل.\n")

    count = 0
    label_counts = {0: 0, 1: 0}

    with open(CSV_FILENAME, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp_ms", "rssi", "num_subcarriers", "mean_amp", "std_amp", "label"])

        try:
            while True:
                data, addr = sock.recvfrom(1024)

                if len(data) != PACKET_SIZE:
                    # حزمة بحجم غير متوقع (تلف أثناء النقل، أو ESP32 بيبعت تنسيق قديم) — نتجاهلها
                    continue

                timestamp_ms, rssi, num_subcarriers, mean_amp, std_amp, label = struct.unpack(PACKET_FORMAT, data)
                writer.writerow([timestamp_ms, rssi, num_subcarriers, round(mean_amp, 3), round(std_amp, 3), label])

                count += 1
                label_counts[label] = label_counts.get(label, 0) + 1

                if count % 50 == 0:
                    label_txt = "مشغول" if label == 1 else "فاضي"
                    print(f"✅ اتسجل {count} عينة | فاضي={label_counts[0]} مشغول={label_counts[1]} | آخر لابل: {label_txt}")

        except KeyboardInterrupt:
            print(f"\n🛑 اتوقف التسجيل.")
            print(f"إجمالي العينات: {count}  (فاضي={label_counts[0]}, مشغول={label_counts[1]})")
            print(f"الملف: {CSV_FILENAME}")


if __name__ == "main":
    main()