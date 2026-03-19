import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def get_youtube_client():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open("token.json","w") as f:
            f.write(creds.to_json())
    if not creds or not creds.valid:
        raise RuntimeError("token.json غير موجود. شغل generate_token.py اولا.")
    return build("youtube","v3",credentials=creds)

def build_description(d):
    return f"🌙 {d['surah_name']} الآية {d['ayah_number']}\n📖 {d['arabic']}\n\n🔤 Translation:\n{d['english']}\n\nSurah {d['surah_name_en']} [{d['surah_number']}:{d['ayah_number']}]\n\n🤲 اشترك لتصلك آية يومياً\n#Quran #Islam #QuranShorts #قرآن #إسلام"

def upload_video(video_path, ayah_data):
    yt = get_youtube_client()
    body = {
        "snippet": {
            "title": f"آية اليوم | سورة {ayah_data['surah_name']} الآية {ayah_data['ayah_number']} | Quran Short"[:100],
            "description": build_description(ayah_data),
            "tags": ["Quran","Islam","QuranShorts","قرآن","إسلام",ayah_data["surah_name_en"]],
            "categoryId": "22",
            "defaultLanguage": "ar",
        },
        "status": {"privacyStatus":"public","selfDeclaredMadeForKids":False},
    }
    media = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True)
    req = yt.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    print("[^] جاري الرفع...")
    while response is None:
        status, response = req.next_chunk()
        if status:
            print(f"    {int(status.progress()*100)}%")
    url = f"https://www.youtube.com/shorts/{response['id']}"
    print(f"[OK] تم! {url}")
    return url
