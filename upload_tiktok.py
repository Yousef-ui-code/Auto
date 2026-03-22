import os
import json
from tiktok_uploader.upload import upload_video
from tiktok_uploader.auth import AuthBackend

COOKIES_FILE = "tiktok_cookies.json"

def upload_to_tiktok(video_path, ayah_data):
    surah = ayah_data.get("surah_name", "")
    num   = ayah_data.get("ayah_number", "")
    title = "ayah " + str(num) + " surah " + str(surah) + " #shorts #quran #islam #قرآن"
    print("[TikTok] جاري الرفع...")
    try:
        auth = AuthBackend(cookies=COOKIES_FILE)
        upload_video(video_path, description=title, auth=auth)
        print("[TikTok] تم الرفع!")
        return True
    except Exception as e:
        print("[TikTok] خطأ: " + str(e))
        return False
