import os, json, sys
from generate_video import generate_video
from generate_video import get_ayah_data
from upload_youtube import upload_video

PROGRESS_FILE = "data/progress.json"
OUTPUT_VIDEO  = "output_video.mp4"

def load_progress():
    os.makedirs("data", exist_ok=True)
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {"last_surah":1,"last_ayah":0,"total_uploaded":0}

def save_progress(p):
    with open(PROGRESS_FILE,"w") as f:
        json.dump(p, f, ensure_ascii=False, indent=2)

def main():
    print("="*50)
    p     = load_progress()
    s     = p.get("last_surah", 1)
    a     = p.get("last_ayah",  0) + 1
    total = p.get("total_uploaded", 0)

    if a > {1:7,2:286,3:200}.get(s,200):
        s += 1; a = 1
    if s > 114:
        s = 1; a = 1

    print(f"[->] يبدأ من سورة {s} آية {a}")

    # توليد الفيديو وتجميع الآيات
    output, next_s, next_a = generate_video(s, a, OUTPUT_VIDEO, query_index=total)

    # جلب بيانات الآية الأولى للعنوان
    first_data = get_ayah_data(s, a)

    # رفع يوتيوب
    url = upload_video(OUTPUT_VIDEO, first_data)

    # رفع على TikTok
    try:
        from upload_tiktok import upload_to_tiktok
        upload_to_tiktok(OUTPUT_VIDEO, first_data)
    except Exception as e:
        print(f"[TikTok] فشل: {e}")

    # حفظ التقدم — نحفظ آخر آية وصلناها
    p.update({
        "last_surah":    next_s,
        "last_ayah":     next_a - 1,
        "total_uploaded": total + 1
    })
    save_progress(p)

    if os.path.exists(OUTPUT_VIDEO):
        os.remove(OUTPUT_VIDEO)

    print(f"[OK] فيديو رقم {total+1}")
    print(url)
    print("="*50)

if __name__ == "__main__":
    main()
