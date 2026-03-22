import os
import dropbox

DROPBOX_TOKEN = os.environ.get("DROPBOX_TOKEN", "")

def upload_to_dropbox(video_path, ayah_data):
    print("[Dropbox] جاري الرفع...")
    try:
        dbx = dropbox.Dropbox(DROPBOX_TOKEN)
        surah = ayah_data.get("surah_number", 1)
        ayah  = ayah_data.get("ayah_number", 1)
        dest  = f"/QuranBot/video_{surah}_{ayah}.mp4"
        with open(video_path, "rb") as f:
            dbx.files_upload(f.read(), dest, mode=dropbox.files.WriteMode.overwrite)
        print(f"[Dropbox] تم الرفع: {dest}")
        return True
    except Exception as e:
        print("[Dropbox] خطأ: " + str(e))
        return False
